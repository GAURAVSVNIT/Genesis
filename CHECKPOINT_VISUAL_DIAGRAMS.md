# Checkpoint Flow - Visual Diagrams

## Diagram 1: When Checkpoints Are Created

```
TIMELINE - Checkpoint Creation Points
───────────────────────────────────────────────────────────────────

TIME      ACTION                          CHECKPOINT STATE
────────────────────────────────────────────────────────────────────
10:00     Start: "Write Python guide"     [NONE]
10:01     AI responds                     [NONE - Auto saved to context]
10:02     ↓ User clicks [Save as V1]      [V1 CREATED] ← Manual
10:05     Edit: add Advanced Topics       [V1 only - Context updated, no checkpoint]
10:06     ↓ User clicks [Save as V2]      [V1, V2 CREATED] ← Manual
10:10     Edit: reword some text          [V1, V2 - Context updated, no checkpoint]
10:15     ↓ User clicks [Restore V1]      [V1 ACTIVE, V2 inactive] ← Restoration

KEY:
✓ Checkpoints created ONLY on user button click
✓ Context is saved automatically after each message
✓ Checkpoint = snapshot of context at that moment
✓ User must explicitly click "Save as Version" button
```

---

## Diagram 2: Database Storage During Lifecycle

```
┌─────────────────────────────────────────────────────────────────┐
│              AFTER USER CREATES CHECKPOINT V1                   │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  blog_checkpoints TABLE:                                        │
│  ┌────────────────────────────────────────────────────────┐    │
│  │ id: 546e6566-ab83-47fa-a285-aa876ad5cb7b             │    │
│  │ version_number: 1                                      │    │
│  │ title: "Python Guide - Version 1"                     │    │
│  │ content: "# Python Programming Guide\n\n..."          │    │
│  │ is_active: TRUE                                       │    │
│  │ context_snapshot: {                                   │    │
│  │   "messages": [4 message objects],                    │    │
│  │   "chat_context": [formatted chat],                   │    │
│  │   "current_blog": "# Python Programming..."           │    │
│  │ }                                                      │    │
│  │ created_at: 2025-12-24 17:48:45                      │    │
│  └────────────────────────────────────────────────────────┘    │
│                                                                 │
│  conversation_contexts TABLE:                                   │
│  ┌────────────────────────────────────────────────────────┐    │
│  │ id: 99be7053-6932-4358-a0d4-c48f9777ae68             │    │
│  │ user_id: "guest"                                       │    │
│  │ messages_context: [same as checkpoint]                │    │
│  │ chat_context: "User: ...\nAI: ..."                   │    │
│  │ blog_context: "# Python Programming..."               │    │
│  │ message_count: 4                                       │    │
│  │ last_updated_at: 2025-12-24 17:48:45                 │    │
│  └────────────────────────────────────────────────────────┘    │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

```
┌─────────────────────────────────────────────────────────────────┐
│         AFTER USER CREATES CHECKPOINT V2 (523 chars)           │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  blog_checkpoints TABLE:                                        │
│  ┌─────────────────────────────────┐                          │
│  │ [V1]                            │                          │
│  │ version: 1                      │                          │
│  │ content: (289 chars)            │                          │
│  │ is_active: FALSE ← Deactivated  │                          │
│  └─────────────────────────────────┘                          │
│                                                                 │
│  ┌─────────────────────────────────┐                          │
│  │ [V2] ← NEW                      │                          │
│  │ version: 2                      │                          │
│  │ content: (523 chars)            │                          │
│  │ is_active: TRUE ← Activated     │                          │
│  └─────────────────────────────────┘                          │
│                                                                 │
│  conversation_contexts TABLE:                                   │
│  ┌─────────────────────────────────┐                          │
│  │ blog_context: (523 chars)       │                          │
│  │ message_count: 4                │                          │
│  │ last_updated_at: NOW()          │                          │
│  └─────────────────────────────────┘                          │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

```
┌─────────────────────────────────────────────────────────────────┐
│      AFTER USER CLICKS [RESTORE V1]                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  blog_checkpoints TABLE:                                        │
│  ┌─────────────────────────────────┐                          │
│  │ [V1]                            │                          │
│  │ version: 1                      │                          │
│  │ is_active: TRUE ← Reactivated!  │                          │
│  └─────────────────────────────────┘                          │
│                                                                 │
│  ┌─────────────────────────────────┐                          │
│  │ [V2]                            │                          │
│  │ version: 2                      │                          │
│  │ is_active: FALSE ← Deactivated  │                          │
│  └─────────────────────────────────┘                          │
│                                                                 │
│  conversation_contexts TABLE:                                   │
│  ┌─────────────────────────────────┐                          │
│  │ blog_context: (289 chars)       │ ← From V1 snapshot      │
│  │ messages_context: [...]         │ ← From V1 snapshot      │
│  │ message_count: 4                │ ← From V1 snapshot      │
│  │ last_updated_at: NOW()          │ ← Updated on restore    │
│  └─────────────────────────────────┘                          │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## Diagram 3: Frontend Restoration Flow

```
STEP 1: SHOW CHECKPOINT LIST
┌────────────────────────────────────────────────┐
│ User Interface                                 │
├────────────────────────────────────────────────┤
│  [Version History Panel]                       │
│  ┌──────────────────────────────────────────┐ │
│  │ v2: Python Guide - Version 2 [ACTIVE]    │ │
│  │     [Restore] [Delete]                   │ │
│  │                                          │ │
│  │ v1: Python Guide - Version 1             │ │
│  │     [Restore] ← User clicks here         │ │
│  │     [Delete]                             │ │
│  └──────────────────────────────────────────┘ │
└────────────────────────────────────────────────┘
                     ↓
           listCheckpoints()
                     ↓
         GET /v1/checkpoints/list
         
         
STEP 2: RESTORE CHECKPOINT
┌────────────────────────────────────────────────┐
│ Frontend: restoreCheckpoint()                  │
├────────────────────────────────────────────────┤
│                                                │
│  POST /v1/checkpoints/{id}/restore             │
│  ?user_id=guest&conversation_id={id}           │
│                                                │
└────────────────────────────────────────────────┘
                     ↓
         ┌───────────────────────┐
         │   BACKEND ACTIONS:    │
         ├───────────────────────┤
         │ 1. Find checkpoint    │
         │ 2. Deactivate old     │
         │ 3. Activate new       │
         │ 4. Update context     │
         │    with snapshot      │
         └───────────────────────┘
                     ↓
         Response: {
           "status": "restored",
           "version": 1,
           "title": "Python Guide V1"
         }
         

STEP 3: LOAD RESTORED CONTEXT
┌────────────────────────────────────────────────┐
│ Frontend: loadContext()                        │
├────────────────────────────────────────────────┤
│                                                │
│  GET /v1/context/load/{conversation_id}        │
│  ?user_id=guest                                │
│                                                │
└────────────────────────────────────────────────┘
                     ↓
         ┌───────────────────────┐
         │   BACKEND ACTIONS:    │
         ├───────────────────────┤
         │ Query conversation_   │
         │ contexts table        │
         │ (Updated in step 2)   │
         └───────────────────────┘
                     ↓
         Response: {
           "messages": [4 messages],
           "current_blog_content": "...",
           "chat_messages": [...]
         }
         

STEP 4: UPDATE UI
┌────────────────────────────────────────────────┐
│ Frontend: Update Components                    │
├────────────────────────────────────────────────┤
│                                                │
│ editor.setContent(context.blog_content)        │
│ ↓ Shows: "# Python Guide" (289 chars, V1)     │
│                                                │
│ setChatHistory(context.messages)               │
│ ↓ Shows: 4 messages from V1                    │
│                                                │
│ Update version badges                          │
│ ↓ Shows: "v1 [ACTIVE]" and "v2 [inactive]"   │
│                                                │
└────────────────────────────────────────────────┘
                     ↓
           RESTORATION COMPLETE!
           
User sees V1 content without Advanced Topics
```

---

## Diagram 4: Context Snapshot Content

```
WHAT GETS SAVED IN context_snapshot
═══════════════════════════════════════════════════════════════

{
  "user_id": "guest",
  "conversation_id": "99be7053-6932-4358-a0d4-c48f9777ae68",
  
  "messages": [
    ┌─────────────────────────────────────────────┐
    │ Message 1 (User)                            │
    │ - id: "msg-1"                              │
    │ - role: "user"                             │
    │ - content: "Write a blog about Python"     │
    │ - timestamp: "1703437625.123"              │
    │ - tone: "informative"                      │
    │ - length: "medium"                         │
    └─────────────────────────────────────────────┘
    ┌─────────────────────────────────────────────┐
    │ Message 2 (Assistant)                       │
    │ - id: "msg-2"                              │
    │ - role: "assistant"                        │
    │ - content: "Here's a comprehensive guide..."│
    │ - timestamp: "1703437626.456"              │
    └─────────────────────────────────────────────┘
    ... (Messages 3 & 4)
  ],
  
  "chatContext": [
    {"role": "user", "content": "..."},
    {"role": "assistant", "content": "..."},
    {"role": "user", "content": "..."},
    {"role": "assistant", "content": "..."}
  ],
  
  "current_blog": "# Python Programming Guide\n\n..."
}

THIS ENTIRE OBJECT IS STORED IN:
- blog_checkpoints.context_snapshot (JSONB)
- conversation_contexts.messages_context (JSONB)

WHEN RESTORED:
The entire snapshot is copied from blog_checkpoints
back to conversation_contexts, allowing full restoration
```

---

## Diagram 5: State Changes During Restore

```
BEFORE RESTORE (V2 is ACTIVE)
├─ blog_checkpoints
│  ├─ V1: is_active = FALSE
│  └─ V2: is_active = TRUE  ← Current
│
└─ conversation_contexts
   └─ blog_context: "# Python...\n## Advanced Topics\n..." (523 chars)


RESTORE COMMAND: POST /checkpoints/V1/restore
     ↓ ↓ ↓


DURING RESTORE (Backend executes 3 updates)
├─ UPDATE blog_checkpoints SET is_active=FALSE WHERE id=V2
│  └─ V2: is_active = FALSE
│
├─ UPDATE blog_checkpoints SET is_active=TRUE WHERE id=V1
│  └─ V1: is_active = TRUE  ← Reactivated
│
└─ UPDATE conversation_contexts 
   SET blog_context = V1_snapshot.current_blog,
       messages_context = V1_snapshot.messages,
       ...
   └─ conversation_contexts:
      └─ blog_content: "# Python...\n## Getting Started..." (289 chars)


AFTER RESTORE (V1 is ACTIVE)
├─ blog_checkpoints
│  ├─ V1: is_active = TRUE   ← Now active
│  └─ V2: is_active = FALSE  ← Deactivated
│
└─ conversation_contexts
   └─ blog_context: "# Python...\n## Getting Started..." (289 chars)
   
   
FRONTEND LOADS THIS AND SHOWS:
- Blog editor: "# Python..." (without Advanced Topics)
- Chat history: 4 messages from V1
- Version badge: "v1 [ACTIVE]"
```

---

## Diagram 6: API Call Sequence

```
┌──────────┐                                           ┌─────────────┐
│ Frontend │                                           │   Backend   │
└────┬─────┘                                           └──────┬──────┘
     │                                                        │
     │ 1. GET /v1/checkpoints/list/{id}?user_id=guest       │
     ├───────────────────────────────────────────────────→  │
     │                                                        │
     │    SELECT * FROM blog_checkpoints                     │
     │    WHERE conversation_id = id                         │
     │                                                        │
     │ ←─────────────────────────────────────────────────────┤
     │    [v1: inactive, v2: active]                         │
     │                                                        │
     │ (User clicks Restore on V1)                          │
     │                                                        │
     │ 2. POST /checkpoints/V1/restore?user_id=...          │
     ├───────────────────────────────────────────────────→  │
     │                                                        │
     │    UPDATE blog_checkpoints SET is_active=false        │
     │    WHERE id = V2                                      │
     │    UPDATE blog_checkpoints SET is_active=true         │
     │    WHERE id = V1                                      │
     │    UPDATE conversation_contexts SET                   │
     │      blog_context = V1_snapshot,                      │
     │      messages_context = V1_snapshot,                  │
     │      ...                                              │
     │                                                        │
     │ ←─────────────────────────────────────────────────────┤
     │    {"status": "restored", "version": 1}              │
     │                                                        │
     │ 3. GET /v1/context/load/{id}?user_id=guest           │
     ├───────────────────────────────────────────────────→  │
     │                                                        │
     │    SELECT * FROM conversation_contexts                │
     │    WHERE conversation_id = id                         │
     │                                                        │
     │ ←─────────────────────────────────────────────────────┤
     │    {messages: [...], blog_content: "...", ...}       │
     │                                                        │
     │ (Update UI with restored content)                    │
     │                                                        │
```

---

## Diagram 7: Checkpoint Creation vs Auto-Save

```
┌─────────────────────────────────────────────────────────────┐
│            TWO DIFFERENT MECHANISMS                         │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  AUTO-SAVE (Every message)                                 │
│  ──────────────────────────────────────────────────────    │
│  User: "Write Python guide"                                │
│  ↓                                                          │
│  Backend: POST /v1/context/save                            │
│  ↓                                                          │
│  Database: conversation_contexts UPDATED                   │
│  ↓                                                          │
│  ✓ Latest state saved, ready for restore                   │
│  ✗ NOT in blog_checkpoints yet (no version number)         │
│                                                             │
│  ──────────────────────────────────────────────────────    │
│                                                             │
│  CHECKPOINT (User initiated)                               │
│  ────────────────────────────────────────                  │
│  User: clicks [Save as Version 1]                          │
│  ↓                                                          │
│  Frontend: POST /v1/checkpoints/create                     │
│  ↓                                                          │
│  Backend:                                                   │
│    - Copies current context_snapshot                        │
│    - Creates blog_checkpoints row                           │
│    - Sets version_number = 1                                │
│    - Sets is_active = true                                  │
│  ↓                                                          │
│  Database: blog_checkpoints row INSERTED                   │
│  ✓ Snapshot saved with version number                      │
│  ✓ Ready for later restoration                             │
│                                                             │
└─────────────────────────────────────────────────────────────┘

KEY DIFFERENCE:
┌─────────────────┬──────────────────┬────────────────────┐
│                 │   Auto-Save      │   Checkpoint       │
├─────────────────┼──────────────────┼────────────────────┤
│ When?           │ After every msg  │ On button click    │
│ Table?          │ context_*        │ blog_checkpoints   │
│ Version #?      │ NO               │ YES (1, 2, 3...)   │
│ Can restore?    │ Latest only      │ Any version        │
│ User action?    │ Automatic        │ Manual             │
└─────────────────┴──────────────────┴────────────────────┘
```

---

## Diagram 8: Complete User Journey

```
10:00 AM
┌─────────────────────────────────────────┐
│ User opens Genesis                      │
│ Conversation ID: 99be7053...            │
└─────────────────────────────────────────┘
         ↓

10:01 AM
┌─────────────────────────────────────────┐
│ User: "Write Python programming guide"  │
│ AI responds...                          │
│ [Auto-saved to conversation_contexts]   │
└─────────────────────────────────────────┘
         ↓

10:02 AM
┌─────────────────────────────────────────┐
│ User clicks [Save as Version 1]         │
│ Blog content: 289 characters            │
│ ✓ V1 checkpoint created                 │
│ ✓ V1 marked as [ACTIVE]                 │
└─────────────────────────────────────────┘
         ↓
      (2 more messages exchanged)
         ↓

10:05 AM
┌─────────────────────────────────────────┐
│ User adds "Advanced Topics" section      │
│ Blog content: 523 characters            │
│ User clicks [Save as Version 2]         │
│ ✓ V2 checkpoint created                 │
│ ✗ V1 marked as [inactive]               │
│ ✓ V2 marked as [ACTIVE]                 │
└─────────────────────────────────────────┘
         ↓
      (More editing, but no checkpoints)
         ↓

10:15 AM
┌─────────────────────────────────────────┐
│ User: "Actually, I liked the simpler     │
│        version without Advanced Topics"  │
│ User clicks [Restore V1]                │
└─────────────────────────────────────────┘
         ↓
  BACKEND EXECUTES:
  - V2.is_active = false
  - V1.is_active = true
  - conversation_contexts.blog_context = V1 (289 chars)
  - conversation_contexts.messages = V1 messages
         ↓

10:16 AM
┌─────────────────────────────────────────┐
│ Frontend loads restored context          │
│ Editor shows: "# Python..." (289 chars)  │
│ NO "Advanced Topics" section             │
│ Chat history: restored from V1           │
│ Version indicator: "V1 [ACTIVE]"         │
│                                         │
│ User happy! Time-travel worked!          │
└─────────────────────────────────────────┘
```

This is how checkpoints enable time-travel in Genesis!
