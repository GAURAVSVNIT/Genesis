# Checkpoint Storage & Restoration - Complete Guide

## Part 1: How Checkpoints Are Stored

### Database Structure

**blog_checkpoints table:**
```sql
CREATE TABLE blog_checkpoints (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_id VARCHAR(255),           -- Links to conversation
    user_id VARCHAR(255),                   -- "guest" for guest users
    title VARCHAR(255),                     -- "Python Guide - Version 1"
    content TEXT,                           -- Full blog content at time of checkpoint
    description TEXT,                       -- "Initial version" or "Added topics"
    version_number INTEGER,                 -- Auto-incrementing: 1, 2, 3...
    tone VARCHAR(50),                       -- "informative", "creative", "formal"
    length VARCHAR(50),                     -- "short", "medium", "long"
    context_snapshot JSONB,                 -- **FULL MESSAGE HISTORY**
    chat_messages_snapshot JSONB,           -- Full chat messages at time
    is_active BOOLEAN DEFAULT false,        -- Only ONE checkpoint per conversation
    created_at TIMESTAMP DEFAULT NOW(),     -- When checkpoint created
    updated_at TIMESTAMP DEFAULT NOW(),     -- When last modified
    FOREIGN KEY (conversation_id) REFERENCES conversation_contexts(conversation_id),
    FOREIGN KEY (user_id) REFERENCES conversation_contexts(user_id)
);
```

### What Gets Saved in a Checkpoint

When user creates a checkpoint, the database stores:

```json
{
    "id": "6f0ae875-e44c-43c3-93f4-29b7104526b7",
    "version_number": 1,
    "title": "Python Guide - Version 1",
    "content": "# Python Programming Guide\n\n## Introduction\n...",
    "description": "Initial comprehensive Python programming guide",
    "tone": "informative",
    "length": "long",
    "is_active": true,
    "created_at": "2025-12-24T17:48:45.756733",
    
    // Full snapshot at time of checkpoint creation
    "context_snapshot": {
        "user_id": "guest",
        "conversation_id": "99be7053-6932-4358-a0d4-c48f9777ae68",
        "messages": [
            {
                "id": "msg-1",
                "role": "user",
                "content": "Write a blog post about Python programming",
                "type": "chat",
                "timestamp": "1703437625.123",
                "tone": "informative",
                "length": "medium"
            },
            {
                "id": "msg-2",
                "role": "assistant",
                "content": "Here's a comprehensive guide to Python programming...",
                "type": "chat",
                "timestamp": "1703437626.456"
            }
            // ... more messages
        ],
        "chatContext": [
            {"role": "user", "content": "..."},
            {"role": "assistant", "content": "..."}
        ],
        "current_blog": "# Python Programming Guide\n\n..."
    },
    
    "chat_messages_snapshot": [
        {"role": "user", "content": "..."},
        {"role": "assistant", "content": "..."}
    ]
}
```

---

## Part 2: When Are Checkpoints Created?

### Checkpoint Creation Timing

⚠️ **IMPORTANT:** Checkpoints are **NOT created automatically**. They are created **MANUALLY by the user**.

### User Actions That Create Checkpoints

**In the Frontend UI, user can:**

1. **Click "Save as Version"** button after writing blog content
2. **Click "Create Checkpoint"** button after completing edits
3. **Click "Snapshot"** to save current state

**Example User Workflow:**

```
TIME    | USER ACTION                                  | DATABASE STATE
──────────────────────────────────────────────────────────────────────────
10:00   | Starts writing: "Tell me about Python"       | No checkpoint yet
        | AI responds: "Here's a guide..."             | Context saved to DB
        |                                               |
10:05   | User edits blog: adds Introduction section   | Context updated
        | User clicks [Save as Version 1]              | ✓ CHECKPOINT CREATED
        |                                               | blog_checkpoints.v1 (289 chars)
        |                                               |
10:10   | User continues editing: adds Key Features    | Context updated again
        | User continues: adds Getting Started         | Context saved, but
        |                                               | NO NEW CHECKPOINT
        |                                               |
10:15   | User adds Advanced Topics section             | Context updated
        | User clicks [Save as Version 2]              | ✓ CHECKPOINT CREATED
        |                                               | blog_checkpoints.v2 (523 chars)
        |                                               |
10:20   | User wants to go back to V1                   | 
        | User clicks [Restore Version 1]              | v1 activated, v2 deactivated
        |                                               | context restored to V1
```

### Key Points About Checkpoint Creation

✅ **Manual Creation:** User explicitly clicks a button
❌ **NOT Automatic:** Doesn't create on every save
✅ **Versioned:** Each checkpoint gets version_number (1, 2, 3...)
✅ **One Active:** Only one checkpoint can be [ACTIVE] per conversation
✅ **Full Snapshot:** Saves complete context at that moment
✅ **Descriptive:** User provides title and description

---

## Part 3: How Frontend Restores Context

### Frontend Restoration Flow (Step-by-Step)

#### **Step 1: Show List of Available Checkpoints**

**Frontend Code:**
```typescript
// In React component
import { listCheckpoints } from '@/lib/api/context'

export function VersionHistory() {
    const [checkpoints, setCheckpoints] = useState([])
    const conversationId = useParams().id
    const userId = 'guest'
    
    useEffect(() => {
        // Load all checkpoints for this conversation
        const data = await listCheckpoints(conversationId, userId)
        setCheckpoints(data)
    }, [conversationId])
    
    return (
        <div className="version-history">
            <h3>Version History</h3>
            {checkpoints.map(cp => (
                <VersionCard 
                    key={cp.id}
                    checkpoint={cp}
                    isActive={cp.is_active}
                    onRestore={() => handleRestore(cp.id)}
                />
            ))}
        </div>
    )
}
```

**API Call:**
```
GET /v1/checkpoints/list/{conversation_id}?user_id=guest

Response:
[
    {
        "id": "6f0ae875...",
        "version_number": 2,
        "title": "Python Guide - Version 2",
        "description": "Added Advanced Topics section",
        "created_at": "2025-12-24T17:48:50.684126",
        "is_active": true,
        "tone": "informative",
        "length": "long"
    },
    {
        "id": "f59b0c3b...",
        "version_number": 1,
        "title": "Python Guide - Version 1",
        "description": "Initial comprehensive guide",
        "created_at": "2025-12-24T17:48:45.756733",
        "is_active": false,
        "tone": "informative",
        "length": "long"
    }
]
```

**What User Sees:**
```
┌─────────────────────────────────────────┐
│        VERSION HISTORY                  │
├─────────────────────────────────────────┤
│ v2: Python Guide - Version 2 [ACTIVE]   │
│     Added Advanced Topics section       │
│     Created: 2025-12-24 17:48:50        │
│     [Details] [Restore] [Delete]        │
│                                         │
│ v1: Python Guide - Version 1            │
│     Initial comprehensive guide         │
│     Created: 2025-12-24 17:48:45        │
│     [Details] [Restore] [Delete] ← Click│
└─────────────────────────────────────────┘
```

---

#### **Step 2: User Clicks "Restore" Button**

**Frontend Code:**
```typescript
async function handleRestore(checkpointId: string) {
    try {
        // Show loading indicator
        setIsRestoring(true)
        
        // Step 2A: Tell backend to restore checkpoint
        const restoreResult = await restoreCheckpoint(
            checkpointId,
            userId,
            conversationId
        )
        
        console.log(`Restored: ${restoreResult.title}`)
        
        // Step 2B: Get the restored context
        const restoredContext = await loadContext(
            conversationId,
            userId
        )
        
        // Step 2C: Update the UI
        updateEditorContent(restoredContext.current_blog_content)
        updateChatHistory(restoredContext.messages)
        
        // Show success message
        showNotification(`Restored to ${restoreResult.title}`)
    } catch (error) {
        showError(`Failed to restore: ${error.message}`)
    } finally {
        setIsRestoring(false)
    }
}
```

---

#### **Step 2A: Restore Checkpoint (Backend Updates)**

**Frontend Request:**
```
POST /v1/checkpoints/{checkpoint_id}/restore
    ?user_id=guest
    &conversation_id=99be7053-6932-4358-a0d4-c48f9777ae68
```

**Backend Processing:**
```
1. Find checkpoint: id = "f59b0c3b..." in blog_checkpoints table
2. Deactivate all others: 
   UPDATE blog_checkpoints SET is_active=false 
   WHERE conversation_id='99be7053...' AND id != 'f59b0c3b...'
   
3. Activate this checkpoint:
   UPDATE blog_checkpoints SET is_active=true 
   WHERE id='f59b0c3b...'
   
4. Restore context_snapshot to conversation_contexts:
   UPDATE conversation_contexts SET
     messages_context = checkpoint.context_snapshot,
     chat_context = (formatted from snapshot),
     blog_context = checkpoint.content,
     message_count = checkpoint.message_count,
     last_updated_at = NOW()
   WHERE conversation_id='99be7053...' AND user_id='guest'
```

**Backend Response:**
```json
{
    "status": "restored",
    "checkpoint_id": "f59b0c3b-539d-4530-94d6-a4389ba7ab56",
    "version": 1,
    "title": "Python Guide - Version 1",
    "content": "# Python Programming Guide\n\n## Introduction\nPython is...",
    "description": "Initial comprehensive guide",
    "tone": "informative",
    "length": "long",
    "restored_at": "2025-12-24T17:45:20.123456"
}
```

---

#### **Step 2B: Load Restored Context**

**Frontend Request:**
```
GET /v1/context/load/99be7053-6932-4358-a0d4-c48f9777ae68
    ?user_id=guest
```

**Backend Processing:**
```
SELECT * FROM conversation_contexts 
WHERE conversation_id = '99be7053-6932-4358-a0d4-c48f9777ae68'
AND user_id = 'guest'

(Returns the record that was just updated by the restore)
```

**Backend Response:**
```json
{
    "message_count": 4,
    "messages": [
        {
            "id": "msg-1",
            "role": "user",
            "content": "Write a blog post about Python programming",
            "type": "chat",
            "timestamp": "1703437625.123",
            "tone": "informative",
            "length": "medium"
        },
        {
            "id": "msg-2",
            "role": "assistant",
            "content": "Here's a comprehensive guide to Python programming...",
            "type": "chat",
            "timestamp": "1703437626.456"
        },
        {
            "id": "msg-3",
            "role": "user",
            "content": "Make it more detailed",
            "type": "chat",
            "timestamp": "1703437650.789"
        },
        {
            "id": "msg-4",
            "role": "assistant",
            "content": "I've expanded the guide with more details...",
            "type": "chat",
            "timestamp": "1703437651.012"
        }
    ],
    "current_blog_content": "# Python Programming Guide\n\n## Introduction\nPython is a versatile programming language...",
    "chat_messages": [
        {"role": "user", "content": "Write a blog post about Python programming"},
        {"role": "assistant", "content": "Here's a comprehensive guide..."},
        {"role": "user", "content": "Make it more detailed"},
        {"role": "assistant", "content": "I've expanded the guide..."}
    ]
}
```

---

#### **Step 2C: Update Frontend UI**

**Frontend Code:**
```typescript
// Update blog editor
const editorElement = document.querySelector('[contenteditable]')
editorElement.innerHTML = restoredContext.current_blog_content

// Update chat history
setChatHistory(restoredContext.messages)

// Show version indicator
showVersionBadge(`v1 - Python Guide - Version 1 [RESTORED]`)

// Update version history UI
setCheckpoints(newCheckpoints.map(cp => ({
    ...cp,
    is_active: cp.id === checkpointId
})))
```

**What User Sees:**
```
BEFORE RESTORE:
┌─────────────────────────────────────┐
│ Chat History                        │
├─────────────────────────────────────┤
│ User: Write blog about Python       │
│ AI: Here's a guide...               │
│ User: Make it more detailed         │
│ AI: I've expanded the guide...      │
└─────────────────────────────────────┘
┌─────────────────────────────────────┐
│ Blog Editor                         │
├─────────────────────────────────────┤
│ # Python Programming Guide          │
│                                     │
│ ## Introduction                     │
│ Python is versatile...              │
│                                     │
│ ## Key Features                     │
│ - Easy to learn                     │
│                                     │
│ ## Advanced Topics          ← V2    │
│ ### OOP                             │
│ ### Functional                      │
│ ### APIs                            │
└─────────────────────────────────────┘

AFTER RESTORE TO V1:
┌─────────────────────────────────────┐
│ Chat History (SAME)                 │
├─────────────────────────────────────┤
│ User: Write blog about Python       │
│ AI: Here's a guide...               │
│ User: Make it more detailed         │
│ AI: I've expanded the guide...      │
└─────────────────────────────────────┘
┌─────────────────────────────────────┐
│ Blog Editor                         │
├─────────────────────────────────────┤
│ # Python Programming Guide          │
│                                     │
│ ## Introduction                     │
│ Python is versatile...              │
│                                     │
│ ## Key Features                     │
│ - Easy to learn                     │
│                                     │
│ ## Getting Started         ← V1     │
│ Install Python and start...         │
│                                     │
│ (NO Advanced Topics!)               │
└─────────────────────────────────────┘
```

---

## Part 4: Complete Restoration Code Example

### Frontend Complete Flow

```typescript
// lib/api/context.ts
export async function restoreCheckpoint(
    checkpoint_id: string,
    user_id: string,
    conversation_id?: string
) {
    const params = new URLSearchParams({
        user_id: user_id,
        ...(conversation_id && { conversation_id: conversation_id })
    })
    
    const response = await fetch(
        `${BACKEND_URL}/v1/checkpoints/${checkpoint_id}/restore?${params.toString()}`,
        { method: 'POST' }
    )
    
    if (!response.ok) throw new Error('Restore failed')
    return await response.json()
}

export async function loadContext(
    conversation_id: string,
    user_id: string
) {
    const response = await fetch(
        `${BACKEND_URL}/v1/context/load/${conversation_id}?user_id=${user_id}`
    )
    
    if (!response.ok) throw new Error('Load failed')
    return await response.json()
}

// components/VersionHistory.tsx
export function VersionHistory({ conversationId, userId }) {
    const [checkpoints, setCheckpoints] = useState([])
    const [editor, setEditor] = useState(null)
    
    useEffect(() => {
        loadVersions()
    }, [conversationId])
    
    async function loadVersions() {
        try {
            const data = await listCheckpoints(conversationId, userId)
            setCheckpoints(data)
        } catch (error) {
            console.error('Failed to load versions:', error)
        }
    }
    
    async function handleRestore(checkpoint: CheckpointResponse) {
        try {
            // STEP 1: Restore checkpoint in backend
            const restoreResult = await restoreCheckpoint(
                checkpoint.id,
                userId,
                conversationId
            )
            console.log(`Restored: ${restoreResult.title}`)
            
            // STEP 2: Load the restored context
            const context = await loadContext(conversationId, userId)
            
            // STEP 3: Update UI
            editor.setContent(context.current_blog_content)
            setChatHistory(context.messages)
            
            // STEP 4: Update version list
            await loadVersions()
            
            // STEP 5: Show success
            showNotification(`Restored to v${checkpoint.version_number}: ${checkpoint.title}`)
        } catch (error) {
            showError(`Restore failed: ${error.message}`)
        }
    }
    
    return (
        <div className="version-history">
            <h3>Version History</h3>
            {checkpoints.map(cp => (
                <div key={cp.id} className="checkpoint-card">
                    <div className="checkpoint-header">
                        <span className="version">v{cp.version_number}</span>
                        <span className="title">{cp.title}</span>
                        {cp.is_active && <span className="badge">ACTIVE</span>}
                    </div>
                    <p className="description">{cp.description}</p>
                    <p className="created">{new Date(cp.created_at).toLocaleString()}</p>
                    <button onClick={() => handleRestore(cp)}>
                        Restore
                    </button>
                </div>
            ))}
        </div>
    )
}
```

---

## Part 5: Database State Changes During Restore

### Real Example from Test

**BEFORE RESTORE:**
```sql
-- blog_checkpoints table
id                                    | version | title              | is_active
546e6566-ab83-47fa-a285-aa876ad5cb7b | 1       | Python Guide V1    | false
f59b0c3b-539d-4530-94d6-a4389ba7ab56 | 2       | Python Guide V2    | true  ← Active

-- conversation_contexts table
conversation_id                      | user_id | blog_content (523 chars)
99be7053-6932-4358-a0d4-c48f9777ae68 | guest   | (V2 content with Advanced Topics)
```

**RESTORE PROCESS:**
```
1. POST /checkpoints/546e6566.../restore
2. Backend executes:
   - UPDATE blog_checkpoints SET is_active=false WHERE id='f59b0c3b...'
   - UPDATE blog_checkpoints SET is_active=true WHERE id='546e6566...'
   - UPDATE conversation_contexts SET 
       blog_context = (v1 content: 289 chars),
       messages_context = (v1 snapshot)
     WHERE conversation_id='99be7053...'
```

**AFTER RESTORE:**
```sql
-- blog_checkpoints table
id                                    | version | title              | is_active
546e6566-ab83-47fa-a285-aa876ad5cb7b | 1       | Python Guide V1    | true  ← Now active!
f59b0c3b-539d-4530-94d6-a4389ba7ab56 | 2       | Python Guide V2    | false

-- conversation_contexts table
conversation_id                      | user_id | blog_content (289 chars)
99be7053-6932-4358-a0d4-c48f9777ae68 | guest   | (V1 content without Advanced Topics)
```

---

## Part 6: Timeline of Checkpoint Creation

### Real Workflow Timeline

```
17:48:40 - User: "Write Python programming guide"
17:48:41 - AI responds, context saved to DB
17:48:42 - User clicks [Save as Version] button
           └─> CHECKPOINT V1 CREATED (289 chars)
               blog_checkpoints.v1: "Python Guide - Version 1"
               
17:48:45 - User edits: adds "Advanced Topics" section
17:48:46 - Context updated, saved to DB
17:48:47 - User clicks [Save as Version] button again
           └─> CHECKPOINT V2 CREATED (523 chars)
               blog_checkpoints.v2: "Python Guide - Version 2"
               
17:48:50 - User continues editing, no checkpoint created

17:48:55 - User: "I want to go back to the simpler version"
17:48:56 - User clicks [Restore] on v1
           └─> RESTORE EXECUTED
               V1 marked as [ACTIVE]
               V2 marked as [inactive]
               conversation_contexts updated with V1 content
               
17:48:57 - Editor shows V1 content (no Advanced Topics)
           Chat history restored with 4 messages
```

---

## Part 7: Summary

### How Checkpoints Work

| Aspect | Details |
|--------|---------|
| **Storage** | JSONB in `blog_checkpoints.context_snapshot` |
| **Creation** | Manual - user clicks "Save as Version" button |
| **Frequency** | Not automatic, only on user request |
| **What's Saved** | Full blog content + all messages + metadata |
| **Database Tables** | `blog_checkpoints` + `conversation_contexts` |
| **Restoration** | 2 API calls: POST restore + GET load |
| **Version Limit** | Unlimited (no auto-cleanup) |
| **Active State** | Only ONE checkpoint per conversation |

### Restoration Flow Summary

```
1. User clicks "Restore v1"
   ↓
2. Frontend: POST /checkpoints/{id}/restore
   - Backend marks v1 as active
   - Backend marks v2 as inactive
   - Backend updates conversation_context with v1 data
   ↓
3. Frontend: GET /context/load/{conversation_id}
   - Backend returns all restored data
   ↓
4. Frontend updates UI
   - Editor shows v1 blog content
   - Chat history shows v1 messages
   - Version badge shows "[ACTIVE v1]"
   ↓
5. User sees restored version
```

This is the complete time-travel feature in Genesis!
