# Frontend Integration Guide - Checkpoints with Chat & Images

## Problem
When restoring a checkpoint, chat messages and images weren't being displayed in the frontend.

## Solution
The backend now explicitly returns `chat_messages`, `all_messages`, and `image_url` when restoring.

## Frontend Integration

### 1. When Creating Checkpoint (Save)

```javascript
// User clicks "Save Checkpoint"
const createCheckpoint = async () => {
  const response = await fetch('/v1/checkpoints/create', {
    method: 'POST',
    body: JSON.stringify({
      conversation_id: conversationId,
      user_id: userId,
      title: "My Blog Draft v1",
      content: blogContent,  // The blog text
      image_url: currentImageUrl,  // ⭐ The generated image
      description: "First draft",
      tone: "professional",
      context_snapshot: {
        messages: allMessages,  // All message history
        chat_messages: chatMessages,  // Just chat messages
        current_blog_content: blogContent,
        current_blog_image: currentImageUrl  // ⭐ Image in context too
      }
    })
  });
  
  const checkpoint = await response.json();
  console.log('Checkpoint created:', checkpoint.version_number);
};
```

### 2. When Restoring Checkpoint (Load)

```javascript
// User clicks "Restore v1"
const restoreCheckpoint = async (checkpointId) => {
  const response = await fetch(`/v1/checkpoints/${checkpointId}/restore`, {
    method: 'POST',
    params: { user_id: userId, conversation_id: conversationId }
  });
  
  const restored = await response.json();
  
  // ⭐ Now you get everything explicitly:
  console.log('Restored data:', {
    content: restored.content,           // Blog text
    image: restored.image_url,           // ⭐ Image URL
    chatMessages: restored.chat_messages, // ⭐ Chat history
    allMessages: restored.all_messages,   // ⭐ Full message history
    messagesCount: restored.messages_count
  });
  
  // 1. Restore blog content
  setBlogContent(restored.content);
  
  // 2. Restore image ⭐
  setCurrentImage(restored.image_url);
  
  // 3. Restore chat messages ⭐
  setChatMessages(restored.chat_messages || []);
  
  // 4. Restore all messages (if needed)
  setAllMessages(restored.all_messages || []);
  
  // 5. Show success message
  alert(restored.message);  
  // "Checkpoint restored. Content, image, and 5 chat messages have been loaded."
};
```

### 3. Complete Example Component

```typescript
import { useState } from 'react';

interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  image_url?: string;
}

const BlogEditor = () => {
  const [blogContent, setBlogContent] = useState('');
  const [currentImage, setCurrentImage] = useState<string | null>(null);
  const [chatMessages, setChatMessages] = useState<Message[]>([]);
  
  // Save checkpoint
  const saveCheckpoint = async () => {
    await fetch('/v1/checkpoints/create', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        conversation_id: 'conv-123',
        user_id: 'user-456',
        title: `Draft ${new Date().toLocaleString()}`,
        content: blogContent,
        image_url: currentImage,  // ⭐ Save image
        context_snapshot: {
          chat_messages: chatMessages,  // ⭐ Save chat
          current_blog_content: blogContent,
          current_blog_image: currentImage
        }
      })
    });
  };
  
  // Restore checkpoint
  const restoreCheckpoint = async (checkpointId: string) => {
    const response = await fetch(
      `/v1/checkpoints/${checkpointId}/restore?user_id=user-456`,
      { method: 'POST' }
    );
    
    const data = await response.json();
    
    // Restore everything ⭐
    setBlogContent(data.content);
    setCurrentImage(data.image_url);
    setChatMessages(data.chat_messages || []);
    
    console.log(`✅ Restored: ${data.messages_count} messages`);
  };
  
  return (
    <div>
      {/* Blog editor */}
      <textarea value={blogContent} onChange={e => setBlogContent(e.target.value)} />
      
      {/* Image display */}
      {currentImage && <img src={currentImage} alt="Blog" />}
      
      {/* Chat history */}
      <div className="chat">
        {chatMessages.map(msg => (
          <div key={msg.id} className={msg.role}>
            <p>{msg.content}</p>
            {msg.image_url && <img src={msg.image_url} />}
          </div>
        ))}
      </div>
      
      {/* Checkpoint buttons */}
      <button onClick={saveCheckpoint}>Save Checkpoint</button>
      <button onClick={() => restoreCheckpoint('checkpoint-id')}>
        Restore v1
      </button>
    </div>
  );
};
```

## What's Different Now?

### Before:
```javascript
// Restore only returned:
{
  content: "...",
  context_snapshot: { ... }  // Nested, hard to access
}
```

### After:
```javascript
// Restore now explicitly returns:
{
  content: "...",
  image_url: "...",           // ⭐ Direct access
  chat_messages: [...],        // ⭐ Direct access
  all_messages: [...],         // ⭐ Direct access
  messages_count: 5,
  context_snapshot: { ... }    // Still there for compatibility
}
```

## Testing

```bash
# Backend test
cd apps/backend
python scripts/demo_checkpoint_simple.py
```

## Key Points

1. **Always save `image_url`** when creating checkpoints
2. **Always save `chat_messages`** in `context_snapshot`
3. **Use the explicit fields** (`chat_messages`, `image_url`) from restore response
4. **Don't dig into `context_snapshot`** - use the top-level fields
5. **Check `messages_count`** to see how many messages were restored

## Debugging

If chat/images still don't show:

```javascript
const data = await response.json();
console.log('Restore response:', data);
console.log('Chat messages:', data.chat_messages);
console.log('Image URL:', data.image_url);
console.log('Messages count:', data.messages_count);

// Check if fields exist
if (!data.chat_messages) {
  console.error('❌ No chat_messages in response!');
}
if (!data.image_url) {
  console.warn('⚠️  No image_url in response');
}
```
