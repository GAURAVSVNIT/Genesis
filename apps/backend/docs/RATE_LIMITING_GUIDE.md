# Rate Limiting & Caching Implementation Guide

## 📊 What Was Implemented

### 1. **Sliding Window Rate Limiter** (`core/rate_limiter.py`)

#### How It Works
```
Fixed Window (BAD):
┌─ Minute 1 ─┬─ Minute 2 ─┐
└─────────────┘─────────────┘
 5 requests    5 requests
 User can send 10 in 2 seconds at boundary (at 59s and 1s)

Sliding Window (GOOD):
Now ─────────────────────────────────→
│←─ 60 second window ─→│
Only allows 5 requests in any 60-second window
No burst attacks possible
```

#### Key Features
- ✅ **Sliding window** using Redis sorted sets
- ✅ **Per-user tracking** (user_id, session_id, or IP)
- ✅ **Premium tier support** (3x higher limits)
- ✅ **Automatic cleanup** (removes old timestamps)
- ✅ **Returns remaining requests** (for client feedback)
- ✅ **Returns reset time** (when user can retry)

#### Configuration
```python
RATE_LIMITERS = {
    "free_user": SlidingWindowRateLimiter(max_requests=5, window_seconds=60),      # 5 req/min
    "premium_user": SlidingWindowRateLimiter(max_requests=100, window_seconds=60),  # 100 req/min
    "guest": SlidingWindowRateLimiter(max_requests=3, window_seconds=60),           # 3 req/min
    "api_key": SlidingWindowRateLimiter(max_requests=1000, window_seconds=3600),   # 1000 req/hour
}
```

---

### 2. **Response Caching** (`core/response_cache.py`)

#### How It Works
```
Request 1: "Summarize AI trends"
   ↓
Not in cache
   ↓
Generate response (takes 5 seconds)
   ↓
Store in Redis for 5 minutes
   ↓
Return response

Request 2: "Summarize AI trends" (same prompt)
   ↓
Found in cache!
   ↓
Return immediately (<10ms)
```

#### Features
- ✅ **MD5 hashing** of request parameters
- ✅ **Configurable TTL** per endpoint
- ✅ **JSON serialization** for complex objects
- ✅ **Error resilience** (cache miss = fall through to generation)
- ✅ **Easy invalidation** (delete if needed)

#### TTL Configuration
```python
CACHES = {
    "content": ResponseCache(ttl_seconds=300),      # 5 minutes
    "embeddings": ResponseCache(ttl_seconds=3600),  # 1 hour
    "trends": ResponseCache(ttl_seconds=1800),      # 30 minutes
    "seo": ResponseCache(ttl_seconds=600),          # 10 minutes
}
```

---

### 3. **Updated Content Generation Endpoint** (`api/v1/content.py`)

#### Flow
```
1. Extract identifier (user_id or IP)
2. Check rate limit (sliding window)
   ├─ If exceeded → return 429 error
   └─ If allowed → continue
3. Check response cache
   ├─ If cached → return with rate limit info
   └─ If not cached → continue
4. Generate content (Vertex AI + LangGraph)
5. Cache response for future requests
6. Return response with rate limit headers
```

#### Response Format
```json
{
    "success": true,
    "content": "Generated content here...",
    "safety_checks": {...},
    "tokens_used": 450,
    "rate_limit_remaining": 4,      // NEW!
    "rate_limit_reset_after": 0     // NEW!
}
```

---

## 🔧 How to Use

### Basic Usage (Content Generation)
```bash
# Request 1 - Will generate (no cache)
curl -X POST "http://localhost:8000/v1/content/generate" \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Write a blog post about AI",
    "safety_level": "moderate"
  }'

# Response: rate_limit_remaining: 4

# Request 2 - Same prompt (will use cache!)
curl -X POST "http://localhost:8000/v1/content/generate" \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Write a blog post about AI",
    "safety_level": "moderate"
  }'

# Response: Returns from cache instantly, rate_limit_remaining: 3
```

### Handle Rate Limiting (Client Code)
```python
import requests

response = requests.post(
    "http://localhost:8000/v1/content/generate",
    json={"prompt": "Your prompt here", "safety_level": "moderate"}
)

if response.status_code == 429:
    # Rate limited
    reset_after = response.json()["detail"]  # Extract retry-after
    print(f"Rate limited. Try again in {reset_after} seconds")
elif response.status_code == 200:
    data = response.json()
    print(f"Remaining requests: {data['rate_limit_remaining']}")
    
    if data['rate_limit_remaining'] <= 1:
        print("⚠️ Warning: You're near the rate limit!")
```

---

## 📈 Performance Impact

### Before Implementation
```
Same request twice:
Request 1: 5 seconds (generate)
Request 2: 5 seconds (generate again)
Total: 10 seconds
```

### After Implementation
```
Same request twice:
Request 1: 5 seconds (generate + cache)
Request 2: 10ms (cached!)
Total: 5.01 seconds

✅ ~1000x faster for cached requests!
```

---

## 🎯 Real-World Scenarios

### Scenario 1: Free User Quota
```
User quota: 5 requests per minute
Action:
1. First request allowed ✅ (remaining: 4)
2. Five more requests within 60s ❌ (rate limited)
3. Wait 30s (oldest request rolls out of window)
4. Can make 1 more request ✅
```

### Scenario 2: Caching Benefit
```
Blog writer using same prompt for multiple variations:
Request: "Write SEO-optimized blog post about fitness"
→ Generated once, cached for 5 minutes
→ 100 users requesting same thing get instant response
→ Saves significant Vertex AI costs!
```

### Scenario 3: Premium vs Free
```
Free: 5 req/min
Premium: 15 req/min (3x)

Same cost in Vertex AI, but better UX for premium users
```

---

## 🔐 Redis Data Structure

### Rate Limit Storage
```
Key: rate_limit:sliding:{user_id_or_ip}
Type: Sorted Set (timestamps as scores)
TTL: window_seconds + 1 (auto-cleanup)

Example:
{
    "1703097300.123": 1703097300.123,
    "1703097302.456": 1703097302.456,
    "1703097305.789": 1703097305.789,
}
```

### Cache Storage
```
Key: cache:content:{md5_hash_of_request}
Type: String (JSON)
TTL: 300 seconds (5 minutes)

Example:
cache:content:a1b2c3d4e5f6... = '{"success": true, "content": "..."}'
```

---

## ⚙️ Configuration Guide

### Adjust Rate Limits
Edit `core/rate_limiter.py`:
```python
RATE_LIMITERS = {
    "free_user": SlidingWindowRateLimiter(max_requests=10, window_seconds=60),  # Increase to 10
    "premium_user": SlidingWindowRateLimiter(max_requests=200, window_seconds=60),  # Increase
}
```

### Adjust Cache TTLs
Edit `core/response_cache.py`:
```python
CACHES = {
    "content": ResponseCache(ttl_seconds=600),  # Increase to 10 minutes
}
```

### Per-Endpoint Rate Limits
```python
# In your endpoint:
limiter = RATE_LIMITERS["custom"]  # Create custom preset
# or
limiter = SlidingWindowRateLimiter(max_requests=20, window_seconds=60)
```

---

## 🧪 Testing

### Test Rate Limiting
```bash
# Send 6 requests quickly (limit is 5)
for i in {1..6}; do
  curl -X POST "http://localhost:8000/v1/content/generate" \
    -H "Content-Type: application/json" \
    -d '{"prompt":"test", "safety_level":"moderate"}' \
    -w "\nStatus: %{http_code}\n\n"
done

# 6th request should return 429
```

### Test Caching
```bash
# Send same request twice
# First: ~5 seconds
# Second: ~10ms

curl -X POST "http://localhost:8000/v1/content/generate" \
  -H "Content-Type: application/json" \
  -d '{"prompt":"Write about Python", "safety_level":"moderate"}' \
  -w "\nTime: %{time_total}s\n"
```

---

## 🚀 Future Enhancements

1. **User Authentication**
   - Switch from IP to user_id
   - Different limits for different user tiers
   - Usage tracking & analytics

2. **Advanced Caching**
   - Cache invalidation strategies
   - Partial matching (similar prompts)
   - Cache warming for popular requests

3. **Monitoring**
   - Track cache hit rate
   - Monitor rate limit violations
   - Adjust limits based on usage patterns

4. **Distributed Limits**
   - Sync across multiple backend instances
   - Account for cross-region usage
   - Implement DDoS protection

---

## ✅ Checklist

- [x] Sliding window rate limiter implemented
- [x] Response caching system implemented
- [x] Content generation endpoint updated
- [x] Rate limit headers in response
- [x] Redis integration tested
- [ ] User authentication integration
- [ ] Monitoring dashboard
- [ ] Usage analytics

---

**Status**: ✅ Ready for production with user authentication
