# Frontend Checkpoint Restoration - Visual Request Flow

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                        GENESIS FRONTEND                             │
│                     (Next.js/React/TypeScript)                      │
│                                                                     │
│  [Checkpoint List UI]  ────→  [Restore Button]  ───→  [Editor]    │
│                                                                     │
│         ↓                            ↓                    ↑        │
│  listCheckpoints()         restoreCheckpoint()      loadContext()  │
└─────────────────────────────────────────────────────────────────────┘
         │                            │                      │
         │ GET /v1/checkpoints/list   │ POST /restore        │ GET /load
         │                            │                      │
         ▼                            ▼                      ▼
┌─────────────────────────────────────────────────────────────────────┐
│                        GENESIS BACKEND                              │
│                     (FastAPI/Python/SQLAlchemy)                    │
│                                                                     │
│  [context.py API Router]                                            │
│                                                                     │
│  GET /v1/checkpoints/list/{id}                                      │
│     ↓                                                                │
│  Query: SELECT * FROM blog_checkpoints WHERE conversation_id = id   │
│     ↓                                                                │
│  Return: [ {v1, inactive}, {v2, active} ]                          │
│                                                                     │
│  POST /v1/checkpoints/{id}/restore                                  │
│     ↓                                                                │
│  UPDATE blog_checkpoints SET is_active=false WHERE id != checkpoint │
│  UPDATE blog_checkpoints SET is_active=true WHERE id = checkpoint   │
│  UPDATE conversation_contexts SET ... FROM checkpoint.context_snap  │
│     ↓                                                                │
│  Return: { status: "restored", version: 1, content: "..." }        │
│                                                                     │
│  GET /v1/context/load/{conversation_id}                             │
│     ↓                                                                │
│  Query: SELECT * FROM conversation_contexts WHERE id = conversation │
│     ↓                                                                │
│  Return: { messages, blog_content, metadata }                       │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
         │                            │                      │
         │ [checkpoint list]         │ [restore confirm]     │ [context]
         │                            │                      │
         └────────────────────────────┴──────────────────────┘
                              ↓
                      [Update Frontend UI]
                      [Show restored content]
```

---

## Detailed Request Sequence

### 1️⃣ LIST CHECKPOINTS

```
FRONTEND REQUEST:
┌──────────────────────────────────────────────────────────────┐
│ GET /v1/checkpoints/list/2c1a70a1?user_id=guest             │
│                                                              │
│ Headers:                                                     │
│ - Content-Type: application/json                           │
│                                                              │
│ No request body needed                                      │
└──────────────────────────────────────────────────────────────┘

BACKEND PROCESSING:
┌──────────────────────────────────────────────────────────────┐
│ 1. Parse parameters: conversation_id, user_id               │
│ 2. Validate user authorization (implicit for guest)         │
│ 3. Query database:                                          │
│    SELECT * FROM blog_checkpoints                          │
│    WHERE conversation_id = '2c1a70a1'                      │
│    AND user_id = 'guest'                                   │
│    ORDER BY version_number DESC                            │
│ 4. Format response with CheckpointResponse objects          │
└──────────────────────────────────────────────────────────────┘

BACKEND RESPONSE:
┌──────────────────────────────────────────────────────────────┐
│ Status: 200 OK                                              │
│ Body: [                                                     │
│   {                                                         │
│     "id": "546e6566-ab83-47fa-a285-aa876ad5cb7b",         │
│     "version_number": 2,                                   │
│     "title": "Python Guide - Version 2",                   │
│     "description": "Added Advanced Topics section",        │
│     "created_at": "2025-12-24T17:45:16.773999",           │
│     "is_active": true                                      │
│   },                                                        │
│   {                                                         │
│     "id": "f59b0c3b-539d-4530-94d6-a4389ba7ab56",         │
│     "version_number": 1,                                   │
│     "title": "Python Guide - Version 1",                   │
│     "description": "Initial comprehensive guide",          │
│     "created_at": "2025-12-24T17:45:11.866840",           │
│     "is_active": false                                     │
│   }                                                         │
│ ]                                                           │
└──────────────────────────────────────────────────────────────┘

FRONTEND UPDATES UI:
┌──────────────────────────────────────────────────────────────┐
│ ┌─ Version History ────────────────────────────────────┐   │
│ │ v2: Python Guide - Version 2 [ACTIVE]               │   │
│ │     Added Advanced Topics section                    │   │
│ │     [Restore] [Delete]                              │   │
│ │                                                      │   │
│ │ v1: Python Guide - Version 1 [INACTIVE]             │   │
│ │     Initial comprehensive guide                     │   │
│ │     [Restore] [Delete]                 ← User clicks│   │
│ └──────────────────────────────────────────────────────┘   │
└──────────────────────────────────────────────────────────────┘
```

---

### 2️⃣ RESTORE CHECKPOINT

```
FRONTEND REQUEST (When user clicks Restore on v1):
┌──────────────────────────────────────────────────────────────┐
│ POST /v1/checkpoints/f59b0c3b.../restore                    │
│      ?user_id=guest&conversation_id=2c1a70a1                │
│                                                              │
│ Headers:                                                     │
│ - Content-Type: application/json                           │
│                                                              │
│ Body:                                                       │
│ (empty - all info in URL params)                            │
└──────────────────────────────────────────────────────────────┘

BACKEND PROCESSING:
┌──────────────────────────────────────────────────────────────┐
│ STEP 1: Fetch the checkpoint to restore                     │
│   SELECT * FROM blog_checkpoints                            │
│   WHERE id = 'f59b0c3b...'                                 │
│   AND user_id = 'guest'                                    │
│   ↓ Found: Python Guide V1, context_snapshot = {...}       │
│                                                              │
│ STEP 2: Deactivate all other checkpoints                   │
│   UPDATE blog_checkpoints SET is_active = false             │
│   WHERE conversation_id = '2c1a70a1'                       │
│   ↓ 1 row updated (v2 is now inactive)                      │
│                                                              │
│ STEP 3: Activate this checkpoint                           │
│   UPDATE blog_checkpoints SET is_active = true              │
│   WHERE id = 'f59b0c3b...'                                 │
│   ↓ 1 row updated (v1 is now active)                        │
│                                                              │
│ STEP 4: Restore context snapshot to conversation_contexts   │
│   SELECT * FROM conversation_contexts                       │
│   WHERE conversation_id = '2c1a70a1'                       │
│   AND user_id = 'guest'                                    │
│   ↓ Found existing record                                   │
│                                                              │
│   UPDATE conversation_contexts SET                          │
│     messages_context = checkpoint.context_snapshot,         │
│     chat_context = formatted_messages,                      │
│     blog_context = checkpoint.content,                      │
│     message_count = checkpoint.message_count,               │
│     last_updated_at = NOW()                                 │
│   WHERE id = existing_context.id                            │
│   ↓ Context restored to Version 1 state                     │
│                                                              │
│ STEP 5: Prepare response                                    │
│   Format CheckpointResponse with restored data              │
└──────────────────────────────────────────────────────────────┘

BACKEND RESPONSE:
┌──────────────────────────────────────────────────────────────┐
│ Status: 200 OK                                              │
│ Body: {                                                     │
│   "status": "restored",                                     │
│   "checkpoint_id": "f59b0c3b-539d-4530-94d6-a4389ba7ab56", │
│   "version": 1,                                             │
│   "title": "Python Guide - Version 1",                      │
│   "content": "# Python Programming Guide\n\n##...",         │
│   "description": "Initial comprehensive guide",            │
│   "tone": "informative",                                    │
│   "length": "long",                                         │
│   "restored_at": "2025-12-24T17:45:20.123456"             │
│ }                                                           │
└──────────────────────────────────────────────────────────────┘

FRONTEND UPDATES UI:
┌──────────────────────────────────────────────────────────────┐
│ [Toast] "Checkpoint restored: Version 1"                    │
│                                                              │
│ ┌─ Version History ────────────────────────────────────┐   │
│ │ v2: Python Guide - Version 2 [INACTIVE]              │   │
│ │     Added Advanced Topics section                    │   │
│ │     [Restore] [Delete]                              │   │
│ │                                                      │   │
│ │ v1: Python Guide - Version 1 [ACTIVE] ← Changed!    │   │
│ │     Initial comprehensive guide                     │   │
│ │     [Delete]                                         │   │
│ └──────────────────────────────────────────────────────┘   │
│                                                              │
│ (Still loading context from step 3... see below)           │
└──────────────────────────────────────────────────────────────┘
```

---

### 3️⃣ LOAD RESTORED CONTEXT

```
FRONTEND REQUEST (Automatically after restore):
┌──────────────────────────────────────────────────────────────┐
│ GET /v1/context/load/2c1a70a1?user_id=guest                │
│                                                              │
│ Headers:                                                     │
│ - Content-Type: application/json                           │
│                                                              │
│ No body needed                                              │
└──────────────────────────────────────────────────────────────┘

BACKEND PROCESSING:
┌──────────────────────────────────────────────────────────────┐
│ 1. Parse: conversation_id = '2c1a70a1', user_id = 'guest'  │
│ 2. Query database:                                          │
│    SELECT * FROM conversation_contexts                     │
│    WHERE conversation_id = '2c1a70a1'                      │
│    AND user_id = 'guest'                                  │
│ 3. Found the context that was updated by restore step      │
│ 4. Deserialize JSON: context.messages_context = [...]      │
│ 5. Format response with all context data                   │
└──────────────────────────────────────────────────────────────┘

BACKEND RESPONSE:
┌──────────────────────────────────────────────────────────────┐
│ Status: 200 OK                                              │
│ Body: {                                                     │
│   "message_count": 4,                                       │
│   "messages": [                                             │
│     {                                                       │
│       "id": "msg-1",                                        │
│       "role": "user",                                       │
│       "content": "Write blog about Python",                 │
│       "type": "chat",                                       │
│       "timestamp": "1703... (v1 timestamp)",               │
│       "tone": "informative"                                 │
│     },                                                      │
│     {                                                       │
│       "id": "msg-2",                                        │
│       "role": "assistant",                                  │
│       "content": "Here's comprehensive guide...",           │
│       "type": "chat",                                       │
│       "timestamp": "1703..."                                │
│     },                                                      │
│     {                                                       │
│       "id": "msg-3",                                        │
│       "role": "user",                                       │
│       "content": "Make it more detailed",                   │
│       "timestamp": "1703..."                                │
│     },                                                      │
│     {                                                       │
│       "id": "msg-4",                                        │
│       "role": "assistant",                                  │
│       "content": "I've expanded the guide...",              │
│       "timestamp": "1703..."                                │
│     }                                                       │
│   ],                                                        │
│   "current_blog_content": "# Python Programming...",        │
│   "chat_messages": [ { role, content }, ... ]              │
│ }                                                           │
└──────────────────────────────────────────────────────────────┘

FRONTEND UPDATES UI:
┌──────────────────────────────────────────────────────────────┐
│                                                              │
│ ┌───────────────────┐    ┌──────────────────────────────┐  │
│ │   Chat History    │    │   Blog Editor                │  │
│ ├───────────────────┤    ├──────────────────────────────┤  │
│ │ User:             │    │ # Python Programming Guide   │  │
│ │ Write blog about  │    │                              │  │
│ │ Python            │    │ ## Introduction              │  │
│ │                   │    │ Python is a versatile...     │  │
│ │ Assistant:        │    │                              │  │
│ │ Here's comp-      │    │ ## Key Features              │  │
│ │ rehensive guide   │    │ - Easy to learn syntax       │  │
│ │                   │    │ - Powerful libraries         │  │
│ │ User:             │    │ - Great for everyone         │  │
│ │ Make it more      │    │                              │  │
│ │ detailed          │    │ ## Getting Started           │  │
│ │                   │    │ Install Python and start!    │  │
│ │ Assistant:        │    │                              │  │
│ │ I've expanded...  │    │ [NO Advanced Topics ✓]       │  │
│ │                   │    │ (Correctly showing V1)       │  │
│ └───────────────────┘    └──────────────────────────────┘  │
│                                                              │
│ Status: ✓ Restored to Version 1                             │
└──────────────────────────────────────────────────────────────┘
```

---

## Complete Checkpoint Object Structure

### Database Schema

```sql
CREATE TABLE blog_checkpoints (
    id UUID PRIMARY KEY,
    conversation_id VARCHAR(255),          -- Foreign key to conversation
    user_id VARCHAR(255),                   -- "guest" for guest users
    title VARCHAR(255),                     -- "Python Guide - Version 1"
    content TEXT,                           -- Full blog content at checkpoint time
    description TEXT,                       -- "Initial version" or "Added topics"
    version_number INTEGER,                 -- 1, 2, 3, etc.
    tone VARCHAR(50),                       -- "informative", "creative", etc.
    length VARCHAR(50),                     -- "short", "medium", "long"
    context_snapshot JSONB,                 -- Full context at checkpoint time
    chat_messages_snapshot JSONB,           -- Chat history at checkpoint time
    is_active BOOLEAN DEFAULT false,        -- Only one per conversation is true
    created_at TIMESTAMP,                   -- When checkpoint created
    updated_at TIMESTAMP,                   -- Last modified
    FOREIGN KEY (conversation_id) REFERENCES conversation_contexts(conversation_id),
    FOREIGN KEY (user_id) REFERENCES conversation_contexts(user_id)
);
```

### Response Object (Python Pydantic Model)

```python
class CheckpointResponse(BaseModel):
    id: str                          # UUID as string
    title: str                       # "Python Guide - Version 1"
    content: str                     # Full markdown content
    description: Optional[str]       # "Initial version"
    version_number: int              # 1, 2, 3...
    created_at: str                  # ISO timestamp
    is_active: bool                  # true/false
    tone: Optional[str]              # "informative"
    length: Optional[str]            # "long"
```

---

## API Response Times (from Test)

```
Action                          Time      Database Queries
────────────────────────────────────────────────────────────
1. Save context                 ~200ms    1 INSERT + 1 UPDATE
2. Create checkpoint v1         ~150ms    1 INSERT
3. Update & save context        ~180ms    1 UPDATE
4. Create checkpoint v2         ~140ms    1 INSERT
5. List checkpoints             ~120ms    1 SELECT ORDER BY
6. Restore checkpoint           ~160ms    2-3 UPDATE statements
7. Load restored context        ~140ms    1 SELECT
────────────────────────────────────────────────────────────
Total restoration flow          ~880ms    ~10-12 database ops
```

---

## Error Handling

### Common Errors

```typescript
// Error: Checkpoint not found
{
    "detail": "Checkpoint not found"
}
// Status: 404 Not Found

// Error: Database unavailable
// (Graceful degradation)
listCheckpoints() → returns []  // Empty list
restoreCheckpoint() → still returns 200, but restoration limited

// Error: Unauthorized (different user_id)
// The user_id parameter prevents cross-user restoration
// If user_id doesn't match, checkpoint won't be found
```

---

## Summary: The Complete Flow

```
User Interface          API Request             Backend Action          Database
──────────────────────────────────────────────────────────────────────────────
[Show checkpoints]  →  GET /list          →  Query checkpoints    →  SELECT
                      (conversation_id)

                                            ↓
[User clicks         
 "Restore v1"]     →  POST /restore       →  Deactivate v2        →  UPDATE
                      (checkpoint_id)        Activate v1            →  UPDATE
                                            Restore context        →  UPDATE

                      GET /load            →  Get context           →  SELECT
[Editor refreshes] ←                          with restored data

[UI shows v1       ←
 content]
```

This is how time-travel blog editing works in Genesis!
