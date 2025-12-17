from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.v1.blog import router as blog_router
from api.v1.guest import router as guest_router
from api.v1.agent import router as agent_router
from core.upstash_redis import UpstashRedisClient

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    UpstashRedisClient.get_instance()
    yield
    # Shutdown
    await UpstashRedisClient.close()

app = FastAPI(title="Genesis", description="Genesis API", version="1.0.0", lifespan=lifespan)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(blog_router, prefix="/v1/blog")
app.include_router(guest_router, prefix="/v1/guest")
app.include_router(agent_router, prefix="/v1/agent")

@app.get("/v1/health/redis")
async def health_check_redis():
    try:
        redis = UpstashRedisClient.get_instance()
        pong = redis.ping()
        return {"status": "ok", "redis": "connected" if pong else "disconnected"}
    except Exception as e:
        return {"status": "error", "redis": str(e)}

