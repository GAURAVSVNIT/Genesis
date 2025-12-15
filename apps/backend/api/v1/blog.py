from fastapi import APIRouter, HTTPException, Request, Depends
from pydantic import BaseModel
from agents.orchestrator import run_blog_agent
from core.upstash_redis import get_redis_client
from upstash_redis import Redis

router= APIRouter()

from schemas import BlogRequest

async def check_rate_limit(request: Request, redis: Redis = Depends(get_redis_client)):
    client_ip = request.client.host
    key = f"rate_limit:{client_ip}"
    
    # Simple fixed window counter
    current_count = redis.incr(key)
    
    if current_count == 1:
        redis.expire(key, 60) # Reset after 60 seconds
        
    if current_count > 5:
        raise HTTPException(status_code=429, detail="Rate limit exceeded. Max 5 requests per minute.")

@router.post("/generate", dependencies=[Depends(check_rate_limit)])
async def generate_blog(req:BlogRequest):
    try:
        result = await run_blog_agent(req)
        return result
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
        
        # Return a fallback response instead of crashing
        return {
            "blog": f"# {req.prompt.title()}\n\n*Note: AI generation temporarily unavailable. Here's a placeholder.*\n\nThis would be a {req.length} blog post with a {req.tone} tone about: {req.prompt}\n\nError: {str(e)}"
        }

@router.get("/test")
async def test_endpoint():
    return {"status": "ok", "message": "Blog router is working"} 