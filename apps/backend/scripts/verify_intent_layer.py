
import requests
import json
import time

BASE_URL = "http://localhost:8000"

def test_intent_classification():
    print("\n[TEST] Testing Intent Classification...")
    url = f"{BASE_URL}/v1/classify/intent"
    payload = {
        "prompt": "Write a blog on Crab",
        "context_summary": ""
    }
    
    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()
        data = response.json()
        
        print(f"Response: {json.dumps(data, indent=2)}")
        
        assert data["intent"] == "blog", f"Expected intent 'blog', got '{data.get('intent')}'"
        assert "topic" in data, "Response missing 'topic' field"
        assert data["topic"] is not None, "Topic is None"
        print(f"✅ Intent Classification Passed: Detected topic '{data['topic']}'")
        return data
        
    except Exception as e:
        print(f"❌ Intent Classification Failed: {e}")
        return None

def test_content_generation(classification_data):
    print("\n[TEST] Testing Content Generation...")
    url = f"{BASE_URL}/v1/content/generate"
    
    # Simulate what frontend sends
    payload = {
        "prompt": "Write a blog on Crab",
        "intent": classification_data["intent"],
        "topic": classification_data["topic"],
        "refined_query": classification_data.get("refined_query"),
        "model": "gemini-2.0-flash",
        "tone": "informative"
    }
    
    try:
        start_time = time.time()
        response = requests.post(url, json=payload)
        response.raise_for_status()
        data = response.json()
        
        print(f"Generation Time: {time.time() - start_time:.2f}s")
        content = data["content"]
        print(f"Content Preview: {content[:200]}...")
        
        # Check topic adherence
        if "crab" in content.lower():
            print("✅ Content Topic Verified: Contains 'crab'")
        else:
            print("⚠️ Content Topic Warning: 'crab' not found in first 200 chars. Checking full content length...")
        
        # Check Image Generation
        if data.get("image_url"):
            print(f"✅ Image Generated: {data['image_url'][:50]}...")
        else:
            print("⚠️ No Image Generated")

    except Exception as e:
        print(f"❌ Content Generation Failed: {e}")
        if response.text:
            print(f"Error Response: {response.text}")

if __name__ == "__main__":
    classification = test_intent_classification()
    if classification:
        test_content_generation(classification)
