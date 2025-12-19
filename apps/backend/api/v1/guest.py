"""Guest chat endpoint - stores in both Redis and PostgreSQL for persistence."""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from upstash_redis import Redis
from core.upstash_redis import get_redis_client
from database.database import SessionLocal
from database.models.cache import ConversationCache, MessageCache
import json
from typing import List
from datetime import datetime
import uuid
import hashlib

router = APIRouter()

class ChatMessage(BaseModel):
    role: str
    content: str
    timestamp: str

class MigrationRequest(BaseModel):
    authenticated_user_id: str

def get_db():
    """Get database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/chat/{guest_id}")
async def save_guest_message(
    guest_id: str, 
    message: ChatMessage, 
    redis: Redis = Depends(get_redis_client),
    db = Depends(get_db)
):
    """Save guest message to both Redis (hot) and PostgreSQL (cold) storage."""
    try:
        # Store in Redis (hot cache)
        key = f"guest:{guest_id}"
        redis.rpush(key, json.dumps(message.model_dump()))
        redis.expire(key, 86400)
        
        # Store in PostgreSQL (persistent)
        conversation = db.query(ConversationCache).filter_by(
            user_id=guest_id,
            platform="guest"
        ).first()
        
        if not conversation:
            # Generate hash from guest_id for initial conversation
            conversation_hash = hashlib.sha256(guest_id.encode()).hexdigest()[:64]
            conversation = ConversationCache(
                id=str(uuid.uuid4()),
                user_id=guest_id,
                session_id=guest_id,
                title=f"Guest Chat - {guest_id}",
                conversation_hash=conversation_hash,
                message_count=0,
                platform="guest",
                tone="neutral",
                created_at=datetime.utcnow(),
                migration_version="1.0"
            )
            db.add(conversation)
            db.flush()
        
        conversation.message_count += 1
        
        # Generate hash from message content
        message_hash = hashlib.md5(message.content.encode()).hexdigest()
        
        msg_record = MessageCache(
            id=str(uuid.uuid4()),
            conversation_id=conversation.id,
            role=message.role,
            content=message.content,
            message_hash=message_hash,
            sequence=conversation.message_count - 1,
            tokens=len(message.content.split()),
            created_at=datetime.utcnow()
        )
        db.add(msg_record)
        db.commit()
        
        return {
            "status": "saved",
            "guest_id": guest_id,
            "stored_in": ["redis", "postgresql"]
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to save message: {str(e)}")

@router.get("/chat/{guest_id}", response_model=List[ChatMessage])
async def get_guest_history(
    guest_id: str, 
    redis: Redis = Depends(get_redis_client),
    db = Depends(get_db)
):
    """Get guest chat history from PostgreSQL (with Redis as fallback)."""
    try:
        conversation = db.query(ConversationCache).filter_by(
            user_id=guest_id,
            platform="guest"
        ).first()
        
        if conversation:
            messages_db = db.query(MessageCache).filter_by(
                conversation_id=conversation.id
            ).order_by(MessageCache.sequence).all()
            
            history = [
                ChatMessage(
                    role=m.role,
                    content=m.content,
                    timestamp=m.created_at.isoformat()
                )
                for m in messages_db
            ]
            return history
        
        key = f"guest:{guest_id}"
        messages_raw = redis.lrange(key, 0, -1)
        history = [ChatMessage(**json.loads(m)) for m in messages_raw]
        return history
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve history: {str(e)}")

@router.delete("/chat/{guest_id}")
async def delete_guest_history(
    guest_id: str, 
    redis: Redis = Depends(get_redis_client),
    db = Depends(get_db)
):
    """Delete guest chat history from both Redis and PostgreSQL."""
    try:
        key = f"guest:{guest_id}"
        redis.delete(key)
        
        conversation = db.query(ConversationCache).filter_by(
            user_id=guest_id,
            platform="guest"
        ).first()
        
        if conversation:
            db.query(MessageCache).filter_by(
                conversation_id=conversation.id
            ).delete()
            db.delete(conversation)
            db.commit()
        
        return {
            "status": "deleted",
            "guest_id": guest_id,
            "deleted_from": ["redis", "postgresql"]
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to delete history: {str(e)}")

@router.post("/migrate/{guest_id}")
async def migrate_guest_to_user(
    guest_id: str,
    migration_request: MigrationRequest,
    db = Depends(get_db)
):
    """
    Migrate guest chat history to authenticated user account.
    Called when guest logs in - transfers all conversations and messages to user account.
    
    Args:
        guest_id: UUID of guest session
        migration_request: Contains authenticated_user_id
        
    Returns:
        Migration summary with counts
    """
    authenticated_user_id = migration_request.authenticated_user_id
    
    if not authenticated_user_id:
        raise HTTPException(status_code=400, detail="authenticated_user_id is required")
    
    try:
        # Query all guest conversations
        guest_conversations = db.query(ConversationCache).filter_by(
            user_id=guest_id,
            platform="guest"
        ).all()
        
        if not guest_conversations:
            return {
                "status": "success",
                "guest_id": guest_id,
                "user_id": authenticated_user_id,
                "conversations_migrated": 0,
                "messages_migrated": 0,
                "message": "No guest conversations to migrate"
            }
        
        conversations_migrated = 0
        messages_migrated = 0
        
        # Migrate each conversation
        for guest_conv in guest_conversations:
            # Create new conversation with real user_id
            new_conversation = ConversationCache(
                id=str(uuid.uuid4()),
                user_id=authenticated_user_id,  # Update to real user
                session_id=str(uuid.uuid4()),
                title=guest_conv.title,
                conversation_hash=guest_conv.conversation_hash,  # Preserve original hash
                message_count=guest_conv.message_count,
                platform="authenticated",  # Mark as authenticated
                tone=guest_conv.tone,
                created_at=datetime.utcnow(),
                migration_version="1.0"
            )
            db.add(new_conversation)
            db.flush()  # Get ID
            
            # Get all messages from guest conversation
            guest_messages = db.query(MessageCache).filter_by(
                conversation_id=guest_conv.id
            ).all()
            
            # Copy each message to new conversation
            for guest_msg in guest_messages:
                # Generate message hash if not present
                message_hash = guest_msg.message_hash or hashlib.md5(guest_msg.content.encode()).hexdigest()
                
                new_message = MessageCache(
                    id=str(uuid.uuid4()),
                    conversation_id=new_conversation.id,  # Link to new conversation
                    role=guest_msg.role,
                    content=guest_msg.content,
                    message_hash=message_hash,  # Ensure message_hash is set
                    sequence=guest_msg.sequence,
                    tokens=guest_msg.tokens,
                    created_at=guest_msg.created_at  # Preserve original timestamp
                )
                db.add(new_message)
                messages_migrated += 1
            
            conversations_migrated += 1
            
            # Mark old conversation as archived/migrated
            guest_conv.platform = "archived"  # Mark as archived
            guest_conv.created_at = datetime.utcnow()  # Update timestamp
        
        db.commit()
        
        return {
            "status": "success",
            "guest_id": guest_id,
            "user_id": authenticated_user_id,
            "conversations_migrated": conversations_migrated,
            "messages_migrated": messages_migrated,
            "message": f"Successfully migrated {conversations_migrated} conversations with {messages_migrated} messages"
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Failed to migrate guest data: {str(e)}"
        )
