# Frontend Checkpoint Restoration Flow

## How Frontend Requests to Restore a Checkpoint

### Quick Summary
The frontend uses a **two-part restore process**:
1. **POST** to `/v1/checkpoints/{checkpoint_id}/restore` - Mark checkpoint as active
2. **GET** from `/v1/context/load/{conversation_id}` - Load the restored context

---

## Complete Request Flow

### Step 1: Frontend Lists Available Checkpoints

**Frontend Code:**
```typescript
// apps/frontend/lib/api/context.ts
export async function listCheckpoints(
    conversation_id: string,
    user_id: string
): Promise<CheckpointResponse[]> {
    const response = await fetch(
        `${BACKEND_URL}/v1/checkpoints/list/${conversation_id}?user_id=${user_id}`
    )
    return await response.json()
}
```

**Request:**
```
GET /v1/checkpoints/list/{conversation_id}?user_id=guest

Response:
[
    {
        "id": "546e6566-ab83-47fa-a285-aa876ad5cb7b",
        "version_number": 1,
        "title": "Python Guide - Version 1",
        "description": "Initial comprehensive Python programming guide",
        "created_at": "2025-12-24T17:45:11.866840",
        "is_active": false
    },
    {
        "id": "f59b0c3b-539d-4530-94d6-a4389ba7ab56",
        "version_number": 2,
        "title": "Python Guide - Version 2",
        "description": "Added Advanced Topics section",
        "created_at": "2025-12-24T17:45:16.773999",
        "is_active": true
    }
]
```

**Frontend displays:**
- Version 1 ← (user can click restore here)
- Version 2 [ACTIVE]

---

### Step 2: User Clicks "Restore" Button

When user selects a checkpoint to restore:

**Frontend Code:**
```typescript
export async function restoreCheckpoint(
    checkpoint_id: string,
    user_id: string,
    conversation_id?: string
): Promise<{
    status: string
    checkpoint_id: string
    version: number
    title: string
    content: string
}> {
    const params = new URLSearchParams({
        user_id: user_id,
        ...(conversation_id && { conversation_id: conversation_id })
    })
    
    const response = await fetch(
        `${BACKEND_URL}/v1/checkpoints/${checkpoint_id}/restore?${params.toString()}`,
        {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
        }
    )
    return await response.json()
}
```

**Frontend calls:**
```typescript
// When user clicks "Restore Version 1"
const result = await restoreCheckpoint(
    "546e6566-ab83-47fa-a285-aa876ad5cb7b",
    "guest",
    "2c1a70a1-9e95-41a1-8a39-62f1ef7da02d"
)
```

---

### Step 3: Backend Restores Checkpoint

**Request:**
```
POST /v1/checkpoints/{checkpoint_id}/restore?user_id=guest&conversation_id={id}

Response:
{
    "status": "restored",
    "checkpoint_id": "546e6566-ab83-47fa-a285-aa876ad5cb7b",
    "version": 1,
    "title": "Python Guide - Version 1",
    "content": "# Python Programming Guide\n\n## Introduction\n...",
    "tone": "informative",
    "length": "long",
    "restored_at": "2025-12-24T17:45:20.123456"
}
```

**Backend actions (in order):**
1. Finds the checkpoint by ID and user_id
2. Deactivates current active checkpoint
3. Activates the selected checkpoint (`is_active = true`)
4. If checkpoint has context_snapshot, updates the conversation_context table
5. Returns the restored checkpoint data

---

### Step 4: Frontend Loads the Restored Context

After checkpoint is restored, frontend reloads the conversation context:

**Frontend Code:**
```typescript
export async function loadContext(
    conversation_id: string,
    user_id: string
): Promise<LoadContextResponse> {
    const response = await fetch(
        `${BACKEND_URL}/v1/context/load/${conversation_id}?user_id=${user_id}`
    )
    return await response.json()
}
```

**Frontend calls:**
```typescript
// Reload context with restored data
const context = await loadContext(
    "2c1a70a1-9e95-41a1-8a39-62f1ef7da02d",
    "guest"
)
```

**Response:**
```
GET /v1/context/load/{conversation_id}?user_id=guest

{
    "message_count": 4,
    "messages": [
        {
            "id": "...",
            "role": "user",
            "content": "Write a blog post about Python programming",
            "timestamp": "...",
            "tone": "informative"
        },
        {
            "id": "...",
            "role": "assistant",
            "content": "Here's a comprehensive guide...",
            "timestamp": "..."
        },
        ...
    ],
    "current_blog_content": "# Python Programming Guide\n\n## Introduction\nPython is...",
    "chat_messages": [...]
}
```

---

### Step 5: Frontend Updates the UI

**Frontend updates:**
```typescript
// Update the blog editor
editor.setContent(context.current_blog_content)

// Update chat history
setChatHistory(context.messages)

// Show user success message
showNotification("✓ Restored to Version 1")
```

**Result:**
- Editor shows the original blog content from Version 1
- Chat history shows the original conversation
- Version 1 checkpoint is now marked as [ACTIVE]

---

## Complete API Endpoints Used

### 1. Create Checkpoint
```
POST /v1/checkpoints/create
Body: {
    "conversation_id": "...",
    "user_id": "guest",
    "title": "Version name",
    "content": "blog content here",
    "description": "what changed",
    "tone": "informative",
    "length": "long",
    "context_snapshot": { ... }
}
```

### 2. List Checkpoints
```
GET /v1/checkpoints/list/{conversation_id}?user_id={user_id}
Returns: CheckpointResponse[]
```

### 3. Get Specific Checkpoint
```
GET /v1/checkpoints/{checkpoint_id}?user_id={user_id}
Returns: CheckpointResponse
```

### 4. Restore Checkpoint
```
POST /v1/checkpoints/{checkpoint_id}/restore?user_id={user_id}&conversation_id={id}
Returns: { status, checkpoint_id, version, title, content, ... }
```

### 5. Load Restored Context
```
GET /v1/context/load/{conversation_id}?user_id={user_id}
Returns: LoadContextResponse with all messages and blog content
```

---

## Real Example from Test

Here's what actually happened when we ran the test:

### Timeline:
```
17:45:09 - Created Version 1 checkpoint with Python guide (289 chars)
17:45:11 - Saved as checkpoint V1 - "Python Guide - Version 1"
17:45:16 - User edited blog, added Advanced Topics section (523 chars)
17:45:18 - Saved as checkpoint V2 - "Python Guide - Version 2"
17:45:20 - Listed checkpoints: [V1 inactive, V2 active]
17:45:22 - User clicked "Restore Version 1"
17:45:23 - Backend restored V1 as active, updated conversation_context
17:45:24 - Frontend loaded restored context
17:45:25 - Editor shows V1 content (no Advanced Topics)
```

### What Happened in Database:

**blog_checkpoints table:**
```
id                                    | version | title              | is_active | created_at
546e6566-ab83-47fa-a285-aa876ad5cb7b | 1       | Python Guide V1    | true      | 2025-12-24 17:45:11
f59b0c3b-539d-4530-94d6-a4389ba7ab56 | 2       | Python Guide V2    | false     | 2025-12-24 17:45:16
```

**conversation_contexts table:**
```
conversation_id                      | user_id | messages_context | blog_context | message_count | last_updated_at
2c1a70a1-9e95-41a1-8a39-62f1ef7da02d | guest   | [4 messages]     | (V1 content) | 4             | 2025-12-24 17:45:23
```

---

## Key Points

✅ **Two-Request Process:**
1. POST to restore (changes active state)
2. GET to load (retrieves restored context)

✅ **Context Snapshot Storage:**
- Checkpoint saves complete context at time of creation
- When restored, that exact context is reloaded
- Message history is preserved perfectly

✅ **Version Management:**
- Each checkpoint is a separate version
- Only one can be [ACTIVE] at a time
- Restoring auto-deactivates previous version

✅ **Guest User Support:**
- Works with string user_id = "guest"
- No authentication required
- Each guest has separate conversation contexts

✅ **Full State Restoration:**
- All messages restored
- Blog content restored
- Conversation metadata restored
- UI can recreate exact state from loaded context

---

## Frontend UI Pattern

```typescript
// 1. Show checkpoint selector
<CheckpointVersionSelector
    checkpoints={checkpoints}
    onRestore={(checkpoint) => {
        await restoreCheckpoint(checkpoint.id, userId, conversationId)
        // 2. Reload context after restore
        const context = await loadContext(conversationId, userId)
        // 3. Update editors
        editor.setContent(context.current_blog_content)
        setChatHistory(context.messages)
    }}
/>
```

This is how Genesis implements time-travel - you can literally go back to any previous saved version of your blog!
