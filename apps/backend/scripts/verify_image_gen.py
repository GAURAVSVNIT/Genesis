import requests
import json
import time

URL = "http://localhost:8000/v1/content/generate"
PAYLOAD = {
    "prompt": "Write a blog on Mindbend",
    "safety_level": "moderate",
    "guestId": "verifier-001",
    "tone": "informative"
}

try:
    print(f"Sending request to {URL}...")
    start = time.time()
    response = requests.post(URL, json=PAYLOAD)
    elapsed = time.time() - start
    
    print(f"Status Code: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"Success: {data.get('success')}")
        print(f"Cached: {data.get('cached')}")
        print(f"Image URL: {data.get('image_url')}")
        
        if data.get('image_url'):
            print("✅ PASS: Image URL found!")
        else:
            print("❌ FAIL: Image URL is null.")
            
        if data.get('cached'):
            print("ℹ️ Note: Response was cached.")
    else:
        print(f"Error: {response.text}")

except Exception as e:
    print(f"Exception: {e}")
