"""
Test script for checkpoint and context system
"""
import asyncio
import httpx
import json
from datetime import datetime

BASE_URL = "http://localhost:8000"

async def test_checkpoint_system():
    """Test complete checkpoint workflow"""
    
    print("=" * 60)
    print("CHECKPOINT & CONTEXT SYSTEM TEST")
    print("=" * 60)
    
    test_user_id = "test_user_123"
    test_conversation_id = "conv_123"
    
    async with httpx.AsyncClient() as client:
        
        # Test 1: Save Context
        print("\n1. Testing Save Context...")
        save_context_payload = {
            "conversation_id": test_conversation_id,
            "user_id": test_user_id,
            "messages": [
                {
                    "id": "msg1",
                    "role": "user",
                    "content": "Write a blog about AI",
                    "type": "blog",
                    "timestamp": datetime.now().isoformat(),
                    "tone": "informative",
                    "length": "medium"
                },
                {
                    "id": "msg2",
                    "role": "assistant",
                    "content": "# AI Blog Post\n\nArtificial Intelligence is transforming...",
                    "type": "blog",
                    "timestamp": datetime.now().isoformat(),
                    "tone": "informative",
                    "length": "medium"
                }
            ],
            "chat_messages": [
                {
                    "id": "chat1",
                    "role": "user",
                    "content": "Make it more professional",
                    "type": "chat",
                    "timestamp": datetime.now().isoformat()
                }
            ],
            "current_blog_content": "# AI Blog Post\n\nArtificial Intelligence is transforming..."
        }
        
        try:
            response = await client.post(
                f"{BASE_URL}/v1/context/save",
                json=save_context_payload
            )
            print(f"✓ Save Context: {response.status_code}")
            print(f"  Response: {response.json()}")
        except Exception as e:
            print(f"✗ Save Context Error: {e}")
            return
        
        # Test 2: Load Context
        print("\n2. Testing Load Context...")
        try:
            response = await client.get(
                f"{BASE_URL}/v1/context/load/{test_conversation_id}?user_id={test_user_id}"
            )
            print(f"✓ Load Context: {response.status_code}")
            loaded_context = response.json()
            print(f"  Messages count: {loaded_context.get('message_count')}")
            print(f"  Blog content length: {len(loaded_context.get('current_blog_content', ''))}")
        except Exception as e:
            print(f"✗ Load Context Error: {e}")
            return
        
        # Test 3: Create Checkpoint
        print("\n3. Testing Create Checkpoint...")
        checkpoint_payload = {
            "conversation_id": test_conversation_id,
            "user_id": test_user_id,
            "title": "Blog Version 1",
            "content": "# AI Blog Post\n\nArtificial Intelligence is transforming the world...",
            "description": "Initial version with professional tone",
            "tone": "informative",
            "length": "medium",
            "context_snapshot": {
                "chatContext": [
                    {
                        "id": "chat1",
                        "role": "user",
                        "content": "Write a blog about AI",
                        "timestamp": datetime.now().isoformat(),
                        "tone": "informative"
                    }
                ],
                "timestamp": datetime.now().isoformat()
            }
        }
        
        checkpoint_id = None
        try:
            response = await client.post(
                f"{BASE_URL}/v1/checkpoints/create",
                json=checkpoint_payload
            )
            print(f"✓ Create Checkpoint: {response.status_code}")
            checkpoint_response = response.json()
            checkpoint_id = checkpoint_response.get('id')
            print(f"  Checkpoint ID: {checkpoint_id}")
            print(f"  Version: {checkpoint_response.get('version_number')}")
            print(f"  Is Active: {checkpoint_response.get('is_active')}")
        except Exception as e:
            print(f"✗ Create Checkpoint Error: {e}")
            return
        
        # Test 4: List Checkpoints
        print("\n4. Testing List Checkpoints...")
        try:
            response = await client.get(
                f"{BASE_URL}/v1/checkpoints/list/{test_conversation_id}?user_id={test_user_id}"
            )
            print(f"✓ List Checkpoints: {response.status_code}")
            checkpoints = response.json()
            print(f"  Total checkpoints: {len(checkpoints)}")
            for cp in checkpoints:
                print(f"    - {cp.get('title')} (v{cp.get('version_number')}) - Active: {cp.get('is_active')}")
        except Exception as e:
            print(f"✗ List Checkpoints Error: {e}")
            return
        
        # Test 5: Create Another Checkpoint (to test version incrementation)
        print("\n5. Testing Create Second Checkpoint...")
        checkpoint_payload['title'] = "Blog Version 2"
        checkpoint_payload['content'] = "# AI Blog Post - Updated\n\nArtificial Intelligence is transforming..."
        checkpoint_payload['description'] = "Second version with more details"
        
        try:
            response = await client.post(
                f"{BASE_URL}/v1/checkpoints/create",
                json=checkpoint_payload
            )
            print(f"✓ Create Second Checkpoint: {response.status_code}")
            checkpoint_response = response.json()
            print(f"  Checkpoint ID: {checkpoint_response.get('id')}")
            print(f"  Version: {checkpoint_response.get('version_number')}")
        except Exception as e:
            print(f"✗ Create Second Checkpoint Error: {e}")
        
        # Test 6: Get Specific Checkpoint
        if checkpoint_id:
            print(f"\n6. Testing Get Checkpoint {checkpoint_id[:8]}...")
            try:
                response = await client.get(
                    f"{BASE_URL}/v1/checkpoints/{checkpoint_id}?user_id={test_user_id}"
                )
                print(f"✓ Get Checkpoint: {response.status_code}")
                cp = response.json()
                print(f"  Title: {cp.get('title')}")
                print(f"  Content preview: {cp.get('content')[:50]}...")
            except Exception as e:
                print(f"✗ Get Checkpoint Error: {e}")
        
        # Test 7: List checkpoints again to verify versions
        print("\n7. Testing List Checkpoints (Final)...")
        try:
            response = await client.get(
                f"{BASE_URL}/v1/checkpoints/list/{test_conversation_id}?user_id={test_user_id}"
            )
            checkpoints = response.json()
            print(f"✓ List Checkpoints: {response.status_code}")
            print(f"  Total checkpoints: {len(checkpoints)}")
            for cp in checkpoints:
                print(f"    - {cp.get('title')} (v{cp.get('version_number')}) - Active: {cp.get('is_active')}")
        except Exception as e:
            print(f"✗ List Checkpoints Error: {e}")
        
        # Test 8: Restore Checkpoint (if we have at least 2)
        if len(checkpoints) >= 2:
            print("\n8. Testing Restore Checkpoint...")
            first_checkpoint = checkpoints[-1]  # Get first one (oldest)
            try:
                response = await client.post(
                    f"{BASE_URL}/v1/checkpoints/{first_checkpoint.get('id')}/restore",
                    params={"user_id": test_user_id, "conversation_id": test_conversation_id}
                )
                print(f"✓ Restore Checkpoint: {response.status_code}")
                restore_response = response.json()
                print(f"  Status: {restore_response.get('status')}")
                print(f"  Restored version: {restore_response.get('version')}")
                print(f"  Content preview: {restore_response.get('content')[:50]}...")
            except Exception as e:
                print(f"✗ Restore Checkpoint Error: {e}")
        
        # Test 9: Delete Checkpoint
        if checkpoint_id:
            print(f"\n9. Testing Delete Checkpoint...")
            try:
                response = await client.delete(
                    f"{BASE_URL}/v1/checkpoints/{checkpoint_id}?user_id={test_user_id}"
                )
                print(f"✓ Delete Checkpoint: {response.status_code}")
                print(f"  Response: {response.json()}")
            except Exception as e:
                print(f"✗ Delete Checkpoint Error: {e}")
    
    print("\n" + "=" * 60)
    print("TEST COMPLETE")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(test_checkpoint_system())
