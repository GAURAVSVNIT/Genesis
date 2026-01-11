"""
Test script for image posting to LinkedIn and Twitter.

Tests:
1. Generate content with image
2. Post to LinkedIn with image
3. Post to Twitter with image
"""

import requests
import json

BASE_URL = "http://localhost:8000/v1"

# Test user ID (replace with actual)
USER_ID = "test-user-123"

def test_generate_content_with_image():
    """Generate blog content with image."""
    print("\n" + "="*60)
    print("TEST 1: Generate Content with Image")
    print("="*60)
    
    response = requests.post(
        f"{BASE_URL}/content/generate",
        json={
            "prompt": "Write about the future of AI in healthcare",
            "intent": "blog",
            "tone": "professional",
            "model": "gemini-2.0-flash-exp",
            "max_words": 500
        }
    )
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Content generated")
        print(f"   Content length: {len(data.get('content', ''))} chars")
        print(f"   Image URL: {data.get('image_url', 'None')[:80]}...")
        print(f"   Model: {data.get('model')}")
        print(f"   Image Model: {data.get('image_model')}")
        return data.get('content'), data.get('image_url')
    else:
        print(f"❌ Failed: {response.status_code}")
        print(response.text)
        return None, None

def test_post_to_linkedin_with_image(content: str, image_url: str):
    """Post content with image to LinkedIn."""
    print("\n" + "="*60)
    print("TEST 2: Post to LinkedIn with Image")
    print("="*60)
    
    if not image_url:
        print("⚠️  No image URL available, posting text only")
    
    # Truncate content for social media
    short_content = content[:1000] + "..." if len(content) > 1000 else content
    
    response = requests.post(
        f"{BASE_URL}/social/share",
        params={"user_id": USER_ID},
        json={
            "platform": "linkedin",
            "content": short_content,
            "title": "AI in Healthcare",
            "image_url": image_url
        }
    )
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Posted to LinkedIn")
        print(f"   Status: {data.get('status')}")
        print(f"   Response: {json.dumps(data.get('platform_response', {}), indent=2)}")
    else:
        print(f"❌ Failed: {response.status_code}")
        print(response.text)

def test_post_to_twitter_with_image(content: str, image_url: str):
    """Post content with image to Twitter."""
    print("\n" + "="*60)
    print("TEST 3: Post to Twitter with Image")
    print("="*60)
    
    if not image_url:
        print("⚠️  No image URL available, posting text only")
    
    # Truncate for Twitter (280 char limit)
    tweet_text = content[:250] + "..." if len(content) > 250 else content
    
    response = requests.post(
        f"{BASE_URL}/social/share",
        params={"user_id": USER_ID},
        json={
            "platform": "twitter",
            "content": tweet_text,
            "image_url": image_url
        }
    )
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Posted to Twitter")
        print(f"   Status: {data.get('status')}")
        print(f"   Response: {json.dumps(data.get('platform_response', {}), indent=2)}")
    else:
        print(f"❌ Failed: {response.status_code}")
        print(response.text)

def test_external_image():
    """Test posting with external image URL."""
    print("\n" + "="*60)
    print("TEST 4: Post with External Image")
    print("="*60)
    
    external_image = "https://images.unsplash.com/photo-1485827404703-89b55fcc595e"
    content = "Check out this amazing technology! 🚀"
    
    response = requests.post(
        f"{BASE_URL}/social/share",
        params={"user_id": USER_ID},
        json={
            "platform": "linkedin",
            "content": content,
            "title": "Technology Update",
            "image_url": external_image
        }
    )
    
    if response.status_code == 200:
        print(f"✅ Posted external image to LinkedIn")
    else:
        print(f"❌ Failed: {response.status_code}")

def main():
    print("\n🚀 Testing Image Support in Social Posting")
    print("Make sure you have:")
    print("  1. Backend running")
    print("  2. LinkedIn/Twitter connected for test user")
    print("  3. Valid OAuth tokens")
    
    # Test 1: Generate content with image
    content, image_url = test_generate_content_with_image()
    
    if not content:
        print("\n⚠️  Content generation failed. Testing with sample data...")
        content = "The future of AI in healthcare is promising. AI will revolutionize diagnostics, treatment, and patient care."
        image_url = "https://images.unsplash.com/photo-1576091160399-112ba8d25d1d"
    
    # Test 2: Post to LinkedIn
    test_post_to_linkedin_with_image(content, image_url)
    
    # Test 3: Post to Twitter  
    test_post_to_twitter_with_image(content, image_url)
    
    # Test 4: External image
    test_external_image()
    
    print("\n" + "="*60)
    print("✅ All tests completed!")
    print("="*60)

if __name__ == "__main__":
    main()
