"""
Test the improved regenerate-image endpoint with various scenarios.
"""
import requests
import json

BASE_URL = "http://localhost:8000/v1/content"

# Sample blog content
SAMPLE_CONTENT = """
Revolutionizing Cloud Computing with AI

Artificial intelligence is transforming how we approach cloud infrastructure. 
Modern enterprises are leveraging machine learning algorithms to optimize 
resource allocation and reduce costs by up to 40%.

The integration of AI-powered automation tools enables real-time scaling 
and predictive maintenance, ensuring maximum uptime and performance.
"""

def test_basic_regeneration():
    """Test basic regeneration without preferences."""
    print("\n" + "="*60)
    print("TEST 1: Basic Regeneration (Auto-detect tone)")
    print("="*60)
    
    response = requests.post(
        f"{BASE_URL}/regenerate-image",
        json={"content": SAMPLE_CONTENT}
    )
    
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Image URL: {data.get('image_url', 'N/A')[:80]}...")
    else:
        print(f"❌ Error: {response.text}")

def test_with_style_preference():
    """Test with specific style preference."""
    print("\n" + "="*60)
    print("TEST 2: With Style Preference (Minimalist)")
    print("="*60)
    
    response = requests.post(
        f"{BASE_URL}/regenerate-image",
        json={
            "content": SAMPLE_CONTENT,
            "style_preference": "minimalist",
            "tone": "technical"
        }
    )
    
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Image URL: {data.get('image_url', 'N/A')[:80]}...")
    else:
        print(f"❌ Error: {response.text}")

def test_with_focus_and_exclusions():
    """Test with specific focus and exclusions."""
    print("\n" + "="*60)
    print("TEST 3: With Focus & Exclusions")
    print("="*60)
    
    response = requests.post(
        f"{BASE_URL}/regenerate-image",
        json={
            "content": SAMPLE_CONTENT,
            "style_preference": "cinematic",
            "specific_focus": "cloud servers and network visualization",
            "exclude_elements": ["people", "text", "logos"],
            "variation_level": "high",
            "tone": "professional"
        }
    )
    
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Image URL: {data.get('image_url', 'N/A')[:80]}...")
    else:
        print(f"❌ Error: {response.text}")

def test_casual_content():
    """Test with casual blog content."""
    print("\n" + "="*60)
    print("TEST 4: Casual Content (Auto-detect)")
    print("="*60)
    
    casual_content = """
    10 Amazing Travel Hacks You Need to Try!
    
    Hey there, fellow wanderers! Ready to level up your travel game? 
    Check out these awesome tips that'll make your next adventure way more fun!
    
    From packing hacks to finding hidden gems, we've got you covered!
    """
    
    response = requests.post(
        f"{BASE_URL}/regenerate-image",
        json={
            "content": casual_content,
            "style_preference": "illustration",
            "variation_level": "medium"
        }
    )
    
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Image URL: {data.get('image_url', 'N/A')[:80]}...")
        print(f"   (Should detect 'casual' tone automatically)")
    else:
        print(f"❌ Error: {response.text}")

def main():
    print("\n🚀 Testing Improved Regenerate Image Endpoint")
    print("Make sure the backend is running on localhost:8000")
    
    try:
        # Test if backend is running
        response = requests.get(f"{BASE_URL.rsplit('/', 1)[0]}/health", timeout=2)
        if response.status_code != 200:
            print("⚠️  Backend may not be running properly")
    except requests.exceptions.RequestException:
        print("❌ Backend is not running! Start it first:")
        print("   cd apps/backend && uv run uvicorn main:app --reload")
        return
    
    # Run tests
    test_basic_regeneration()
    test_with_style_preference()
    test_with_focus_and_exclusions()
    test_casual_content()
    
    print("\n" + "="*60)
    print("✅ All tests completed!")
    print("="*60)

if __name__ == "__main__":
    main()
