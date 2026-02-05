# Genesis Context & Checkpoint Storage in Supabase

## Database Tables Overview

### 1. `conversation_contexts` Table
Stores the full conversation state and context for each user-conversation pair.

**Fields:**
```
- id: UUID (primary key)
- user_id: VARCHAR(255) - "guest" or authenticated user UUID
- conversation_id: VARCHAR(255) - unique conversation UUID
- messages_context: JSON - full message history with metadata
- chat_context: TEXT - formatted conversation for AI
- blog_context: TEXT - current blog content being worked on
- full_context: TEXT - enriched context for generation
- message_count: INTEGER - number of messages in conversation
- last_updated_at: TIMESTAMP - when context was last updated
- created_at: TIMESTAMP - when context was created
- updated_at: TIMESTAMP - auto-updated on each change
```

### 2. `blog_checkpoints` Table
Stores specific versions/snapshots of blog content.

**Fields:**
```
- id: UUID (primary key)
- user_id: UUID - user who created checkpoint
- conversation_id: UUID - associated conversation
- title: VARCHAR(255) - checkpoint title
- content: TEXT - full blog content at this version
- description: TEXT - optional description
- context_snapshot: JSON - message context at this checkpoint
- chat_messages_snapshot: JSON - chat history snapshot
- version_number: INTEGER - version number (1, 2, 3, etc.)
- tone: VARCHAR(255) - blog tone setting
- length: VARCHAR(255) - blog length setting
- is_active: BOOLEAN - whether this is the active version
- created_at: TIMESTAMP
- updated_at: TIMESTAMP
```

---

## Data Flow: SAVE → STORE → RESTORE

### 1️⃣ SAVE FLOW (Frontend → Backend → Database)

**Frontend sends POST to `/v1/context/save`:**
```json
{
  "conversation_id": "948cffb6-7a23-4f3f-a7e7-f38a5f8f90f8",
  "user_id": "guest",
  "messages": [
    {
      "id": "ee305e62-23cb-4f65-9412-2440c8eea806",
      "role": "user",
      "content": "hello",
      "type": "chat",
      "timestamp": "2025-12-24T17:22:11.742Z",
      "tone": "informative",
      "length": "medium"
    }
  ],
  "chat_messages": [
    {
      "role": "user",
      "content": "hello"
    },
    {
      "role": "assistant",
      "content": "Hello! How can I help..."
    }
  ],
  "current_blog_content": "## Blog Title\n\nBlog content here..."
}
```

**Backend processes (in `api/v1/context.py`):**
1. Receives the SaveContextRequest
2. Checks if ConversationContext exists for (conversation_id + user_id)
3. If exists: UPDATE the record
4. If new: CREATE new ConversationContext record
5. Stores data:
   - `messages_context` ← JSON of all message objects
   - `chat_context` ← Formatted as "User: ... \nAssistant: ... \n"
   - `blog_context` ← Raw blog content
   - `message_count` ← Total message count
   - `last_updated_at` ← Current timestamp

**Database receives and stores:**
```sql
INSERT INTO conversation_contexts 
(user_id, conversation_id, messages_context, chat_context, blog_context, message_count, last_updated_at, created_at, id)
VALUES 
('guest', '948cffb6-7a23-4f3f-a7e7-f38a5f8f90f8', {...JSON...}, 'User: hello\nAssistant: ...', '## Blog...', 2, NOW(), NOW(), UUID)
```

---

### 2️⃣ RESTORE FLOW (Database → Backend → Frontend)

**Frontend requests GET `/v1/context/load/{conversation_id}?user_id=guest`**

**Backend queries Supabase:**
```python
existing_context = db.query(ConversationContext).filter(
    ConversationContext.conversation_id == "948cffb6-7a23-4f3f-a7e7-f38a5f8f90f8",
    ConversationContext.user_id == "guest"
).first()
```

**Database returns the stored record:**
```
Row from conversation_contexts:
- id: e66bc210-978b-4c1c-82c4-60cb393ee5c7
- user_id: guest
- conversation_id: 948cffb6-7a23-4f3f-a7e7-f38a5f8f90f8
- messages_context: {...full JSON...}
- chat_context: "User: hello\nAssistant: Hello!..."
- blog_context: "## The Majestic Himalayas..."
- message_count: 6
- last_updated_at: 2025-12-24 17:23:31
```

**Backend returns to frontend as ContextResponse:**
```json
{
  "user_id": "guest",
  "conversation_id": "948cffb6-7a23-4f3f-a7e7-f38a5f8f90f8",
  "messages": [
    {
      "id": "ee305e62-23cb-4f65-9412-2440c8eea806",
      "role": "user",
      "content": "hello",
      "type": "chat",
      "timestamp": "2025-12-24T17:22:11.742Z"
    }
  ],
  "chat_context": "User: hello\nAssistant: Hello!...",
  "blog_context": "## The Majestic Himalayas...",
  "message_count": 6,
  "last_updated_at": "2025-12-24T17:23:31.211486"
}
```

**Frontend updates UI:**
1. Renders chat history from `messages`
2. Renders blog content from `blog_context`
3. Continues conversation from where it left off
4. Shows message_count for reference

---

### 3️⃣ CHECKPOINT FLOW (Save specific version)

**Frontend sends POST to `/v1/checkpoints/create`:**
```json
{
  "conversation_id": "948cffb6-7a23-4f3f-a7e7-f38a5f8f90f8",
  "user_id": "guest",
  "title": "First Draft - Himalayas",
  "content": "## The Majestic Himalayas...",
  "description": "Initial draft with introduction",
  "tone": "informative",
  "length": "medium"
}
```

**Backend creates new record in blog_checkpoints:**
```sql
INSERT INTO blog_checkpoints 
(id, user_id, conversation_id, version_number, title, content, tone, length, is_active, created_at)
VALUES
(UUID, 'guest', '948cffb6-7a23-4f3f-a7e7-f38a5f8f90f8', 1, 'First Draft - Himalayas', '...', 'informative', 'medium', true, NOW())
```

**Frontend requests GET `/v1/checkpoints/list/{conversation_id}?user_id=guest`:**
Returns list of all versions:
```json
[
  {
    "id": "checkpoint-uuid-1",
    "version_number": 2,
    "title": "Second Draft",
    "created_at": "2025-12-24T17:25:00Z",
    "is_active": true
  },
  {
    "id": "checkpoint-uuid-2",
    "version_number": 1,
    "title": "First Draft",
    "created_at": "2025-12-24T17:23:00Z",
    "is_active": false
  }
]
```

---

## Real Data Example from Supabase

### Stored messages_context JSON:
```json
{
  "user_id": "guest",
  "conversation_id": "948cffb6-7a23-4f3f-a7e7-f38a5f8f90f8",
  "messages": [
    {
      "id": "ee305e62-23cb-4f65-9412-2440c8eea806",
      "role": "user",
      "content": "hello",
      "type": "chat",
      "timestamp": "2025-12-24T17:22:11.742Z",
      "tone": "informative",
      "length": "medium"
    },
    {
      "id": "1c732474-8e7f-4902-b098-b8cb45770005",
      "role": "assistant",
      "content": "Hello! How can I help you today?...",
      "type": "chat",
      "timestamp": "2025-12-24T17:22:12.414Z"
    },
    {
      "id": "2f312937-7df8-4d52-82b6-cb55660aa898",
      "role": "user",
      "content": "papaya",
      "type": "chat",
      "timestamp": "2025-12-24T17:22:16.729Z",
      "tone": "informative",
      "length": "medium"
    }
  ],
  "chat_messages": [...],
  "current_blog": "## The Majestic Himalayas..."
}
```

### Stored chat_context TEXT:
```
User: hello
Assistant: Hello! How can I help you today? Are you looking for information, creative content, or something else?

User: papaya
Assistant: Okay, let's talk about papayas! Here's some information...

**What is a Papaya?**
- Botanical Background: The papaya (Carica papaya) is a tropical fruit...
```

### Stored blog_context TEXT:
```markdown
## The Majestic Himalayas: A Journey to the Roof of the World

The Himalayas. Just the name evokes images of towering, snow-capped peaks...

**A Geological Giant: The Birth of a Mountain Range**
The Himalayas are relatively young, geologically speaking...
```

---

## Key Points

✅ **All conversation data is stored in ONE context record** per conversation  
✅ **Messages are stored as JSON** for easy parsing and querying  
✅ **Chat context is a formatted text version** for AI context window  
✅ **Blog content is stored separately** for easy rendering  
✅ **Checkpoints save snapshots** for version control  
✅ **Guest users use string "guest" as user_id** (not UUID)  
✅ **Automatic timestamps** track creation and updates  
✅ **last_updated_at** shows when context was last modified  

---

## Backend Code References

- **Save Context:** `api/v1/context.py` → `save_context()` (Line 116)
- **Load Context:** `api/v1/context.py` → `load_context()` (Line 182)
- **List Checkpoints:** `api/v1/context.py` → `list_checkpoints()` (Line 269)
- **Create Checkpoint:** `api/v1/context.py` → `create_checkpoint()` (Line 207)
- **Models:** `database/models/conversation.py` → `ConversationContext`, `BlogCheckpoint`
