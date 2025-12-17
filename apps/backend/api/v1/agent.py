from fastapi import APIRouter, HTTPException, Request, Depends
from schemas import AgentRequest
from graph.multi_agent_graph import multi_agent_graph
from core.upstash_redis import get_redis_client, RedisClientType

router = APIRouter()

async def check_rate_limit(request: Request, redis: RedisClientType = Depends(get_redis_client)):
    client_ip = request.client.host
    key = f"rate_limit:agent:{client_ip}"
    
    # Simple fixed window counter
    current_count = redis.incr(key)
    
    if current_count == 1:
        redis.expire(key, 60)  # Reset after 60 seconds
        
    if current_count > 5:
        raise HTTPException(status_code=429, detail="Rate limit exceeded. Max 5 requests per minute.")

@router.post("/process", dependencies=[Depends(check_rate_limit)])
async def process_task(req: AgentRequest):
    """
    Multi-agent system endpoint
    Processes tasks using: Coordinator -> Planner -> Executor -> Reviewer
    """
    try:
        # Initialize state with user task
        initial_state = {
            "task": req.task,
            "coordination": None,
            "plan": None,
            "execution": None,
            "final_output": None,
            "status": None
        }
        
        # Run the multi-agent graph
        result = await multi_agent_graph.ainvoke(initial_state)
        
        return {
            "task": result["task"],
            "coordination": result.get("coordination"),
            "plan": result.get("plan"),
            "execution": result.get("execution"),
            "final_output": result.get("final_output"),
            "status": result.get("status")
        }
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"\n{'='*50}")
        print(f"ERROR in process_task:")
        print(f"Error type: {type(e).__name__}")
        print(f"Error message: {str(e)}")
        print(f"Full traceback:")
        print(error_details)
        print(f"{'='*50}\n")
        
        raise HTTPException(status_code=500, detail=f"Agent processing failed: {str(e)}")

@router.get("/test")
async def test_endpoint():
    return {"status": "ok", "message": "Multi-agent router is working"}
