# Quick Reference: Frontend Checkpoint Restore Requests

## TL;DR - The Two Requests

### Request 1: Restore the Checkpoint
```
POST /v1/checkpoints/{checkpoint_id}/restore?user_id=guest&conversation_id={id}

What it does:
- Marks checkpoint as "is_active = true"
- Deactivates all other checkpoints
- Updates conversation_contexts with checkpoint's saved data
```

### Request 2: Load the Restored Context
```
GET /v1/context/load/{conversation_id}?user_id=guest

What it does:
- Retrieves all messages and blog content from database
- Returns the state that was restored by the POST request
```

---

## Frontend Code Example

```typescript
// 1. Display list of checkpoints
const checkpoints = await listCheckpoints(conversationId, userId)
checkpoints.forEach(cp => {
    console.log(`v${cp.version_number}: ${cp.title} ${cp.is_active ? '[ACTIVE]' : ''}`)
})

// 2. User clicks a checkpoint to restore
async function handleRestoreClick(checkpointId: string) {
    // First: Restore the checkpoint
    const restoreResult = await restoreCheckpoint(
        checkpointId,
        userId,
        conversationId
    )
    console.log(`Restored: ${restoreResult.title}`)
    
    // Second: Load the restored context
    const restoredContext = await loadContext(conversationId, userId)
    
    // Third: Update the UI
    editor.setContent(restoredContext.current_blog_content)
    chatHistory.setMessages(restoredContext.messages)
    showNotification(`Restored to ${restoreResult.title}`)
}
```

---

## API Parameters

| Endpoint | Method | Parameters | Body |
|----------|--------|-----------|------|
| `/v1/checkpoints/list/{id}` | GET | `user_id` (query) | None |
| `/v1/checkpoints/{id}/restore` | POST | `user_id`, `conversation_id` (query) | Empty |
| `/v1/context/load/{id}` | GET | `user_id` (query) | None |

---

## What Gets Restored

✅ **Messages** - All user and AI messages in the conversation
✅ **Blog Content** - Exact markdown that was saved at checkpoint time
✅ **Chat History** - Full conversation history
✅ **Metadata** - Message timestamps, tones, lengths
✅ **Version State** - Only one checkpoint marked as [ACTIVE]

---

## Database Changes During Restore

```
Before Restore:
blog_checkpoints:
  v1 [INACTIVE] - 289 chars
  v2 [ACTIVE]   - 523 chars  ← Current
  
conversation_contexts:
  blog_context = (v2 content with Advanced Topics)

After Restore:
blog_checkpoints:
  v1 [ACTIVE]   - 289 chars  ← Now active!
  v2 [INACTIVE] - 523 chars
  
conversation_contexts:
  blog_context = (v1 content without Advanced Topics)
  
Result: Editor shows v1 content
```

---

## Response Examples

### Restore Response
```json
{
    "status": "restored",
    "checkpoint_id": "546e6566-ab83-47fa-a285-aa876ad5cb7b",
    "version": 1,
    "title": "Python Guide - Version 1",
    "content": "# Python Programming Guide\n\n## Introduction...",
    "tone": "informative",
    "length": "long",
    "restored_at": "2025-12-24T17:45:20.123456"
}
```

### Load Response
```json
{
    "message_count": 4,
    "messages": [
        {"id": "...", "role": "user", "content": "...", "timestamp": "..."},
        {"id": "...", "role": "assistant", "content": "...", "timestamp": "..."},
        ...
    ],
    "current_blog_content": "# Python Programming Guide\n\n...",
    "chat_messages": [...]
}
```

---

## Testing the Flow

Run our test to see it in action:
```bash
cd E:\genesis\apps\backend
python test_checkpoint_restore_flow.py
```

This test:
1. Creates a blog post and saves checkpoint v1 (289 chars)
2. User edits blog, adds Advanced Topics section
3. Saves checkpoint v2 (523 chars)
4. Lists both checkpoints (v1 inactive, v2 active)
5. **Restores v1** - marks it as active, deactivates v2
6. **Loads context** - retrieves v1 content from database
7. Verifies v1 content restored (no Advanced Topics)

---

## Key Points

- **Two requests needed**: Restore + Load
- **Fast restore**: Only marks checkpoint as active, doesn't copy data
- **Context snapshot**: Saves all data, full restoration possible
- **One active**: Only one checkpoint per conversation can be [ACTIVE]
- **Time-travel**: Can restore to any previous version instantly
- **No data loss**: Old versions never deleted, always restorable

---

## Files to Reference

- **Frontend API**: [apps/frontend/lib/api/context.ts](apps/frontend/lib/api/context.ts)
- **Backend API**: [apps/backend/api/v1/context.py](apps/backend/api/v1/context.py)
- **Database Models**: [apps/backend/database/models/conversation.py](apps/backend/database/models/conversation.py)
- **Test Script**: [apps/backend/test_checkpoint_restore_flow.py](apps/backend/test_checkpoint_restore_flow.py)
