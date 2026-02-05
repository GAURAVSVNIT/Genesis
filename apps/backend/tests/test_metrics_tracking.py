"""
Test script to verify cache metrics tracking is working.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi.testclient import TestClient
from main import app
from database.database import SessionLocal
from database.models.cache import CacheMetrics
import json
import time

client = TestClient(app)
db = SessionLocal()

def test_metrics_tracking():
    """Test that cache hits/misses are being recorded."""
    
    print("\n" + "="*60)
    print("CACHE METRICS TRACKING TEST")
    print("="*60)
    
    # Generate a test guest ID
    guest_id = "test-metrics-guest"
    
    # Clear any existing data
    try:
        from core.upstash_redis import RedisManager
        redis = RedisManager.get_instance()
        redis.delete(f"guest:{guest_id}")
        print(f"[CLEANUP] Cleared Redis cache for {guest_id}")
    except:
        pass
    
    print("\n1. POST new message (should create new conversation & message)")
    response = client.post(
        f"/v1/guest/chat/{guest_id}",
        json={
            "role": "user",
            "content": "Test message for metrics tracking",
            "timestamp": datetime.utcnow().isoformat()
        }
    )
    print(f"   Status: {response.status_code}")
    print(f"   Response: {response.json()}")
    
    # Give it a moment for the commit
    time.sleep(0.5)
    
    print("\n2. GET history (should be CACHE HIT)")
    response = client.get(f"/v1/guest/chat/{guest_id}")
    print(f"   Status: {response.status_code}")
    print(f"   Retrieved {len(response.json())} messages")
    
    time.sleep(0.5)
    
    print("\n3. GET history again (should be CACHE HIT)")
    response = client.get(f"/v1/guest/chat/{guest_id}")
    print(f"   Status: {response.status_code}")
    print(f"   Retrieved {len(response.json())} messages")
    
    time.sleep(0.5)
    
    print("\n4. GET non-existent guest (should be CACHE MISS)")
    response = client.get(f"/v1/guest/chat/nonexistent-guest-12345")
    print(f"   Status: {response.status_code}")
    print(f"   Retrieved {len(response.json())} messages")
    
    # Now check the metrics
    time.sleep(1)
    
    print("\n" + "="*60)
    print("METRICS RECORDED IN cache_metrics TABLE")
    print("="*60)
    
    metrics_records = db.query(CacheMetrics).order_by(
        CacheMetrics.recorded_at.desc()
    ).limit(3).all()
    
    if not metrics_records:
        print("❌ NO METRICS RECORDS FOUND!")
        return
    
    for i, metric in enumerate(metrics_records):
        print(f"\n[Record {i+1}] Recorded at: {metric.recorded_at}")
        print(f"  - Cache Hits: {metric.cache_hits}")
        print(f"  - Cache Misses: {metric.cache_misses}")
        print(f"  - Total Requests: {metric.total_requests}")
        print(f"  - Hit Rate: {metric.hit_rate:.1f}%")
        print(f"  - Avg Response Time: {metric.avg_response_time:.2f}ms")
    
    # Expected: Should see hits from the GET requests
    latest = metrics_records[0]
    if latest.cache_hits > 0 or latest.cache_misses > 0:
        print("\n✅ METRICS TRACKING IS WORKING!")
        print(f"   Latest record shows {latest.cache_hits} hits, {latest.cache_misses} misses")
    else:
        print("\n❌ METRICS NOT BEING RECORDED")
    
    print("\n" + "="*60)

if __name__ == "__main__":
    from datetime import datetime
    test_metrics_tracking()
