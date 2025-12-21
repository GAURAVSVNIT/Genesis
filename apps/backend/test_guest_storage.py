"""
Test script to verify guest chat data storage in both Redis and PostgreSQL.
"""

import asyncio
import json
import uuid
from datetime import datetime
from core.upstash_redis import RedisManager
from database.database import SessionLocal
from database.models.cache import ConversationCache, MessageCache

async def test_storage():
    """Test storing and retrieving guest chat data."""
    
    print("=" * 60)
    print("TESTING GUEST CHAT DATA STORAGE")
    print("=" * 60)
    
    # Test data
    guest_id = str(uuid.uuid4())
    print(f"\n✓ Generated guest_id: {guest_id}")
    
    test_message = {
        "role": "user",
        "content": "Hello, this is a test message",
        "timestamp": datetime.utcnow().isoformat()
    }
    
    # Test 1: Redis Storage
    print("\n[TEST 1] Redis Storage")
    print("-" * 60)
    try:
        redis = RedisManager.get_instance()
        key = f"guest:{guest_id}"
        
        # Store message
        redis.rpush(key, json.dumps(test_message))
        print(f"✅ Message stored in Redis with key: {key}")
        
        # Set expiration
        redis.expire(key, 86400)
        print(f"✅ TTL set to 86400 seconds")
        
        # Retrieve to verify
        stored_messages = redis.lrange(key, 0, -1)
        print(f"✅ Retrieved {len(stored_messages)} message(s) from Redis")
        
        if stored_messages:
            retrieved = json.loads(stored_messages[0])
            print(f"   Content: {retrieved['content']}")
        
    except Exception as e:
        print(f"❌ Redis Storage Error: {str(e)}")
        return False
    
    # Test 2: PostgreSQL Storage
    print("\n[TEST 2] PostgreSQL Storage")
    print("-" * 60)
    try:
        db = SessionLocal()
        
        # Check if conversation exists
        conversation = db.query(ConversationCache).filter_by(
            user_id=guest_id,
            platform="guest"
        ).first()
        
        if not conversation:
            # Create new conversation
            import hashlib
            conversation_hash = hashlib.sha256(guest_id.encode()).hexdigest()[:64]
            conversation = ConversationCache(
                id=str(uuid.uuid4()),
                user_id=guest_id,
                session_id=guest_id,
                title=f"Test Chat - {guest_id}",
                conversation_hash=conversation_hash,
                message_count=0,
                platform="guest",
                tone="neutral",
                created_at=datetime.utcnow(),
                migration_version="1.0"
            )
            db.add(conversation)
            db.flush()
            print(f"✅ Conversation created: {conversation.id}")
        
        conversation.message_count += 1
        
        # Create message record
        import hashlib
        message_hash = hashlib.md5(test_message['content'].encode()).hexdigest()
        
        msg_record = MessageCache(
            id=str(uuid.uuid4()),
            conversation_id=conversation.id,
            role=test_message['role'],
            content=test_message['content'],
            message_hash=message_hash,
            sequence=conversation.message_count - 1,
            tokens=len(test_message['content'].split()),
            created_at=datetime.utcnow()
        )
        
        db.add(msg_record)
        db.commit()
        print(f"✅ Message committed to PostgreSQL: {msg_record.id}")
        
        # Verify data was stored
        stored_conversation = db.query(ConversationCache).filter_by(id=conversation.id).first()
        if stored_conversation:
            stored_messages = db.query(MessageCache).filter_by(
                conversation_id=conversation.id
            ).all()
            print(f"✅ Retrieved {len(stored_messages)} message(s) from PostgreSQL")
            if stored_messages:
                print(f"   Content: {stored_messages[0].content}")
        
        db.close()
        
    except Exception as e:
        print(f"❌ PostgreSQL Storage Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
    
    # Test 3: Verify Both Storages
    print("\n[TEST 3] Cross-Storage Verification")
    print("-" * 60)
    try:
        redis = RedisManager.get_instance()
        db = SessionLocal()
        
        # Check Redis
        key = f"guest:{guest_id}"
        redis_data = redis.lrange(key, 0, -1)
        print(f"✅ Redis data count: {len(redis_data)}")
        
        # Check PostgreSQL
        conversation = db.query(ConversationCache).filter_by(
            user_id=guest_id,
            platform="guest"
        ).first()
        
        if conversation:
            pg_data = db.query(MessageCache).filter_by(
                conversation_id=conversation.id
            ).all()
            print(f"✅ PostgreSQL data count: {len(pg_data)}")
        
        db.close()
        
        if len(redis_data) > 0 and conversation and len(pg_data) > 0:
            print("\n" + "=" * 60)
            print("✅ ALL TESTS PASSED!")
            print("=" * 60)
            print(f"\nSummary:")
            print(f"  • Redis: 1 message stored")
            print(f"  • PostgreSQL: 1 conversation + 1 message stored")
            print(f"  • Guest ID: {guest_id}")
            return True
        else:
            print("\n❌ Data mismatch between Redis and PostgreSQL")
            return False
            
    except Exception as e:
        print(f"❌ Verification Error: {str(e)}")
        return False

if __name__ == "__main__":
    success = asyncio.run(test_storage())
    exit(0 if success else 1)
