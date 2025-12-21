# Root Cause Analysis: Missing Data Storage

## Issues Identified

### 1. **Usage Metrics Not Being Stored**
   - **Problem**: The `guest.py` endpoint imports `CacheMetricsTracker` but does NOT track `UsageMetrics` table
   - **Root Cause**: Only `CacheMetrics` is being tracked (cache hits/misses), but not `UsageMetrics` (user request counts, tokens, costs)
   - **Missing Code**: No code to create/update `UsageMetrics` record with guest user_id

### 2. **cache_embeddings Not Being Stored**
   - **Problem**: Embeddings ARE attempted but fail silently
   - **Root Cause**: See guest.py line 127-134 - there's a try/except that catches embedding generation errors but doesn't fail
   - **Status**: ✅ Code exists but needs error handling improvement

### 3. **cache_content_mapping Has No Entry**
   - **Problem**: No code creates `CacheContentMapping` records
   - **Root Cause**: The mapping table is never populated during guest chat save
   - **Missing Code**: After creating message/embedding, should create cache_content_mapping entry

### 4. **Upstash Has No `guest:...` Entry**
   - **Problem**: Actually works, but Redis key format needs verification
   - **Root Cause**: Check if Redis is actually being called or if `USE_LOCAL_REDIS=False` is preventing storage
   - **Expected Format**: `guest:{guest_id}` as JSON array of messages

---

## Solutions

### Fix 1: Track Usage Metrics for Guests
Add to `guest.py` `save_guest_message()`:
```python
# After db.commit() for embeddings
try:
    # Track usage metrics
    from database.models.content import UsageMetrics
    usage = db.query(UsageMetrics).filter_by(user_id=guest_id).first()
    if not usage:
        usage = UsageMetrics(
            id=str(uuid.uuid4()),
            user_id=guest_id,
            tier="guest",
            total_requests=1,
            cache_misses=1
        )
        db.add(usage)
    else:
        usage.total_requests += 1
        usage.cache_misses += 1
    
    db.commit()
    print(f"[Metrics] Recorded usage metrics for guest: {guest_id}")
except Exception as e:
    print(f"[Metrics] Warning - could not record usage metrics: {str(e)}")
```

### Fix 2: Create cache_content_mapping Entry
Add after embedding is stored:
```python
# Create cache content mapping (links cache to content)
try:
    from database.models.content import CacheContentMapping
    mapping = CacheContentMapping(
        id=str(uuid.uuid4()),
        cache_type="message",
        cache_id=msg_record.id,
        content_id=None,  # No generated_content for guest chat
        user_id=guest_id,
        cache_backend="postgresql",
        content_backend="postgresql",
        is_synced=True
    )
    db.add(mapping)
    db.commit()
    print(f"[Mapping] Created cache_content_mapping entry")
except Exception as e:
    print(f"[Mapping] Warning - could not create mapping: {str(e)}")
```

### Fix 3: Improve Embedding Error Handling
Replace try/except in guest.py (line 127-134) with:
```python
try:
    embedding_service = get_vertex_ai_embedding_service()
    embedding_vector = embedding_service.generate_embedding(message.content)
    
    if not embedding_vector:
        raise ValueError("Embedding service returned empty vector")
    
    embedding_record = CacheEmbedding(
        id=str(uuid.uuid4()),
        conversation_id=conversation.id,
        message_id=msg_record.id,
        embedding=json.dumps(embedding_vector),
        embedding_model="multimodalembedding@001",
        embedding_dim=len(embedding_vector),
        text_chunk=message.content,
        chunk_index=conversation.message_count - 1,
        created_at=datetime.utcnow()
    )
    db.add(embedding_record)
    db.commit()
    print(f"[Embeddings] ✓ Embedding stored: {len(embedding_vector)} dimensions")
except Exception as e:
    print(f"[Embeddings] ✗ FAILED: {str(e)}")
    # Log but don't fail the entire request
    logger.error(f"Embedding generation failed: {str(e)}")
```

### Fix 4: Verify Redis Setup
Check `.env` and ensure:
```
USE_LOCAL_REDIS=False  # ✓ Using Upstash
UPSTASH_REDIS_REST_URL=https://apparent-pony-24821.upstash.io
UPSTASH_REDIS_REST_TOKEN=AWD1AAIncD...
```

---

## Implementation Order

1. **Update guest.py** - Add UsageMetrics tracking
2. **Update guest.py** - Add CacheContentMapping creation
3. **Improve error handling** - Better embedding error messages
4. **Test end-to-end** - Verify all tables get data

---

## Verification Queries

After fixes, run these to verify:

```sql
-- Check guest conversations
SELECT id, user_id, platform, message_count FROM conversation_cache WHERE platform='guest' LIMIT 5;

-- Check messages
SELECT id, conversation_id, role, content FROM message_cache LIMIT 5;

-- Check embeddings
SELECT id, conversation_id, embedding_dim FROM cache_embeddings LIMIT 5;

-- Check metrics
SELECT cache_hits, cache_misses, total_requests FROM cache_metrics ORDER BY recorded_at DESC LIMIT 1;

-- Check usage metrics for guest
SELECT user_id, total_requests, cache_hits, tier FROM usage_metrics WHERE tier='guest' LIMIT 5;

-- Check cache content mapping
SELECT cache_type, cache_id, user_id, is_synced FROM cache_content_mapping WHERE user_id LIKE '%-%-%-' LIMIT 5;
```
