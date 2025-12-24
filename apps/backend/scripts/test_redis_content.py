
import requests
import redis
import json
import uuid
import time
import os

# Configuration
API_URL = "http://localhost:8000/v1/content/generate"
GUEST_ID = str(uuid.uuid4())
PROMPT = "Write a short haiku about debugging."

def test_content_generation():
    print(f"Testing Content Generation with Guest ID: {GUEST_ID}")
    
    payload = {
        "prompt": PROMPT,
        "safety_level": "moderate",
        "guestId": GUEST_ID
    }
    
    try:
        response = requests.post(API_URL, json=payload)
        response.raise_for_status()
        result = response.json()
        print("API Response Received:")
        print(json.dumps(result, indent=2))
        
        return True
    except Exception as e:
        print(f"API Request Failed: {e}")
        if hasattr(e, 'response') and e.response:
             print(e.response.text)
        return False

def check_redis():
    # We can't easily check remote Redis (Upstash) without credentials from here 
    # unless we use the backend's RedisManager.
    # So instead, we will rely on the backend logs or checking the API side effects.
    # But wait, we can try to use the python redis client if we have the URL.
    # For now, let's trust the API response success first, and maybe add a check endpoint to the backend?
    pass

if __name__ == "__main__":
    if test_content_generation():
        print("\nAPI call successful. Please check your Upstash dashboard or backend logs for:")
        print(f"Key: guest:{GUEST_ID}")
