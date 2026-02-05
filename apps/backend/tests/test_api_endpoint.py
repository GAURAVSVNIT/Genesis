"""
Test the actual guest chat API endpoint
"""

import asyncio
import json
import uuid
from datetime import datetime
from fastapi.testclient import TestClient
from main import app

def test_api_endpoint():
    """Test the /v1/guest/chat/{guest_id} POST endpoint"""
    
    print("=" * 60)
    print("TESTING GUEST CHAT API ENDPOINT")
    print("=" * 60)
    
    client = TestClient(app)
    
    guest_id = str(uuid.uuid4())
    print(f"\nGuest ID: {guest_id}")
    
    message_payload = {
        "role": "user",
        "content": "This is a test message from the API",
        "timestamp": datetime.utcnow().isoformat()
    }
    
    print(f"Message: {json.dumps(message_payload, indent=2)}")
    
    try:
        # Test POST - save message
        print("\n[TEST 1] POST /v1/guest/chat/{guest_id}")
        print("-" * 60)
        
        response = client.post(
            f"/v1/guest/chat/{guest_id}",
            json=message_payload
        )
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.json()}")
        
        if response.status_code == 200:
            print("✅ Message saved successfully")
        else:
            print(f"❌ Failed to save message: {response.text}")
        
        # Test GET - retrieve history
        print("\n[TEST 2] GET /v1/guest/chat/{guest_id}")
        print("-" * 60)
        
        response = client.get(f"/v1/guest/chat/{guest_id}")
        
        print(f"Status Code: {response.status_code}")
        history = response.json()
        print(f"History items: {len(history)}")
        
        if history:
            for i, msg in enumerate(history, 1):
                print(f"\nMessage {i}:")
                print(f"  Role: {msg['role']}")
                print(f"  Content: {msg['content']}")
        else:
            print("⚠️ No messages in history")
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_api_endpoint()
