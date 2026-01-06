
import requests
import json

url = "http://localhost:8000/v1/content/regenerate-image"
payload = {
    "content": "A blog post about artificial intelligence and the future of coding."
}
headers = {
    "Content-Type": "application/json"
}

try:
    print(f"Sending request to {url}...")
    response = requests.post(url, json=payload, headers=headers)
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.text}")
except Exception as e:
    print(f"Request failed: {e}")
