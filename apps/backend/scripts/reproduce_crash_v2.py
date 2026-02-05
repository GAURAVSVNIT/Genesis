import requests
import json
import traceback

print("Attempting to reproduce crash on http://localhost:8000/v1/content/generate")

url = "http://localhost:8000/v1/content/generate"
payload = {
    "prompt": "Test blog post about AI",
    "tone": "professional",
    "length": "medium",  # This might be the issue if validation rejects it?
    "guestId": "test-guest-id",
    "include_critique": True,
    "include_alternatives": True,
    "include_implications": True,
    "format": "markdown"
}

try:
    print(f"Sending payload: {json.dumps(payload, indent=2)}")
    response = requests.post(url, json=payload, timeout=30)
    
    print(f"Status Code: {response.status_code}")
    print("Response Body:")
    try:
        print(json.dumps(response.json(), indent=2))
    except:
        print(response.text)
        
except Exception:
    traceback.print_exc()
