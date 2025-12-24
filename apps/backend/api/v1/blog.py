from fastapi import APIRouter, HTTPException, Request, Depends
from core.upstash_redis import get_redis_client, RedisClientType
import httpx

router = APIRouter()

from schemas import BlogRequest

async def check_rate_limit(request: Request, redis: RedisClientType = Depends(get_redis_client)):
    client_ip = request.client.host
    key = f"rate_limit:{client_ip}"
    
    current_count = redis.incr(key)
    
    if current_count == 1:
        redis.expire(key, 60)
        
    if current_count > 5:
        raise HTTPException(status_code=429, detail="Rate limit exceeded. Max 5 requests per minute.")

@router.post("/generate", dependencies=[Depends(check_rate_limit)])
async def generate_blog(req: BlogRequest, http_request: Request):
    """DEPRECATED: Forwards to /v1/content/generate for backward compatibility."""
    try:
        new_request = {
            "prompt": f"Generate a {req.tone} {req.length} blog post about: {req.prompt}",
            "safety_level": "moderate",
            "conversation_history": []
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "http://localhost:8000/v1/content/generate",
                json=new_request,
                timeout=30.0
            )
            response.raise_for_status()
            data = response.json()
            
            return {
                "blog": data["content"],
                "success": data["success"],
                "cached": data["cached"],
                "generation_time_ms": data["generation_time_ms"]
            }
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"\n{'='*50}")
        print(f"ERROR in generate_blog:")
        print(f"Error type: {type(e).__name__}")
        print(f"Error message: {str(e)}")
        print(f"Full traceback:")
        print(error_details)
        print(f"{'='*50}\n")
        
        return {
            "blog": f"# {req.prompt.title()}\n\n*Note: AI generation temporarily unavailable.*\n\nError: {str(e)}",
            "success": False
        }

@router.get("/test")
async def test_endpoint():
    return {"status": "ok", "message": "Blog router working (deprecated)"}
