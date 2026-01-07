import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from core.config import settings
from api.v1.blog import router as blog_router
from api.v1.guest import router as guest_router
from api.v1.agent import router as agent_router
from api.v1.embeddings import router as embeddings_router
from api.v1.guardrails import router as guardrails_router
from api.v1.content import router as content_router
from api.v1.classifier import router as classifier_router
from api.v1.context import router as context_router
from api.routes.trends import router as trends_router
from api.v1.social import router as social_router
from core.upstash_redis import UpstashRedisClient
from database.database import init_db

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    try:
        init_db()  # Create database tables
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
# Parse allowed origins from environment variable
allowed_origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "https://genecis.vercel.app",
]

env_origins = os.getenv("ALLOWED_ORIGINS")
if env_origins:
    allowed_origins.extend([origin.strip() for origin in env_origins.split(",") if origin.strip()])

app.add_middleware(
    CORSMiddleware,
    # Allow specific origins
    allow_origins=allowed_origins,
    # Regex to matches any localhost/127.0.0.1 port (great for dev)
    allow_origin_regex=r"http://(localhost|127\.0\.0\.1|::1)(:\d+)?",
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
app.include_router(social_router, prefix="/v1/social", tags=["Social"])

@app.get("/health")
async def health_check():
    """Basic health check endpoint"""
    return {"status": "ok"}

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """
    Global exception handler to ensure CORS headers are always sent,
    even for unhandled server errors (500).
    """
    import traceback
    error_details = traceback.format_exc()
    print(f"🔥 CRITICAL ERROR: Unhandled exception: {exc}")
    print(error_details)
    
    return JSONResponse(
        status_code=500,
        content={
            "detail": "Internal Server Error",
            "error": str(exc),
        },
        headers={
            "Access-Control-Allow-Origin": request.headers.get("origin", "*"),
            "Access-Control-Allow-Credentials": "true",
            "Access-Control-Allow-Methods": "*",
            "Access-Control-Allow-Headers": "*",
        }
    )

@app.get("/v1/health/redis")
async def health_check_redis():
    try:
        redis = UpstashRedisClient.get_instance()
        pong = redis.ping()
        return {"status": "ok", "redis": "connected" if pong else "disconnected"}
    except Exception as e:
        return {"status": "error", "redis": str(e)}