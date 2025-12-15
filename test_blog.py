import requests

response = requests.post(
    'http://localhost:8000/v1/blog/generate',
    json={
        "prompt": "test blog about redis",
        "tone": "informative", 
        "length": "short"
    }
)

print(f"Status: {response.status_code}")
print(f"Response: {response.text}")
