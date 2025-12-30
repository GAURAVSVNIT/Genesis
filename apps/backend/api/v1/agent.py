"""Multi-agent system endpoint with database persistence."""

from fastapi import APIRouter, HTTPException, Request, Depends
from pydantic import BaseModel
from schemas import AgentRequest
from graph.multi_agent_graph import multi_agent_graph
from core.upstash_redis import get_redis_client, RedisClientType
from database.database import SessionLocal
from database.models.content import GeneratedContent
import uuid
from datetime import datetime

router = APIRouter()

class AgentTaskResponse(BaseModel):
    """Response from agent processing with persistent storage."""
    task_id: str
    task: str
    coordination: dict
    plan: dict
    execution: dict
    final_output: str
    status: str

def get_db():
    """Get database session."""
    db = None
    try:
        db = SessionLocal()
        yield db
    except Exception as e:
        print(f"Database connection error: {e}")
        yield None
    finally:
        if db:
            db.close()

async def check_rate_limit(request: Request, redis: RedisClientType = Depends(get_redis_client)):
    client_ip = request.client.host
    key = f"rate_limit:agent:{client_ip}"
    
    current_count = redis.incr(key)
    
    if current_count == 1:
        redis.expire(key, 60)
        
    if current_count > 5:
        raise HTTPException(status_code=429, detail="Rate limit exceeded. Max 5 requests per minute.")

@router.post("/process", response_model=AgentTaskResponse, dependencies=[Depends(check_rate_limit)])
async def process_task(req: AgentRequest, db = Depends(get_db)):
    """
    Multi-agent system endpoint with persistent storage.
    Processes tasks using: Coordinator -> Planner -> Executor -> Reviewer
    Stores all results in generated_content table for audit trail.
    """
    task_id = str(uuid.uuid4())
    user_id = str(uuid.uuid4())
    
    try:
        initial_state = {
            "task": req.task,
            "coordination": None,
            "plan": None,
            "execution": None,
            "final_output": None,
            "status": None
        }
        
        result = await multi_agent_graph.ainvoke(initial_state)
        
        # Store results in generated_content
        generated_content = GeneratedContent(
            id=task_id,
            user_id=user_id,
            conversation_id=str(uuid.uuid4()),
            message_id=None,
            original_prompt=req.task,
            requirements={"task_type": "multi_agent"},
            content_type="multi_agent_output",
            platform="api",
            generated_content={
                "task": result["task"],
                "coordination": result.get("coordination"),
                "plan": result.get("plan"),
                "execution": result.get("execution"),
                "final_output": result.get("final_output"),
                "status": result.get("status")
            },
            status=result.get("status", "completed"),
            created_at=datetime.utcnow()
        )
        db.add(generated_content)
        db.commit()
        
        return AgentTaskResponse(
            task_id=task_id,
            task=result["task"],
            coordination=result.get("coordination", {}),
            plan=result.get("plan", {}),
            execution=result.get("execution", {}),
            final_output=result.get("final_output", ""),
            status=result.get("status", "completed")
        )
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
        
        try:
            error_content = GeneratedContent(
                id=task_id,
                user_id=user_id,
                conversation_id=str(uuid.uuid4()),
                message_id=None,
                original_prompt=req.task,
                requirements={"task_type": "multi_agent"},
                content_type="multi_agent_output",
                platform="api",
                generated_content={
                    "error": str(e),
                    "error_type": type(e).__name__
                },
                status="error",
                created_at=datetime.utcnow()
            )
            db.add(error_content)
            db.commit()
        except:
            db.rollback()
        
        raise HTTPException(status_code=500, detail=f"Agent processing failed: {str(e)}")

@router.get("/test")
async def test_endpoint():
    return {"status": "ok", "message": "Multi-agent router is working"}
