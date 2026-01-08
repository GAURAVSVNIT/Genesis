"""Guest chat endpoint - stores in both Redis and PostgreSQL for persistence."""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from core.upstash_redis import RedisManager, RedisClientType
from core.vertex_ai_embeddings import get_vertex_ai_embedding_service
from core.cache_metrics import CacheMetricsTracker
from database.database import SessionLocal
from database.models.cache import ConversationCache, MessageCache, CacheEmbedding
from database.models.content import UsageMetrics
import json
from typing import List
from datetime import datetime
import uuid
import hashlib
import logging
import time

logger = logging.getLogger(__name__)

router = APIRouter()

class ChatMessage(BaseModel):
    role: str
    content: str
    timestamp: str

class MigrationRequest(BaseModel):
    authenticated_user_id: str

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
        try:
            if db:
                db.close()
        except:
            pass

@router.post("/chat/{guest_id}")
async def save_guest_message(
    guest_id: str, 
    message: ChatMessage,
    db = Depends(get_db)
):
    """Save guest message to both Redis (hot) and PostgreSQL (cold) storage."""
    try:
        # Store in Redis (hot cache)
        redis = RedisManager.get_instance()
        key = f"guest:{guest_id}"
        print(f"[Redis] Storing message with key: {key}")
        redis.rpush(key, json.dumps(message.model_dump()))
        print(f"[Redis] Setting expiration to 86400 seconds")
        redis.expire(key, 86400)
        print(f"[Redis] Message stored successfully!")
        
        # Store in PostgreSQL (persistent)
        print(f"[PostgreSQL] Querying conversation for guest: {guest_id}")
        conversation = db.query(ConversationCache).filter_by(
            user_id=guest_id,
            platform="guest"
        ).first()
        
        if not conversation:
            print(f"[PostgreSQL] Creating new conversation...")
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
            print(f"[PostgreSQL] Conversation created: {conversation.id}")
        
        # Get current message count before incrementing (for sequence)
        current_sequence = conversation.message_count
        
        # Generate hash from message content
        message_hash = hashlib.md5(message.content.encode()).hexdigest()
        
        # Use first USER message as title for conversations without titles
        # Only update title for user messages, not assistant messages
        if message.role == "user" and conversation.title.startswith("Guest Chat - "):
            # Extract first 50 chars of first message as title
            title_text = message.content[:50].strip()
            if title_text:
                conversation.title = title_text
        
        msg_record = MessageCache(
            id=str(uuid.uuid4()),
            conversation_id=conversation.id,
            role=message.role,
            content=message.content,
            message_hash=message_hash,
            sequence=current_sequence,
            tokens=len(message.content.split()),
            created_at=datetime.utcnow()
        )
        print(f"[PostgreSQL] Adding message record with sequence {current_sequence}...")
        db.add(msg_record)
        
        # Increment message count AFTER creating message record
        conversation.message_count += 1
        print(f"[PostgreSQL] Updated message count to: {conversation.message_count}")
        
        print(f"[PostgreSQL] Committing to database...")
        db.commit()
        print(f"[PostgreSQL] Message committed!")
        
        # Generate embeddings for semantic search
        print(f"[Embeddings] Generating embedding for message...")
        try:
            embedding_service = get_vertex_ai_embedding_service()
            embedding_vector = embedding_service.generate_embedding(message.content)
            
            if not embedding_vector:
                raise ValueError("Embedding service returned empty vector")
            
            print(f"[Embeddings] Generated embedding with {len(embedding_vector)} dimensions")
            
            # Store embedding in database
            embedding_record = CacheEmbedding(
                id=str(uuid.uuid4()),
                conversation_id=conversation.id,
                message_id=msg_record.id,
                embedding=json.dumps(embedding_vector),  # Store as JSON string
                embedding_model="multimodalembedding@001",
                embedding_dim=len(embedding_vector),
                text_chunk=message.content,
                chunk_index=current_sequence,
                created_at=datetime.utcnow()
            )
            db.add(embedding_record)
            db.commit()
            print(f"[Embeddings] ✓ Embedding stored in cache_embeddings table ({len(embedding_vector)} dims)!")
        except Exception as e:
            print(f"[Embeddings] ✗ FAILED to generate/store embedding: {str(e)}")
            logger.error(f"Embedding generation failed: {str(e)}")
        
        # Track usage metrics for this guest
        try:
            usage = db.query(UsageMetrics).filter_by(user_id=guest_id).first()
            if not usage:
                usage = UsageMetrics(
                    id=str(uuid.uuid4()),
                    user_id=guest_id,
                    tier="guest",
                    total_requests=1,
                    cache_misses=1,
                    monthly_request_limit=100
                )
                db.add(usage)
                print(f"[UsageMetrics] ✓ Created new usage metrics record for guest: {guest_id}")
            else:
                usage.total_requests += 1
                usage.cache_misses += 1
                print(f"[UsageMetrics] ✓ Updated usage metrics for guest: {guest_id} (requests: {usage.total_requests})")
            
            db.commit()
        except Exception as e:
            print(f"[UsageMetrics] ✗ Warning - could not track usage metrics: {str(e)}")
            logger.warning(f"UsageMetrics tracking failed: {str(e)}")
        
        return {
            "status": "saved",
            "guest_id": guest_id,
            "stored_in": ["redis", "postgresql"],
            "message_id": msg_record.id,
            "conversation_id": conversation.id
        }
    except Exception as e:
        print(f"[ERROR] Failed to save message: {str(e)}")
        logger.error(f"Error saving message: {str(e)}", exc_info=True)
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to save message: {str(e)}")

@router.get("/chat/{guest_id}", response_model=List[ChatMessage])
async def get_guest_history(
    guest_id: str, 
    db = Depends(get_db)
):
    """Get guest chat history from PostgreSQL (with Redis as fallback)."""
    start_time = time.time()
    try:
        conversation = db.query(ConversationCache).filter_by(
            user_id=guest_id,
            platform="guest"
        ).first()
        
        if conversation:
            messages_db = db.query(MessageCache).filter_by(
                conversation_id=conversation.id
            ).order_by(MessageCache.sequence).all()
            
            # Record cache hit (data found in PostgreSQL)
            response_time_ms = (time.time() - start_time) * 1000
            CacheMetricsTracker.record_cache_hit(db)
            CacheMetricsTracker.record_response_time(db, response_time_ms)
            print(f"[Cache] Hit - Retrieved {len(messages_db)} messages from PostgreSQL in {response_time_ms:.2f}ms")
            
            history = [
                ChatMessage(
                    role=m.role,
                    content=m.content,
                    timestamp=m.created_at.isoformat()
                )
                for m in messages_db
            ]
            return history
        
        # Try Redis fallback
        redis = RedisManager.get_instance()
        key = f"guest:{guest_id}"
        messages_raw = redis.lrange(key, 0, -1)
        
        if messages_raw:
            # Record cache hit (data found in Redis)
            response_time_ms = (time.time() - start_time) * 1000
            CacheMetricsTracker.record_cache_hit(db)
            CacheMetricsTracker.record_response_time(db, response_time_ms)
            print(f"[Cache] Hit - Retrieved {len(messages_raw)} messages from Redis in {response_time_ms:.2f}ms")
            history = [ChatMessage(**json.loads(m)) for m in messages_raw]
            return history
        
        # Cache miss - no data found
        CacheMetricsTracker.record_cache_miss(db)
        print(f"[Cache] Miss - No history found for guest {guest_id}")
        return []
        
    except Exception as e:
        logger.error(f"❌ Error retrieving history: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to retrieve history: {str(e)}")

@router.delete("/chat/{guest_id}")
async def delete_guest_history(
    guest_id: str, 
    db = Depends(get_db)
):
    """Delete guest chat history from both Redis and PostgreSQL."""
    try:
        redis = RedisManager.get_instance()
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
            # Update the existing guest conversation in-place
            # instead of creating a new one
            guest_conv.user_id = authenticated_user_id  # Update to real user
            guest_conv.platform = "authenticated"  # Mark as authenticated (not archived!)
            
            # Get all messages from this conversation and ensure they have message_hash
            guest_messages = db.query(MessageCache).filter_by(
                conversation_id=guest_conv.id
            ).all()
            
            # Update messages to ensure message_hash is set
            for guest_msg in guest_messages:
                if not guest_msg.message_hash:
                    guest_msg.message_hash = hashlib.md5(guest_msg.content.encode()).hexdigest()
                messages_migrated += 1
            
            conversations_migrated += 1
        
        db.commit()
        
        # Clean up Redis - delete guest session key
        try:
            redis = RedisManager.get_instance()
            key = f"guest:{guest_id}"
            redis.delete(key)
            print(f"[Redis] ✓ Deleted guest session key: {key}")
        except Exception as e:
            print(f"[Redis] ✗ Warning - could not delete guest key: {str(e)}")
            logger.warning(f"Redis cleanup failed: {str(e)}")
        
        # Migrate usage metrics from guest to authenticated user
        try:
            guest_usage = db.query(UsageMetrics).filter_by(user_id=guest_id).first()
            if guest_usage:
                # Check if authenticated user ALREADY has usage metrics
                user_usage = db.query(UsageMetrics).filter_by(user_id=authenticated_user_id).first()
                if user_usage:
                    # Merge counts
                    user_usage.total_requests += guest_usage.total_requests
                    user_usage.cache_misses += guest_usage.cache_misses
                    # Delete guest record to avoid duplicate/orphaned record
                    db.delete(guest_usage)
                    print(f"[UsageMetrics] ✓ Merged guest metrics into existing user metrics: {authenticated_user_id}")
                else:
                    # No existing user metrics, safe to reassign
                    guest_usage.user_id = authenticated_user_id
                    guest_usage.tier = "authenticated"
                    print(f"[UsageMetrics] ✓ Reassigned guest metrics to user: {authenticated_user_id}")
                db.commit()
            else:
                print(f"[UsageMetrics] ℹ No guest usage metrics to migrate")
        except Exception as e:
            print(f"[UsageMetrics] ✗ Warning - could not migrate usage metrics: {str(e)}")
            logger.warning(f"UsageMetrics migration failed: {str(e)}")
        
        # Record migration in cache_migrations table
        try:
            from database.models.cache import CacheMigration
            migration_record = CacheMigration(
                id=str(uuid.uuid4()),
                version="1.0",
                migration_type="guest_to_user",
                status="completed",
                records_migrated=messages_migrated,
                records_failed=0,
                started_at=datetime.utcnow(),
                completed_at=datetime.utcnow(),
                source="guest_session",
                destination="authenticated_user",
                notes=f"Migrated {conversations_migrated} conversations with {messages_migrated} messages from guest {guest_id}"
            )
            db.add(migration_record)
            db.commit()
            print(f"[Migration] Recorded migration in cache_migrations table")
        except Exception as migration_error:
            print(f"[Migration] Warning - could not record migration: {str(migration_error)}")
        
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
