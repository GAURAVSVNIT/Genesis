# Quick Testing Guide - Guest Chat Data Storage

## What Was Fixed

Three data storage issues were resolved:

1. ✓ **usage_metrics** - Now tracks guest requests, tokens, tier info
2. ✓ **cache_embeddings** - Now stores embeddings with proper error handling  
3. ✓ **cache_content_mapping** - Now creates mapping entries for each message
4. ✓ **Upstash Redis** - Already working (guest:{guest_id} format confirmed)

---

## Test the Endpoint

### Step 1: Start Backend
```powershell
cd e:\genesis\Genesis\apps\backend
python -m uvicorn main:app --reload --port 8000
```

### Step 2: Send a Test Message
```powershell
# Using PowerShell
$guest_id = [guid]::NewGuid().ToString()
$body = @{
    "role" = "user"
    "content" = "Hello, this is a test message for guest chat"
    "timestamp" = (Get-Date).ToString("o")
} | ConvertTo-Json

Invoke-WebRequest -Uri "http://localhost:8000/v1/guest/chat/$guest_id" `
  -Method POST `
  -ContentType "application/json" `
  -Body $body
```

Or using curl:
```bash
curl -X POST "http://localhost:8000/v1/guest/chat/test-guest-001" \
  -H "Content-Type: application/json" \
  -d '{"role":"user","content":"Test message","timestamp":"2025-12-21T12:00:00Z"}'
```

### Step 3: Check Backend Logs

You should see logs like:
```
[Redis] Storing message with key: guest:test-guest-001
[Redis] Message stored successfully!
[PostgreSQL] Creating new conversation...
[PostgreSQL] Conversation created: <uuid>
[PostgreSQL] Adding message record...
[PostgreSQL] Message committed!
[Embeddings] Generating embedding for message...
[Embeddings] ✓ Embedding stored in cache_embeddings table (1408 dims)!
[UsageMetrics] ✓ Created new usage metrics record for guest: test-guest-001
[CacheMapping] ✓ Created cache_content_mapping entry for message: <uuid>
```

---

## Verify Data in Database

### Check conversation_cache
```sql
SELECT id, user_id, title, message_count, platform, created_at 
FROM conversation_cache 
WHERE platform = 'guest' 
ORDER BY created_at DESC 
LIMIT 5;
```

Expected: 1 row per guest with message_count incremented

### Check message_cache
```sql
SELECT m.id, m.role, m.content, m.sequence, c.user_id
FROM message_cache m
JOIN conversation_cache c ON m.conversation_id = c.id
WHERE c.platform = 'guest'
ORDER BY m.created_at DESC
LIMIT 5;
```

Expected: Messages stored with correct sequence numbers

### Check cache_embeddings
```sql
SELECT id, conversation_id, embedding_dim, text_chunk, created_at
FROM cache_embeddings
WHERE conversation_id IN (
  SELECT id FROM conversation_cache WHERE platform = 'guest'
)
ORDER BY created_at DESC
LIMIT 5;
```

Expected: embedding_dim = 1408, text_chunk = message content

### Check usage_metrics
```sql
SELECT user_id, total_requests, cache_misses, tier, created_at
FROM usage_metrics
WHERE tier = 'guest'
ORDER BY created_at DESC
LIMIT 5;
```

Expected: user_id = guest_id, tier = 'guest', total_requests >= 1

### Check cache_content_mapping
```sql
SELECT cache_type, cache_id, user_id, is_synced, created_at
FROM cache_content_mapping
WHERE user_id IN (
  SELECT user_id FROM usage_metrics WHERE tier = 'guest'
)
ORDER BY created_at DESC
LIMIT 5;
```

Expected: cache_type = 'message', is_synced = true

---

## Verify Data in Redis

### Using Upstash Console
1. Go to https://console.upstash.com/redis
2. Select your database
3. Open the console
4. Run: `KEYS guest:*`
5. For each key, run: `LRANGE <key> 0 -1`

Expected format:
```json
[
  {"role": "user", "content": "...", "timestamp": "..."},
  {"role": "assistant", "content": "...", "timestamp": "..."}
]
```

### Using Python
```python
from core.upstash_redis import RedisManager
import json

redis = RedisManager.get_instance()

# List all guest keys
keys = redis.keys("guest:*")
print(f"Found {len(keys)} guest conversations")

# Get messages from first guest
if keys:
    key = keys[0].decode() if isinstance(keys[0], bytes) else keys[0]
    messages = redis.lrange(key, 0, -1)
    for msg in messages:
        print(json.loads(msg))
```

---

## Test GET and DELETE

### Retrieve chat history
```bash
curl -X GET "http://localhost:8000/v1/guest/chat/test-guest-001"
```

Expected: Array of messages with role, content, timestamp

### Delete chat history
```bash
curl -X DELETE "http://localhost:8000/v1/guest/chat/test-guest-001"
```

Expected: Message deleted from both Redis and PostgreSQL

---

## Performance Metrics Check

```sql
-- Check cache hit/miss tracking
SELECT cache_hits, cache_misses, total_requests, 
       ROUND(100.0 * cache_hits / total_requests, 2) as hit_rate_percent,
       avg_response_time,
       recorded_at
FROM cache_metrics
ORDER BY recorded_at DESC
LIMIT 5;
```

Expected: Metrics are recorded for each guest chat operation

---

## Troubleshooting

### If UsageMetrics not created:
```sql
-- Check if GUID type is supported
SELECT column_name, data_type 
FROM information_schema.columns 
WHERE table_name = 'usage_metrics';
```

### If CacheContentMapping not created:
```sql
-- Check if table exists
SELECT EXISTS(
  SELECT 1 FROM information_schema.tables 
  WHERE table_name = 'cache_content_mapping'
);
```

### If Embeddings fail:
Check logs for `[Embeddings] ✗ FAILED` message
Common issues:
- Vertex AI service not initialized
- Invalid API key
- Network timeout

The endpoint will still succeed but without embeddings (graceful degradation)

---

## Summary

All three issues are now fixed:

| Component | Status | Check |
|-----------|--------|-------|
| usage_metrics | ✓ FIXED | Query table, should have records with tier='guest' |
| cache_embeddings | ✓ FIXED | Query table, should have records with embedding_dim=1408 |
| cache_content_mapping | ✓ FIXED | Query table, should have records with cache_type='message' |
| Upstash Redis | ✓ OK | Run KEYS guest:* in console |

Test by sending a message and verifying all tables get data!
