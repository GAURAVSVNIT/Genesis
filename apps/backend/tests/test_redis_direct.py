"""
Direct test to check Redis connectivity and data storage
"""

from core.upstash_redis import RedisManager
import json
from datetime import datetime

print("=" * 60)
print("DIRECT REDIS TEST")
print("=" * 60)

try:
    redis = RedisManager.get_instance()
    print("✅ Redis connection established")
    
    # Test 1: Ping
    print("\n[TEST 1] Ping")
    pong = redis.ping()
    print(f"Ping response: {pong}")
    
    # Test 2: Set a simple key
    print("\n[TEST 2] Simple Key-Value")
    redis.set("test_key", "test_value")
    value = redis.get("test_key")
    print(f"Stored: 'test_value'")
    print(f"Retrieved: '{value}'")
    
    # Test 3: List operations (like guest chat)
    print("\n[TEST 3] List Operations (Like Guest Chat)")
    test_key = "guest:test-guest-123"
    test_data = {
        "role": "user",
        "content": "Hello world",
        "timestamp": datetime.utcnow().isoformat()
    }
    
    print(f"Pushing to key: {test_key}")
    result = redis.rpush(test_key, json.dumps(test_data))
    print(f"Push result: {result}")
    
    # Set expiration
    expire_result = redis.expire(test_key, 86400)
    print(f"Expire result: {expire_result}")
    
    # Retrieve
    retrieved = redis.lrange(test_key, 0, -1)
    print(f"Retrieved items: {len(retrieved)}")
    if retrieved:
        print(f"Content: {retrieved[0]}")
    
    # Test 4: List all keys
    print("\n[TEST 4] List All Keys in Redis")
    keys = redis.keys("*")
    print(f"Total keys in Redis: {len(keys)}")
    
    guest_keys = [k for k in keys if "guest" in str(k).lower()]
    print(f"Guest-related keys: {len(guest_keys)}")
    
    if guest_keys:
        print("Guest keys found:")
        for k in guest_keys:
            print(f"  - {k}")
    else:
        print("❌ No guest keys found in Redis!")
    
    # Test 5: Check database info
    print("\n[TEST 5] Redis Info")
    try:
        info = redis.info()
        if info:
            print(f"Redis is responsive: {type(info)}")
            if isinstance(info, dict):
                print(f"  Keys in info: {list(info.keys())[:5]}...")
        else:
            print("⚠️ Info returned empty")
    except Exception as e:
        print(f"⚠️ Could not get info: {e}")
    
    print("\n" + "=" * 60)
    print("✅ REDIS TEST COMPLETE")
    print("=" * 60)
    
except Exception as e:
    print(f"❌ Error: {str(e)}")
    import traceback
    traceback.print_exc()
