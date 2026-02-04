
import requests
import json

url = "http://localhost:8000/v1/context/save"
data = {
    "conversation_id": "test_conv_id",
    "user_id": "test_user_id",
    "messages": [],
    "chat_messages": []
}

try:
    print(f"Testing POST {url}...")
    response = requests.post(url, json=data)
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.text}")
except Exception as e:
    print(f"Error: {e}")
