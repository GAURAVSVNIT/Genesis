from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
# Load environment variables early
print("⬇ Importing config...")
from core.config import settings
print("⬇ Importing blog...")
from api.v1.blog import router as blog_router
print("⬇ Importing guest...")
from api.v1.guest import router as guest_router
print("⬇ Importing agent...")
from api.v1.agent import router as agent_router
print("⬇ Importing embeddings...")
from api.v1.embeddings import router as embeddings_router
print("⬇ Importing guardrails...")
from api.v1.guardrails import router as guardrails_router
print("⬇ Importing content...")
from api.v1.content import router as content_router
print("⬇ Importing classifier...")
from api.v1.classifier import router as classifier_router
print("⬇ Importing context...")
from api.v1.context import router as context_router
print("⬇ Importing trends...")
from api.routes.trends import router as trends_router
print("⬇ Importing redis...")
from core.upstash_redis import UpstashRedisClient
print("⬇ Importing database...")
from database.database import init_db
print(" Imports complete.")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print(" Starting lifespan...")
    try:
        print("  Calling init_db()...")
        init_db()  # Create database tables
        print("  init_db() completed.")
    except Exception as e:
        print(f" Warning: Database initialization failed: {e}")
        print(" Server will continue running in limited mode")
    try:
        UpstashRedisClient.get_instance()
    except Exception as e:
        print(f" Warning: Redis initialization failed: {e}")
    yield
    # Shutdown
    try:
        await UpstashRedisClient.close()
    except Exception:
        pass

app = FastAPI(title="Genesis", description="Genesis API", version="1.0.0", lifespan=lifespan)

# Add CORS middleware FIRST (before any routes)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins in development
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

app.include_router(blog_router, prefix="/v1/blog")
app.include_router(guest_router, prefix="/v1/guest")
app.include_router(agent_router, prefix="/v1/agent")
app.include_router(embeddings_router)
app.include_router(guardrails_router)
app.include_router(content_router)
app.include_router(classifier_router)
app.include_router(context_router)
app.include_router(trends_router)

@app.get("/health")
async def health_check():
    """Basic health check endpoint"""
    return {"status": "ok"}

@app.get("/v1/health/redis")
async def health_check_redis():
    try:
        redis = UpstashRedisClient.get_instance()
        pong = redis.ping()
        return {"status": "ok", "redis": "connected" if pong else "disconnected"}
    except Exception as e:
        return {"status": "error", "redis": str(e)}