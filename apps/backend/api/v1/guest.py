from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from redis.asyncio import Redis
from core.redis import get_redis_client
import json
from typing import List

router = APIRouter()

class ChatMessage(BaseModel):
    role: str
    content: str
    timestamp: str

@router.post("/chat/{guest_id}")
async def save_guest_message(
    guest_id: str, 
    message: ChatMessage, 
    redis: Redis = Depends(get_redis_client)
):
    key = f"guest:{guest_id}:chat"
    # Store as JSON string
    await redis.rpush(key, json.dumps(message.model_dump()))
    # Optional: Set TTL for guest sessions (e.g., 24 hours)
    await redis.expire(key, 86400) 
    return {"status": "saved", "guest_id": guest_id}

@router.get("/chat/{guest_id}", response_model=List[ChatMessage])
async def get_guest_history(
    guest_id: str, 
    redis: Redis = Depends(get_redis_client)
):
    key = f"guest:{guest_id}:chat"
    # Get all messages
    messages_raw = await redis.lrange(key, 0, -1)
    
    # Parse JSON strings back to objects
    history = [json.loads(m) for m in messages_raw]
    return history
