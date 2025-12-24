#!/usr/bin/env python3
"""
Quick verification script to check guest data storage
Run: python verify_guest_data.py
"""

from database.database import SessionLocal
from database.models.cache import ConversationCache, MessageCache, CacheEmbedding
from database.models.content import UsageMetrics
from core.upstash_redis import RedisManager

GUEST_ID = "626c45c1-69e5-4213-98bb-d35f7787ed82"

def check_guest_data():
    db = SessionLocal()
    
    print(f"\n{'='*80}")
    print(f"VERIFYING DATA FOR GUEST: {GUEST_ID}")
    print(f"{'='*80}\n")
    
    # 1. Check Redis
    print("[1] REDIS - Looking for guest key...")
    try:
        redis = RedisManager.get_instance()
        key = f"guest:{GUEST_ID}"
        messages = redis.lrange(key, 0, -1)
        
        if messages:
            print(f"✅ Redis key EXISTS: {key}")
            print(f"   Messages stored: {len(messages)}")
            for i, msg in enumerate(messages[:2]):  # Show first 2
                print(f"   - Message {i+1}: {msg[:100]}...")
        else:
            print(f"❌ Redis key NOT FOUND: {key}")
    except Exception as e:
        print(f"❌ Redis error: {str(e)}")
    
    # 2. Check conversation_cache
    print("\n[2] CONVERSATION_CACHE - Looking for conversations...")
    try:
        conversations = db.query(ConversationCache).filter_by(
            user_id=GUEST_ID,
            platform="guest"
        ).all()
        
        if conversations:
            print(f"✅ Found {len(conversations)} conversation(s)")
            for conv in conversations:
                print(f"   - ID: {conv.id}")
                print(f"     Title: {conv.title}")
                print(f"     Messages: {conv.message_count}")
                print(f"     Created: {conv.created_at}")
        else:
            print(f"❌ No conversations found")
    except Exception as e:
        print(f"❌ Error: {str(e)}")
    
    # 3. Check message_cache
    print("\n[3] MESSAGE_CACHE - Looking for messages...")
    try:
        conversations = db.query(ConversationCache).filter_by(
            user_id=GUEST_ID,
            platform="guest"
        ).all()
        
        if conversations:
            total_messages = 0
            for conv in conversations:
                messages = db.query(MessageCache).filter_by(
                    conversation_id=conv.id
                ).order_by(MessageCache.sequence).all()
                total_messages += len(messages)
                
                if messages:
                    print(f"✅ Found {len(messages)} message(s) in conversation {conv.id}")
                    for msg in messages[:3]:  # Show first 3
                        print(f"   - [{msg.role}] {msg.content[:60]}...")
                        print(f"     Hash: {msg.message_hash[:20]}..." if msg.message_hash else "     Hash: NOT SET ❌")
            
            if total_messages == 0:
                print(f"❌ No messages found")
        else:
            print(f"❌ No conversations to check")
    except Exception as e:
        print(f"❌ Error: {str(e)}")
    
    # 4. Check cache_embeddings
    print("\n[4] CACHE_EMBEDDINGS - Looking for embeddings...")
    try:
        conversations = db.query(ConversationCache).filter_by(
            user_id=GUEST_ID,
            platform="guest"
        ).all()
        
        if conversations:
            total_embeddings = 0
            for conv in conversations:
                embeddings = db.query(CacheEmbedding).filter_by(
                    conversation_id=conv.id
                ).all()
                total_embeddings += len(embeddings)
            
            if total_embeddings > 0:
                print(f"✅ Found {total_embeddings} embedding(s)")
                first_embedding = db.query(CacheEmbedding).filter(
                    CacheEmbedding.conversation_id.in_(
                        [c.id for c in conversations]
                    )
                ).first()
                if first_embedding:
                    print(f"   - Dimension: {first_embedding.embedding_dim}")
                    print(f"   - Model: {first_embedding.embedding_model}")
                    print(f"   - Text: {first_embedding.text_chunk[:60]}...")
            else:
                print(f"❌ No embeddings found")
        else:
            print(f"❌ No conversations to check")
    except Exception as e:
        print(f"❌ Error: {str(e)}")
    
    # 5. Check usage_metrics
    print("\n[5] USAGE_METRICS - Looking for metrics...")
    try:
        usage = db.query(UsageMetrics).filter_by(user_id=GUEST_ID).first()
        
        if usage:
            print(f"✅ Usage metrics found")
            print(f"   - Tier: {usage.tier}")
            print(f"   - Total requests: {usage.total_requests}")
            print(f"   - Cache hits: {usage.cache_hits}")
            print(f"   - Cache misses: {usage.cache_misses}")
            print(f"   - Monthly limit: {usage.monthly_request_limit}")
        else:
            print(f"❌ No usage metrics found")
    except Exception as e:
        print(f"❌ Error: {str(e)}")
    
    # Summary
    print(f"\n{'='*80}")
    print("SUMMARY")
    print(f"{'='*80}")
    
    conv_count = db.query(ConversationCache).filter_by(user_id=GUEST_ID, platform="guest").count()
    msg_count = 0
    for conv in db.query(ConversationCache).filter_by(user_id=GUEST_ID, platform="guest").all():
        msg_count += db.query(MessageCache).filter_by(conversation_id=conv.id).count()
    
    emb_count = 0
    for conv in db.query(ConversationCache).filter_by(user_id=GUEST_ID, platform="guest").all():
        emb_count += db.query(CacheEmbedding).filter_by(conversation_id=conv.id).count()
    
    usage_exists = db.query(UsageMetrics).filter_by(user_id=GUEST_ID).first() is not None
    
    print(f"Conversations: {conv_count} {'✅' if conv_count > 0 else '❌'}")
    print(f"Messages: {msg_count} {'✅' if msg_count > 0 else '❌'}")
    print(f"Embeddings: {emb_count} {'✅' if emb_count > 0 else '❌'}")
    print(f"Usage Metrics: {'✅' if usage_exists else '❌'}")
    print(f"{'='*80}\n")
    
    db.close()

if __name__ == "__main__":
    check_guest_data()
