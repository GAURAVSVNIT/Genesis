# Genesis Database Tables Reference

Complete documentation of what each table stores and how it's used in the caching architecture.

---

## **Layer 1: Redis (Hot Cache)**

### `guest:{guest_id}`
**What stores**: List of guest conversation messages

```json
[
  {
    "role": "user|assistant",
    "content": "message text",
    "timestamp": "2025-12-20T19:10:22Z"
  },
  {
    "role": "assistant",
    "content": "response text",
    "timestamp": "2025-12-20T19:10:25Z"
  }
]
```

**Schema**:
- Type: List (Redis LPUSH/RPUSH)
- Key format: `guest:{guest_id}` where guest_id is UUID
- Value: JSON-serialized message objects
- TTL: 86400 seconds (24 hours)
- Max size: Unlimited (per Redis memory)

**How used**:
- **Speed**: Instant message retrieval for active guest conversations (< 1ms)
- **Temporary storage**: Guest messages before authentication
- **Fallback**: If Supabase is slow, data still available in Redis
- **Auto-cleanup**: Expires after 24 hours automatically
- **No persistence needed**: Non-critical for Redis to lose this data

**Typical lifecycle**:
```
Guest starts typing
  ↓ RPUSH guest:8b861dcd... message_json
Redis in-memory list grows
  ↓ (if Redis expires or too large)
Falls back to conversation_cache + message_cache
  ↓ User authenticates
Message data synced to main DB
  ↓ Can DELETE from Redis (optional, will auto-expire)
```

---

## **Layer 2: Supabase Cache Tables**

### **1. conversation_cache**

**Purpose**: Store conversation metadata for both guest and authenticated users before syncing to main DB.

**Schema**:

| Column | Type | Nullable | Notes |
|--------|------|----------|-------|
| `id` | UUID | NO | Primary key, unique conversation ID |
| `user_id` | UUID | NO | Guest ID or authenticated user ID |
| `session_id` | UUID | YES | Browser session tracker |
| `title` | TEXT | YES | Conversation name/title |
| `conversation_hash` | TEXT(64) | YES | SHA256(user_id) for deduplication |
| `message_count` | INTEGER | YES | How many messages in this conversation |
| `total_tokens` | INTEGER | YES | Cumulative tokens used |
| `platform` | TEXT | NO | **'guest' OR 'authenticated'** (CRITICAL for migration) |
| `tone` | TEXT | YES | 'formal', 'casual', 'technical', etc |
| `language` | TEXT | YES | 'english', 'spanish', etc |
| `migration_version` | TEXT | YES | Schema version, e.g., "1.0" |
| `created_at` | TIMESTAMP | NO | When created |
| `accessed_at` | TIMESTAMP | YES | Last access time |
| `expires_at` | TIMESTAMP | YES | When to auto-delete cache |

**How used**:

**Guest Phase** (platform='guest'):
- Store metadata while guest types
- One conversation_cache per guest session
- Messages linked via message_cache.conversation_id
- Platform='guest' identifies temporary data

**Migration Phase**:
```sql
UPDATE conversation_cache 
SET user_id = authenticated_user_id,
    platform = 'authenticated'
WHERE user_id = guest_id;
```

**Authenticated Phase** (platform='authenticated'):
- Query for user's conversations
- Acts as reference layer (faster than main conversations table)
- Still has all original guest messages

**Typical queries**:
```sql
-- Get guest conversations
SELECT * FROM conversation_cache 
WHERE platform='guest' AND created_at > NOW() - INTERVAL '24 hours';

-- Get user's authenticated conversations
SELECT * FROM conversation_cache 
WHERE user_id = 'auth-user-id' AND platform='authenticated';

-- Check if guest has active conversations
SELECT COUNT(*) FROM conversation_cache 
WHERE user_id = 'guest-id' AND platform='guest';
```

**Example data**:
```
{
  "id": "284385b5-0a8f-4cb5-bbe2-2a0c580aca28",
  "user_id": "8b861dcd-819b-43fa-b7e2-f5c35be4df7a",  // Guest ID
  "session_id": "session-12345",
  "title": "Guest ML Discussion",
  "conversation_hash": "abc123def456...",
  "message_count": 4,
  "total_tokens": 18,
  "platform": "guest",  // BEFORE migration
  "tone": "neutral",
  "language": "english",
  "created_at": "2025-12-20 19:10:15",
  "accessed_at": "2025-12-20 19:10:20"
}
```

After migration:
```
{
  // ... same fields ...
  "user_id": "32b892a6-00e4-47fc-94dd-78f2bf1d78d5",  // Authenticated ID
  "platform": "authenticated",  // AFTER migration
  // ... rest unchanged ...
}
```

---

### **2. message_cache**

**Purpose**: Store individual cached messages with deduplication hashing.

**Schema**:

| Column | Type | Nullable | Notes |
|--------|------|----------|-------|
| `id` | UUID | NO | Primary key |
| `conversation_id` | UUID | NO | FK to conversation_cache |
| `role` | TEXT | NO | 'user' or 'assistant' |
| `content` | TEXT | NO | Actual message text |
| `message_hash` | TEXT(32) | YES | MD5(content) for deduplication |
| `tokens` | INTEGER | YES | Token count for this message |
| `sequence` | INTEGER | YES | Order (0, 1, 2, 3...) |
| `is_edited` | BOOLEAN | NO | Default: false |
| `quality_score` | FLOAT | YES | 0-1, AI-assessed quality |
| `migration_version` | TEXT | YES | Schema version |
| `created_at` | TIMESTAMP | NO | When message created |
| `updated_at` | TIMESTAMP | NO | Last update time |

**How used**:

**Deduplication**:
- MD5 prevents storing same message twice
- If guest asks "What is AI?" twice → same MD5 hash
- Check hash before insert → skip duplicate

**Backup**:
- When Redis expires after 24 hours
- message_cache still has all guest messages
- Acts as fallback storage layer

**Migration**:
- Source of truth when syncing to main DB
- All fields copied to messages table

**Typical queries**:
```sql
-- Get all messages in a conversation
SELECT * FROM message_cache 
WHERE conversation_id = 'conv-id' 
ORDER BY sequence;

-- Check for duplicate message
SELECT id FROM message_cache 
WHERE message_hash = MD5('What is AI?');

-- Get high-quality messages
SELECT * FROM message_cache 
WHERE quality_score > 0.8 
ORDER BY sequence;
```

**Example data**:
```
{
  "id": "msg-uuid-1",
  "conversation_id": "284385b5-0a8f-4cb5-bbe2-2a0c580aca28",
  "role": "user",
  "content": "What is machine learning?",
  "message_hash": "abc123def456...",  // MD5 of content
  "tokens": 4,
  "sequence": 0,  // First message
  "is_edited": false,
  "quality_score": null,  // User message, no score yet
  "created_at": "2025-12-20 19:10:22"
},
{
  "id": "msg-uuid-2",
  "conversation_id": "284385b5-0a8f-4cb5-bbe2-2a0c580aca28",
  "role": "assistant",
  "content": "ML is a subset of AI where...",
  "message_hash": "xyz789abc123...",
  "tokens": 6,
  "sequence": 1,  // Second message
  "is_edited": false,
  "quality_score": 0.92,  // AI-generated, scored
  "created_at": "2025-12-20 19:10:25"
}
```

---

### **3. prompt_cache**

**Purpose**: Cache LLM prompts and responses to avoid redundant API calls.

**Schema**:

| Column | Type | Nullable | Notes |
|--------|------|----------|-------|
| `id` | UUID | NO | Primary key |
| `conversation_id` | UUID | NO | FK to conversation_cache |
| `prompt_hash` | TEXT(64) | NO | SHA256(system_prompt + user_input) |
| `prompt_content` | TEXT | NO | Full prompt sent to LLM |
| `response_hash` | TEXT(64) | YES | SHA256(response) |
| `response_content` | TEXT | YES | LLM's complete response |
| `model_used` | TEXT | NO | 'gpt-4', 'claude-3', 'gemini', etc |
| `temperature` | FLOAT | YES | 0-2 (randomness setting) |
| `tokens_used` | INTEGER | YES | Total tokens (prompt + response) |
| `cached_at` | TIMESTAMP | NO | When cached |
| `expires_at` | TIMESTAMP | YES | When cache invalidates |

**How used**:

**Cost Savings**:
- LLM API calls are expensive (~$0.01 per 1K tokens)
- If user asks same/similar question → return cached response
- Skip the API call entirely

**Speed**:
- Cached response instant (< 10ms)
- LLM call takes 1-5 seconds
- User perceives faster response

**A/B Testing**:
- Store different prompts/responses
- Compare which performs better
- Test variations of system prompt

**Typical queries**:
```sql
-- Check if prompt cached
SELECT response_content FROM prompt_cache 
WHERE prompt_hash = SHA256('prompt_text')
AND expires_at > NOW()
LIMIT 1;

-- Get cached responses for conversation
SELECT * FROM prompt_cache 
WHERE conversation_id = 'conv-id'
ORDER BY cached_at DESC;

-- Purge expired cache
DELETE FROM prompt_cache 
WHERE expires_at < NOW();
```

**Example data**:
```
{
  "id": "cache-uuid-1",
  "conversation_id": "284385b5-0a8f-4cb5-bbe2-2a0c580aca28",
  "prompt_hash": "abc123def456xyz...",  // SHA256 of exact prompt
  "prompt_content": "You are an AI assistant. User asked: 'Explain machine learning'",
  "response_hash": "789xyz123abc...",
  "response_content": "Machine learning is a subset of artificial intelligence...",
  "model_used": "gpt-4",
  "temperature": 0.7,
  "tokens_used": 287,  // 47 prompt + 240 response
  "cached_at": "2025-12-20 19:10:25",
  "expires_at": "2025-12-27 19:10:25"  // 7 days
}
```

---

### **4. cache_embeddings**

**Purpose**: Store vector embeddings for semantic search and similarity matching.

**Schema**:

| Column | Type | Nullable | Notes |
|--------|------|----------|-------|
| `id` | UUID | NO | Primary key |
| `conversation_id` | UUID | NO | FK to conversation_cache |
| `message_id` | UUID | NO | FK to message_cache |
| `content` | TEXT | NO | The text that was embedded |
| `embedding` | VECTOR(1536) | NO | Vector from sentence-transformers |
| `model_used` | TEXT | NO | 'all-MiniLM-L6-v2', 'sentence-bert', etc |
| `similarity_score` | FLOAT | YES | How similar to query (0-1) |
| `created_at` | TIMESTAMP | NO | When embedded |

**How used**:

**Semantic Search**:
- User asks: "Tell me about neural networks"
- Convert query to embedding (1536 float vector)
- Compare with cached embeddings using cosine similarity
- Find closest matches (e.g., messages about "deep learning", "networks")
- Return relevant context

**RAG (Retrieval-Augmented Generation)**:
- When answering user question
- Search embeddings for relevant past context
- Provide that context to LLM
- Improves answer quality with real conversation history

**Recommendations**:
- User starts new conversation
- Suggest related topics from embeddings
- "Based on your past discussions about X..."

**Clustering**:
- Group similar conversations
- Find conversation patterns
- Identify common topics

**Typical queries**:
```sql
-- Find similar messages
SELECT message_id, content, similarity_score 
FROM cache_embeddings 
WHERE conversation_id = 'conv-id'
ORDER BY similarity_score DESC
LIMIT 5;

-- Semantic search across all conversations
SELECT DISTINCT conversation_id, content
FROM cache_embeddings
WHERE embedding <-> query_embedding < 0.5  -- PostgreSQL cosine similarity
ORDER BY embedding <-> query_embedding
LIMIT 10;
```

**Example data**:
```
{
  "id": "embed-uuid-1",
  "conversation_id": "284385b5-0a8f-4cb5-bbe2-2a0c580aca28",
  "message_id": "msg-uuid-1",
  "content": "What is machine learning?",
  "embedding": [0.123, -0.456, 0.789, ..., 0.234],  // 1536 floats
  "model_used": "all-MiniLM-L6-v2",
  "similarity_score": null,  // Set during search
  "created_at": "2025-12-20 19:10:22"
}
```

---

### **5. cache_metrics**

**Purpose**: Track cache performance and usage statistics.

**Schema**:

| Column | Type | Nullable | Notes |
|--------|------|----------|-------|
| `id` | UUID | NO | Primary key |
| `conversation_id` | UUID | NO | FK to conversation_cache |
| `metric_type` | TEXT | NO | 'cache_hit', 'cache_miss', 'tokens_used', 'response_time' |
| `value` | FLOAT | NO | Numeric value of metric |
| `timestamp` | TIMESTAMP | NO | When recorded |

**How used**:

**Cache Hit Monitoring**:
- Cache hit: returned cached response (good)
- Cache miss: called LLM (not bad, just not cached)
- Goal: > 80% cache hit rate
- Calculate: hits / (hits + misses)

**Performance Tracking**:
- response_time: How long to respond to user
- Goal: < 200ms for cached, < 5s for LLM calls
- Identify slow queries

**Token Counting**:
- tokens_used: Count for billing
- Track per-user usage
- Enforce rate limits

**Cost Analysis**:
- tokens_used → multiply by price per token
- Calculate cost per user, per conversation
- Budget planning

**Typical queries**:
```sql
-- Cache hit rate
SELECT 
  COUNT(CASE WHEN metric_type = 'cache_hit' THEN 1 END) as hits,
  COUNT(CASE WHEN metric_type = 'cache_miss' THEN 1 END) as misses,
  COUNT(CASE WHEN metric_type = 'cache_hit' THEN 1 END) * 100.0 / 
    COUNT(*) as hit_rate
FROM cache_metrics
WHERE conversation_id = 'conv-id';

-- Average response time
SELECT AVG(value) as avg_response_ms
FROM cache_metrics
WHERE metric_type = 'response_time'
AND timestamp > NOW() - INTERVAL '1 day';

-- User token usage
SELECT SUM(value) as total_tokens
FROM cache_metrics
WHERE metric_type = 'tokens_used'
AND conversation_id IN (
  SELECT id FROM conversation_cache WHERE user_id = 'user-id'
);
```

**Example data**:
```
[
  {
    "id": "metric-1",
    "conversation_id": "284385b5-0a8f-4cb5-bbe2-2a0c580aca28",
    "metric_type": "cache_hit",
    "value": 1,  // Boolean as 1/0
    "timestamp": "2025-12-20 19:10:25"
  },
  {
    "id": "metric-2",
    "conversation_id": "284385b5-0a8f-4cb5-bbe2-2a0c580aca28",
    "metric_type": "response_time",
    "value": 45.23,  // milliseconds
    "timestamp": "2025-12-20 19:10:25"
  },
  {
    "id": "metric-3",
    "conversation_id": "284385b5-0a8f-4cb5-bbe2-2a0c580aca28",
    "metric_type": "tokens_used",
    "value": 287,  // tokens
    "timestamp": "2025-12-20 19:10:25"
  }
]
```

---

### **6. cache_migrations**

**Purpose**: Audit trail of all guest-to-user migrations.

**Schema**:

| Column | Type | Nullable | Notes |
|--------|------|----------|-------|
| `id` | UUID | NO | Primary key |
| `guest_user_id` | UUID | NO | Original guest ID |
| `authenticated_user_id` | UUID | NO | New authenticated user ID |
| `conversation_count` | INTEGER | NO | How many conversations migrated |
| `message_count` | INTEGER | NO | How many messages migrated |
| `platform_changed_from` | TEXT | NO | Always 'guest' |
| `platform_changed_to` | TEXT | NO | Always 'authenticated' |
| `migration_timestamp` | TIMESTAMP | NO | When migration happened |
| `status` | TEXT | NO | 'success', 'pending', 'failed' |
| `error_message` | TEXT | YES | If failed, what went wrong |

**How used**:

**Audit Trail**:
- Complete record of every migration
- When did user sign up?
- How many conversations converted?
- How many messages lost? (should be 0)

**Recovery**:
- If migration fails → retry using this record
- If data corrupted → replay the migration
- Idempotent → safe to run multiple times

**Analytics**:
- How many guests convert to authenticated users?
- Conversion rate: migrations / total guests
- Funnel analysis: guests → signups → paying users

**Debugging**:
- Did migration succeed?
- How many messages per guest on average?
- Typical conversation patterns

**Typical queries**:
```sql
-- Count successful migrations
SELECT COUNT(*) FROM cache_migrations 
WHERE status = 'success';

-- Find failed migrations
SELECT guest_user_id, error_message 
FROM cache_migrations 
WHERE status = 'failed'
ORDER BY migration_timestamp DESC;

-- Guest-to-authenticated conversion funnel
SELECT 
  COUNT(DISTINCT guest_user_id) as total_guests,
  COUNT(DISTINCT authenticated_user_id) as converted_to_auth,
  COUNT(DISTINCT authenticated_user_id) * 100.0 / COUNT(DISTINCT guest_user_id) as conversion_rate
FROM cache_migrations
WHERE status = 'success';

-- Average messages per guest
SELECT AVG(message_count) 
FROM cache_migrations;
```

**Example data**:
```
{
  "id": "migration-uuid-1",
  "guest_user_id": "8b861dcd-819b-43fa-b7e2-f5c35be4df7a",
  "authenticated_user_id": "32b892a6-00e4-47fc-94dd-78f2bf1d78d5",
  "conversation_count": 1,
  "message_count": 4,
  "platform_changed_from": "guest",
  "platform_changed_to": "authenticated",
  "migration_timestamp": "2025-12-20 19:10:22",
  "status": "success",
  "error_message": null
}
```

---

## **Layer 3: Main Database Tables (Source of Truth)**

### **1. users**

**Purpose**: Store authenticated user accounts.

**Schema**:

| Column | Type | Nullable | Notes |
|--------|------|----------|-------|
| `id` | UUID | NO | Primary key |
| `email` | TEXT | NO | UNIQUE, login identifier |
| `username` | TEXT | NO | UNIQUE, display name |
| `password_hash` | TEXT | NO | bcrypt/argon2 hashed |
| `subscription_status` | TEXT | NO | 'free', 'pro', 'enterprise' |
| `created_at` | TIMESTAMP | NO | Account creation date |
| `updated_at` | TIMESTAMP | NO | Last profile update |

**How used**:
- **Authentication**: Verify email + password on login
- **Authorization**: Check subscription tier for features
- **Billing**: Track subscription status
- **Foreign key anchor**: All other tables link to users.id

**Typical queries**:
```sql
-- User login
SELECT * FROM users WHERE email = 'user@example.com';

-- Count active users
SELECT COUNT(*) FROM users;

-- Get user info
SELECT * FROM users WHERE id = 'user-id';
```

**Example data**:
```
{
  "id": "32b892a6-00e4-47fc-94dd-78f2bf1d78d5",
  "email": "user@example.com",
  "username": "john_doe",
  "password_hash": "$argon2id$v=19$m=65536,t=3,p=4$...",
  "subscription_status": "pro",
  "created_at": "2025-12-20 19:10:22",
  "updated_at": "2025-12-20 19:10:22"
}
```

---

### **2. conversations**

**Purpose**: Main conversation records (source of truth).

**Schema**:

| Column | Type | Nullable | Notes |
|--------|------|----------|-------|
| `id` | UUID | NO | Primary key |
| `user_id` | UUID | NO | FK to users |
| `folder_id` | UUID | YES | FK to folders (organize) |
| `title` | TEXT | YES | Conversation name |
| `description` | TEXT | YES | Long description |
| `agent_type` | TEXT | NO | 'text-generation', 'code-assistant', 'research' |
| `model_used` | TEXT | NO | 'gpt-4', 'claude-3', 'gemini-pro' |
| `system_prompt` | TEXT | YES | LLM system message |
| `temperature` | FLOAT | YES | 0-2 (randomness) |
| `max_tokens` | INTEGER | YES | Output limit |
| `status` | TEXT | NO | 'active', 'archived', 'deleted' |
| `message_count` | INTEGER | NO | Total messages |
| `token_count` | INTEGER | NO | Total tokens |
| `is_public` | BOOLEAN | NO | Shareable with world? |
| `is_shared` | BOOLEAN | NO | Shared with team? |
| `tags` | TEXT ARRAY | YES | ['#ai', '#ml', '#research'] |
| `last_message_at` | TIMESTAMP | YES | When last message sent |
| `deleted_at` | TIMESTAMP | YES | Soft delete timestamp |
| `created_at` | TIMESTAMP | NO | When created |
| `updated_at` | TIMESTAMP | NO | Last update |

**How used**:
- **Session management**: Get user's conversation list
- **Settings storage**: temperature, model, system_prompt per conversation
- **Privacy**: is_public flag for sharing
- **Billing**: token_count tracks usage for cost
- **Organization**: folders and tags for UX
- **Soft delete**: deleted_at allows restore

**Typical queries**:
```sql
-- Get user's conversations
SELECT * FROM conversations 
WHERE user_id = 'user-id' AND deleted_at IS NULL
ORDER BY last_message_at DESC;

-- Get one conversation
SELECT * FROM conversations 
WHERE id = 'conv-id' AND user_id = 'user-id';

-- Count tokens for billing
SELECT SUM(token_count) 
FROM conversations 
WHERE user_id = 'user-id';

-- Get public conversations
SELECT * FROM conversations 
WHERE is_public = true;
```

**Example data**:
```
{
  "id": "5652c826-7037-49b5-af12-e9f3cf2c4b5c",
  "user_id": "32b892a6-00e4-47fc-94dd-78f2bf1d78d5",
  "folder_id": null,
  "title": "Guest ML Discussion",
  "description": "Migrated from guest session",
  "agent_type": "text-generation",
  "model_used": "gpt-4",
  "system_prompt": null,
  "temperature": 0.7,
  "max_tokens": null,
  "status": "active",
  "message_count": 5,
  "token_count": 23,
  "is_public": false,
  "is_shared": false,
  "tags": ["ml", "learning"],
  "last_message_at": "2025-12-20 19:10:24",
  "deleted_at": null,
  "created_at": "2025-12-20 19:10:23",
  "updated_at": "2025-12-20 19:10:24"
}
```

---

### **3. messages**

**Purpose**: Individual conversation messages (complete history).

**Schema**:

| Column | Type | Nullable | Notes |
|--------|------|----------|-------|
| `id` | UUID | NO | Primary key |
| `conversation_id` | UUID | NO | FK to conversations |
| `user_id` | UUID | NO | FK to users |
| `role` | TEXT | NO | 'user' or 'assistant' |
| `content` | TEXT | NO | The message text |
| `content_type` | TEXT | NO | 'text', 'markdown', 'code', 'json' |
| `message_index` | INTEGER | NO | Order (0, 1, 2...) |
| `tokens_used` | INTEGER | YES | Token count |
| `model_used` | TEXT | NO | Which model generated it |
| `user_rating` | INTEGER | YES | 1-5 star rating (null = no rating) |
| `is_edited` | BOOLEAN | NO | User edited after sending? |
| `is_regeneration` | BOOLEAN | NO | Was this regenerated? |
| `parent_message_id` | UUID | YES | For branching conversations |
| `flagged` | BOOLEAN | NO | Flagged for review? |
| `created_at` | TIMESTAMP | NO | When message created |
| `updated_at` | TIMESTAMP | NO | When last updated |

**How used**:
- **Display history**: Show full chat to user
- **Context**: Provide to LLM for next response
- **Continuity**: Guest messages migrated here
- **Feedback**: user_rating for model improvement
- **Regeneration**: Allow user to retry/branch conversations
- **Audit**: Complete record of everything said

**Typical queries**:
```sql
-- Get conversation history
SELECT * FROM messages 
WHERE conversation_id = 'conv-id'
ORDER BY message_index ASC;

-- Get rated messages (good feedback)
SELECT * FROM messages 
WHERE user_id = 'user-id' AND user_rating >= 4
ORDER BY created_at DESC;

-- Find flagged messages (quality issues)
SELECT * FROM messages 
WHERE flagged = true
ORDER BY created_at DESC;

-- Get regenerated messages (tried alternatives)
SELECT * FROM messages 
WHERE conversation_id = 'conv-id' AND is_regeneration = true;
```

**Example data**:
```
[
  {
    "id": "861a1572-1095-46b3-8417-05e52f09f1f4",
    "conversation_id": "5652c826-7037-49b5-af12-e9f3cf2c4b5c",
    "user_id": "32b892a6-00e4-47fc-94dd-78f2bf1d78d5",
    "role": "user",
    "content": "What is machine learning?",
    "content_type": "text",
    "message_index": 0,
    "tokens_used": 4,
    "model_used": null,
    "user_rating": null,
    "is_edited": false,
    "is_regeneration": false,
    "parent_message_id": null,
    "flagged": false,
    "created_at": "2025-12-20 19:10:22",
    "updated_at": "2025-12-20 19:10:22"
  },
  {
    "id": "785af92f-73a7-4d3d-95dc-39d457986ab3",
    "conversation_id": "5652c826-7037-49b5-af12-e9f3cf2c4b5c",
    "user_id": "32b892a6-00e4-47fc-94dd-78f2bf1d78d5",
    "role": "assistant",
    "content": "Machine learning is a subset of artificial intelligence where systems learn from data...",
    "content_type": "text",
    "message_index": 1,
    "tokens_used": 6,
    "model_used": "gpt-4",
    "user_rating": 5,  // User loved this
    "is_edited": false,
    "is_regeneration": false,
    "parent_message_id": null,
    "flagged": false,
    "created_at": "2025-12-20 19:10:25",
    "updated_at": "2025-12-20 19:10:25"
  }
]
```

---

### **4. generated_content**

**Purpose**: AI-generated responses with quality metrics and versioning.

**Schema**:

| Column | Type | Nullable | Notes |
|--------|------|----------|-------|
| `id` | UUID | NO | Primary key |
| `conversation_id` | UUID | NO | FK to conversations |
| `message_id` | UUID | NO | FK to messages |
| `content` | TEXT | NO | The generated text |
| `model_used` | TEXT | NO | Which model generated it |
| `prompt_used` | TEXT | NO | What prompt generated this |
| `quality_score` | FLOAT | YES | 0-1 rating |
| `is_approved` | BOOLEAN | NO | Human approved? |
| `is_published` | BOOLEAN | NO | Published to users? |
| `version` | INTEGER | NO | Which iteration? |
| `created_at` | TIMESTAMP | NO | When generated |

**How used**:
- **A/B testing**: Compare model outputs
- **Quality**: Track which models produce best content
- **Publishing**: Decide what to show users
- **Model improvement**: Train on approved content

**Typical queries**:
```sql
-- Get high-quality generated content
SELECT * FROM generated_content 
WHERE quality_score > 0.9 AND is_approved = true
ORDER BY created_at DESC;

-- Compare model performance
SELECT model_used, AVG(quality_score) as avg_score
FROM generated_content
GROUP BY model_used;
```

**Example data**:
```
{
  "id": "gen-uuid-1",
  "conversation_id": "5652c826-7037-49b5-af12-e9f3cf2c4b5c",
  "message_id": "785af92f-73a7-4d3d-95dc-39d457986ab3",
  "content": "Machine learning is...",
  "model_used": "gpt-4",
  "prompt_used": "You are an AI assistant. Explain this...",
  "quality_score": 0.92,
  "is_approved": true,
  "is_published": true,
  "version": 1,
  "created_at": "2025-12-20 19:10:25"
}
```

---

### **5. content_versions**

**Purpose**: Version history for A/B testing and rollback.

**Schema**:

| Column | Type | Nullable | Notes |
|--------|------|----------|-------|
| `id` | UUID | NO | Primary key |
| `generated_content_id` | UUID | NO | FK to generated_content |
| `version_number` | INTEGER | NO | v1, v2, v3... |
| `content` | TEXT | NO | The content at this version |
| `created_by` | TEXT | YES | Who created this version |
| `created_at` | TIMESTAMP | NO | When created |
| `is_active` | BOOLEAN | NO | Is this the current version? |

**How used**:
- **A/B testing**: "Version A or B converts better?"
- **Rollback**: "New version is bad, revert to old"
- **Audit**: "What changed from v1 to v2?"
- **Publishing**: Track which versions went live

**Typical queries**:
```sql
-- Get current active version
SELECT * FROM content_versions 
WHERE generated_content_id = 'gen-id' AND is_active = true;

-- Get all versions for comparison
SELECT * FROM content_versions 
WHERE generated_content_id = 'gen-id'
ORDER BY version_number;
```

**Example data**:
```
[
  {
    "id": "v1-uuid",
    "generated_content_id": "gen-uuid-1",
    "version_number": 1,
    "content": "Machine learning is...",
    "created_by": "system",
    "created_at": "2025-12-20 19:10:25",
    "is_active": false
  },
  {
    "id": "v2-uuid",
    "generated_content_id": "gen-uuid-1",
    "version_number": 2,
    "content": "Machine learning is an approach to AI where...",
    "created_by": "system",
    "created_at": "2025-12-20 19:10:26",
    "is_active": true  // Currently live
  }
]
```

---

### **6. message_feedback**

**Purpose**: User ratings and feedback on messages.

**Schema**:

| Column | Type | Nullable | Notes |
|--------|------|----------|-------|
| `id` | UUID | NO | Primary key |
| `message_id` | UUID | NO | FK to messages |
| `user_id` | UUID | NO | FK to users |
| `rating` | INTEGER | YES | 1-5 stars |
| `feedback_text` | TEXT | YES | User's comments |
| `helpful` | BOOLEAN | YES | Was helpful? |
| `accurate` | BOOLEAN | YES | Was accurate? |
| `created_at` | TIMESTAMP | NO | When given |

**How used**:
- **Model improvement**: Train better models from feedback
- **Quality assurance**: Identify bad responses
- **Metrics**: Calculate average message quality
- **User preferences**: Understand what users like

**Typical queries**:
```sql
-- Get all feedback for a message
SELECT * FROM message_feedback 
WHERE message_id = 'msg-id'
ORDER BY created_at DESC;

-- Get messages with good feedback
SELECT m.*, mf.rating FROM messages m
JOIN message_feedback mf ON m.id = mf.message_id
WHERE m.conversation_id = 'conv-id'
AND mf.rating >= 4;

-- Accuracy metrics
SELECT 
  COUNT(CASE WHEN accurate = true THEN 1 END) as accurate,
  COUNT(CASE WHEN accurate = false THEN 1 END) as inaccurate
FROM message_feedback;
```

**Example data**:
```
{
  "id": "fb-uuid-1",
  "message_id": "785af92f-73a7-4d3d-95dc-39d457986ab3",
  "user_id": "32b892a6-00e4-47fc-94dd-78f2bf1d78d5",
  "rating": 5,
  "feedback_text": "Very clear and accurate explanation!",
  "helpful": true,
  "accurate": true,
  "created_at": "2025-12-20 19:10:30"
}
```

---

### **7. rag_sources**

**Purpose**: Sources used in Retrieval-Augmented Generation.

**Schema**:

| Column | Type | Nullable | Notes |
|--------|------|----------|-------|
| `id` | UUID | NO | Primary key |
| `message_id` | UUID | NO | FK to messages (which message cited this) |
| `conversation_id` | UUID | NO | FK to conversations |
| `title` | TEXT | NO | Source title/heading |
| `url` | TEXT | NO | Source URL |
| `content_snippet` | TEXT | NO | Excerpt from source |
| `relevance_score` | FLOAT | YES | 0-1 (how relevant?) |
| `created_at` | TIMESTAMP | NO | When added |

**How used**:
- **Citations**: Show user where AI got information
- **Fact-checking**: Sources for verification
- **RAG**: Retrieve relevant sources for next response
- **Transparency**: "I got this from Wikipedia..."

**Typical queries**:
```sql
-- Get sources for a message
SELECT * FROM rag_sources 
WHERE message_id = 'msg-id'
ORDER BY relevance_score DESC;

-- Most cited sources
SELECT url, COUNT(*) as citation_count
FROM rag_sources
GROUP BY url
ORDER BY citation_count DESC;
```

**Example data**:
```
{
  "id": "source-uuid-1",
  "message_id": "785af92f-73a7-4d3d-95dc-39d457986ab3",
  "conversation_id": "5652c826-7037-49b5-af12-e9f3cf2c4b5c",
  "title": "Machine Learning - Wikipedia",
  "url": "https://en.wikipedia.org/wiki/Machine_learning",
  "content_snippet": "Machine learning (ML) is a field of study in artificial intelligence...",
  "relevance_score": 0.95,
  "created_at": "2025-12-20 19:10:25"
}
```

---

### **8. conversation_context**

**Purpose**: Per-conversation settings and metadata.

**Schema**:

| Column | Type | Nullable | Notes |
|--------|------|----------|-------|
| `id` | UUID | NO | Primary key |
| `conversation_id` | UUID | NO | FK to conversations |
| `setting_key` | TEXT | NO | 'tone', 'language', 'domain', 'style' |
| `setting_value` | TEXT | NO | 'formal', 'english', 'tech', 'technical' |
| `created_at` | TIMESTAMP | NO | When set |
| `updated_at` | TIMESTAMP | NO | When updated |

**How used**:
- **Customization**: Different settings per conversation
- **Context**: LLM needs to know "use technical language"
- **User preferences**: Remember how user likes to talk
- **Multi-language**: Support different languages

**Typical queries**:
```sql
-- Get conversation context
SELECT * FROM conversation_context 
WHERE conversation_id = 'conv-id';

-- Get user's language preference
SELECT setting_value FROM conversation_context
WHERE conversation_id = 'conv-id' 
AND setting_key = 'language';
```

**Example data**:
```
[
  {
    "id": "ctx-1",
    "conversation_id": "5652c826-7037-49b5-af12-e9f3cf2c4b5c",
    "setting_key": "tone",
    "setting_value": "formal",
    "created_at": "2025-12-20 19:10:23",
    "updated_at": "2025-12-20 19:10:23"
  },
  {
    "id": "ctx-2",
    "conversation_id": "5652c826-7037-49b5-af12-e9f3cf2c4b5c",
    "setting_key": "language",
    "setting_value": "english",
    "created_at": "2025-12-20 19:10:23",
    "updated_at": "2025-12-20 19:10:23"
  }
]
```

---

### **9. usage_metrics**

**Purpose**: User activity and billing metrics.

**Schema**:

| Column | Type | Nullable | Notes |
|--------|------|----------|-------|
| `id` | UUID | NO | Primary key |
| `user_id` | UUID | NO | FK to users |
| `metric_type` | TEXT | NO | 'tokens_used', 'conversations_created', 'api_calls' |
| `value` | INTEGER | NO | The value |
| `period` | TEXT | NO | 'day', 'week', 'month', 'year' |
| `timestamp` | TIMESTAMP | NO | When recorded |

**How used**:
- **Billing**: Count tokens for charges
- **Rate limiting**: Prevent abuse (max 1000 requests/hour)
- **Analytics**: "How many conversations per user?"
- **Dashboards**: Show usage to users
- **Alerts**: "You're near your limit"

**Typical queries**:
```sql
-- Get user's monthly token usage
SELECT SUM(value) 
FROM usage_metrics
WHERE user_id = 'user-id' 
AND metric_type = 'tokens_used'
AND period = 'month'
AND DATE_TRUNC('month', timestamp) = DATE_TRUNC('month', NOW());

-- Get total API calls this week
SELECT SUM(value)
FROM usage_metrics
WHERE user_id = 'user-id'
AND metric_type = 'api_calls'
AND period = 'week';

-- Top users by usage
SELECT user_id, SUM(value) as total
FROM usage_metrics
WHERE metric_type = 'tokens_used'
AND period = 'month'
GROUP BY user_id
ORDER BY total DESC
LIMIT 10;
```

**Example data**:
```
[
  {
    "id": "usage-1",
    "user_id": "32b892a6-00e4-47fc-94dd-78f2bf1d78d5",
    "metric_type": "tokens_used",
    "value": 1523,
    "period": "day",
    "timestamp": "2025-12-20 00:00:00"
  },
  {
    "id": "usage-2",
    "user_id": "32b892a6-00e4-47fc-94dd-78f2bf1d78d5",
    "metric_type": "conversations_created",
    "value": 5,
    "period": "day",
    "timestamp": "2025-12-20 00:00:00"
  }
]
```

---

### **10. activity_logs**

**Purpose**: Audit trail of all user actions.

**Schema**:

| Column | Type | Nullable | Notes |
|--------|------|----------|-------|
| `id` | UUID | NO | Primary key |
| `user_id` | UUID | NO | FK to users |
| `action` | TEXT | NO | 'conversation_created', 'message_sent', 'feedback_given' |
| `resource_type` | TEXT | NO | 'conversation', 'message', 'user' |
| `resource_id` | UUID | NO | Which resource |
| `timestamp` | TIMESTAMP | NO | When happened |

**How used**:
- **Security audit**: Track who did what when
- **Compliance**: Regulations require audit trails
- **Debugging**: "When did this conversation get created?"
- **Analytics**: "What's the average action rate?"
- **Fraud detection**: Unusual patterns

**Typical queries**:
```sql
-- Get user's activity for a day
SELECT * FROM activity_logs
WHERE user_id = 'user-id'
AND DATE(timestamp) = '2025-12-20'
ORDER BY timestamp DESC;

-- Find all conversations created by user
SELECT DISTINCT resource_id 
FROM activity_logs
WHERE user_id = 'user-id'
AND action = 'conversation_created'
ORDER BY timestamp DESC;

-- Audit trail for specific conversation
SELECT * FROM activity_logs
WHERE resource_id = 'conv-id'
ORDER BY timestamp DESC;
```

**Example data**:
```
[
  {
    "id": "log-1",
    "user_id": "32b892a6-00e4-47fc-94dd-78f2bf1d78d5",
    "action": "conversation_created",
    "resource_type": "conversation",
    "resource_id": "5652c826-7037-49b5-af12-e9f3cf2c4b5c",
    "timestamp": "2025-12-20 19:10:23"
  },
  {
    "id": "log-2",
    "user_id": "32b892a6-00e4-47fc-94dd-78f2bf1d78d5",
    "action": "message_sent",
    "resource_type": "message",
    "resource_id": "861a1572-1095-46b3-8417-05e52f09f1f4",
    "timestamp": "2025-12-20 19:10:22"
  }
]
```

---

## **Complete Data Flow Example**

### Guest Interaction → Authentication → Conversation Continuity

```
┌─────────────────────────────────────────────────────────────────────┐
│                        GUEST INTERACTION                              │
└─────────────────────────────────────────────────────────────────────┘

STEP 1: Guest opens browser
  Status: No user account
  Database state:
    users: [empty]
    conversations: [empty]
    messages: [empty]
    REDIS: [empty]

STEP 2: Guest types message 1: "What is machine learning?"
  Action: POST /chat/{guest_id}
  Stored in:
    REDIS: guest:8b861dcd... = [message_json]
    message_cache: 1 row (content="What is machine...", sequence=0)
    conversation_cache: 1 row (platform='guest')
  Database state:
    users: [empty]
    conversations: [empty]
    messages: [empty]
    conversation_cache: 1 row (platform='guest')
    message_cache: 1 row
    REDIS: 1 message with 24h TTL

STEP 3: Guest types messages 2, 3, 4
  Stored in:
    REDIS: guest:8b861dcd... = [msg1, msg2, msg3, msg4]
    message_cache: 4 rows (all backed up)
    conversation_cache: still 1 row (message_count updated to 4)
  Database state:
    conversation_cache: 1 row (platform='guest', message_count=4)
    message_cache: 4 rows
    REDIS: 4 messages with 24h TTL

┌─────────────────────────────────────────────────────────────────────┐
│                      AUTHENTICATION EVENT                             │
└─────────────────────────────────────────────────────────────────────┘

STEP 4: Guest signs up
  Email: user@example.com
  Password: (hashed)
  Action: POST /signup
  Created:
    users: 1 row (id=32b892a6..., email=user@example.com)
  Database state:
    users: 1 row (NEW)
    conversation_cache: still 1 row (platform='guest')
    message_cache: 4 rows (unchanged)

STEP 5: Migration Triggered (Atomic Transaction)
  Precondition: User exists with ID 32b892a6...
  Action: POST /migrate/8b861dcd...
  Update:
    conversation_cache:
      - user_id: 8b861dcd... → 32b892a6...
      - platform: 'guest' → 'authenticated'
  Log:
    cache_migrations: 1 row (guest_id → auth_id, 1 conversation, 4 messages)
  Database state:
    users: 1 row
    conversation_cache: 1 row (platform='authenticated', user_id=32b892a6...)
    message_cache: 4 rows (unchanged, backup)
    cache_migrations: 1 row (success)

STEP 6: Sync to Main DB
  Action: Internal sync (triggered by migration)
  Create:
    conversations: 1 row (from conversation_cache)
    messages: 4 rows (from message_cache)
    activity_logs: 2 rows (conversation_created, messages_created)
  Database state:
    users: 1 row
    conversations: 1 row (migrated from cache)
    messages: 4 rows (from cache)
    conversation_cache: 1 row (reference layer)
    message_cache: 4 rows (backup)
    activity_logs: 2+ rows

┌─────────────────────────────────────────────────────────────────────┐
│                    AUTHENTICATED USER CONTINUES                       │
└─────────────────────────────────────────────────────────────────────┘

STEP 7: User adds new message
  Message: "Tell me about deep learning"
  Action: POST /conversations/{conv_id}/messages
  Created:
    messages: 1 NEW row (message_index=4, directly in main DB)
    activity_logs: 1 row (message_sent)
  Updated:
    conversations: message_count=5, token_count+=5
  Database state:
    conversations: 1 row (message_count=5 ✅ updated)
    messages: 5 rows (4 original + 1 new)
    activity_logs: 3+ rows

STEP 8: User requests conversation history
  Action: GET /conversations/{conv_id}/messages
  Retrieved from: messages table (main DB)
  Result: All 5 messages in order
    1. user: "What is machine learning?"
    2. assistant: "ML is..."
    3. user: "Can you explain neural networks?"
    4. assistant: "Neural networks are..."
    5. user: "Tell me about deep learning"
  Database state: [unchanged]

STEP 9: User asks related question
  Message: "Compare supervised and unsupervised learning"
  Check: Does prompt_cache have similar cached response?
    Query: SELECT response FROM prompt_cache WHERE prompt_hash = SHA256(...)
    Result: Cache HIT (similar question cached)
    Action: Return cached response instantly
  If MISS:
    Call LLM → Get response → Store in prompt_cache
  Database state:
    prompt_cache: +1 row (cached response)
    cache_metrics: +1 row (cache_hit)

FINAL STATE AFTER FULL INTERACTION:
  users: 1 row (authenticated user)
  conversations: 1 row (migrated + active)
  messages: 6 rows (4 guest + 2 new authenticated)
  
  REDIS:
    guest:8b861dcd...: will auto-expire in ~23.8 hours
    
  conversation_cache: 1 row (backup reference)
  message_cache: 4 rows (backup of original guest messages)
  prompt_cache: 1+ rows (cached responses)
  cache_embeddings: 6+ rows (vector embeddings)
  cache_metrics: 5+ rows (performance data)
  cache_migrations: 1 row (audit trail)
  
  activity_logs: 4+ rows (account creation, migration, message sends)
  usage_metrics: 2+ rows (tokens used, conversations created)
```

---

## **Quick Lookup: Which Table for What?**

| Need to... | Use this table | Environment |
|-----------|---------|---------|
| Store guest message | `message_cache` + Redis | Cache layer |
| Find conversation history | `messages` | Main DB |
| Get conversation metadata | `conversation_cache` | Cache layer |
| Check if user authenticated | `users` | Main DB |
| Find similar messages | `cache_embeddings` | Cache layer |
| Reuse LLM response | `prompt_cache` | Cache layer |
| Track message quality | `message_feedback` + `generated_content` | Main DB |
| Audit who did what | `activity_logs` + `cache_migrations` | Both |
| Check token usage/billing | `usage_metrics` | Main DB |
| Find sources for response | `rag_sources` | Main DB |
| Manage message versions | `content_versions` | Main DB |
| Check cache performance | `cache_metrics` | Cache layer |
| Migrate guest to user | `conversation_cache` + `message_cache` | Cache layer |

---

## **Key Design Principles**

✅ **Three-Layer Architecture**
- Layer 1 (Redis): Ultra-fast, temporary
- Layer 2 (Cache tables): Persistent backup, reference
- Layer 3 (Main DB): Authoritative source of truth

✅ **Zero Data Loss**
- Redis expires → data still in cache tables
- Cache tables → synced to main DB
- Main DB → permanent audit trail

✅ **Atomic Migrations**
- Guest → authenticated: all-or-nothing transaction
- No partial states
- Rollback on failure

✅ **Performance Optimized**
- Hot cache for active conversations (< 1ms)
- Cold cache for backup (10-50ms)
- Embeddings for semantic search
- Prompt caching for cost savings

✅ **Complete Audit Trail**
- cache_migrations: guest→auth conversions
- activity_logs: user actions
- message_feedback: quality tracking
- content_versions: change history
