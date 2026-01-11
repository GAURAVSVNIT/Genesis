"""
Simple checkpoint workflow demo - Save and restore your work including images.

Workflow:
1. Generate content with image
2. Create checkpoint (saves content + image + chat history)
3. Make some edits
4. Restore previous checkpoint (everything comes back)
"""

import requests
import json

BASE_URL = "http://localhost:8000/v1"
USER_ID = "test-user-123"
CONVERSATION_ID = "test-conv-456"

def demo_checkpoint_workflow():
    print("\n" + "="*60)
    print("🔖 CHECKPOINT DEMO - Simple Version Control")
    print("="*60)
    
    # Step 1: Generate content with image
    print("\n📝 Step 1: Generate blog post with image...")
    gen_response = requests.post(
        f"{BASE_URL}/content/generate",
        json={
            "prompt": "Write about quantum computing breakthroughs",
            "intent": "blog",
            "tone": "professional",
            "model": "gemini-2.0-flash-exp"
        }
    )
    
    if gen_response.status_code != 200:
        print(f"❌ Generation failed: {gen_response.status_code}")
        return
    
    gen_data = gen_response.json()
    original_content = gen_data.get("content")
    original_image = gen_data.get("image_url")
    
    print(f"✅ Generated content: {len(original_content)} chars")
    print(f"✅ Generated image: {original_image[:60] if original_image else 'None'}...")
    
    # Step 2: Create checkpoint (save everything)
    print("\n💾 Step 2: Create checkpoint v1 (saving content + image)...")
    
    checkpoint_response = requests.post(
        f"{BASE_URL}/checkpoints/create",
        json={
            "conversation_id": CONVERSATION_ID,
            "user_id": USER_ID,
            "title": "Quantum Computing - First Draft",
            "content": original_content,
            "image_url": original_image,  # ⭐ Image is saved!
            "description": "Initial version with AI-generated image",
            "tone": "professional",
            "context_snapshot": {
                "messages": [],
                "chat_messages": [],
                "current_blog_content": original_content,
                "current_blog_image": original_image,  # ⭐ Image in context too!
                "timestamp": "2026-01-11T12:00:00Z"
            }
        }
    )
    
    if checkpoint_response.status_code != 200:
        print(f"❌ Checkpoint creation failed: {checkpoint_response.status_code}")
        return
    
    checkpoint_data = checkpoint_response.json()
    checkpoint_id = checkpoint_data["id"]
    
    print(f"✅ Checkpoint v{checkpoint_data['version_number']} created")
    print(f"   ID: {checkpoint_id}")
    print(f"   Title: {checkpoint_data['title']}")
    print(f"   Has image: {'Yes' if checkpoint_data.get('image_url') else 'No'}")
    
    # Step 3: Simulate user making edits (in real app, they'd edit in UI)
    print("\n✏️  Step 3: User makes changes (simulated)...")
    print("   - Changed some paragraphs")
    print("   - Added new sections")
    print("   - Different image generated")
    
    # Step 4: List checkpoints
    print("\n📋 Step 4: List all checkpoints...")
    list_response = requests.get(
        f"{BASE_URL}/checkpoints/list/{CONVERSATION_ID}",
        params={"user_id": USER_ID}
    )
    
    if list_response.status_code == 200:
        checkpoints = list_response.json()
        print(f"✅ Found {len(checkpoints)} checkpoint(s):")
        for cp in checkpoints:
            print(f"   v{cp['version_number']}: {cp['title']}")
            print(f"      - Image: {'✓' if cp.get('image_url') else '✗'}")
            print(f"      - Active: {'✓' if cp['is_active'] else '✗'}")
    
    # Step 5: Restore checkpoint (go back to previous work)
    print("\n⏮️  Step 5: Restore checkpoint v1 (going back to previous work)...")
    restore_response = requests.post(
        f"{BASE_URL}/checkpoints/{checkpoint_id}/restore",
        params={"user_id": USER_ID, "conversation_id": CONVERSATION_ID}
    )
    
    if restore_response.status_code == 200:
        restored_data = restore_response.json()
        print(f"✅ {restored_data.get('message', 'Checkpoint restored!')}")
        print(f"\n📄 Restored content preview:")
        print(f"   {restored_data['content'][:200]}...")
        print(f"\n🖼️  Restored image:")
        print(f"   {restored_data.get('image_url', 'None')[:80]}...")
        print(f"\n💬 Chat history restored: {'Yes' if restored_data.get('context_snapshot') else 'No'}")
        
        # Now user can:
        # - See original content
        # - See original image
        # - Continue from where they were
        # - Make new checkpoint for new branch
        
    else:
        print(f"❌ Restore failed: {restore_response.status_code}")
    
    print("\n" + "="*60)
    print("✅ DEMO COMPLETE!")
    print("\nWhat you learned:")
    print("  ✓ Checkpoints save content + images + chat history")
    print("  ✓ You can go back to any previous version")
    print("  ✓ Everything is restored: text, image, context")
    print("  ✓ Simple workflow: Create → Edit → Restore")
    print("="*60)

if __name__ == "__main__":
    demo_checkpoint_workflow()
