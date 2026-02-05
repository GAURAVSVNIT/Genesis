"""
Test script to verify cache_migrations tracking is working.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi.testclient import TestClient
from main import app
from database.database import SessionLocal
from database.models.cache import CacheMigration
from datetime import datetime

client = TestClient(app)
db = SessionLocal()

def test_migration_tracking():
    """Test that migrations are being recorded in cache_migrations."""
    
    print("\n" + "="*60)
    print("CACHE MIGRATIONS TRACKING TEST")
    print("="*60)
    
    # Create a test guest session first
    guest_id = "test-migration-guest"
    
    print("\n1. Create guest chat session")
    response = client.post(
        f"/v1/guest/chat/{guest_id}",
        json={
            "role": "user",
            "content": "Test message for migration",
            "timestamp": datetime.utcnow().isoformat()
        }
    )
    print(f"   Status: {response.status_code}")
    print(f"   Response: {response.json()}")
    
    print("\n2. Migrate guest session to authenticated user")
    response = client.post(
        f"/v1/guest/migrate/{guest_id}",
        json={"authenticated_user_id": "test-user-12345"}
    )
    print(f"   Status: {response.status_code}")
    print(f"   Response: {response.json()}")
    
    # Now check the migrations table
    print("\n" + "="*60)
    print("MIGRATIONS RECORDED IN cache_migrations TABLE")
    print("="*60)
    
    migrations = db.query(CacheMigration).order_by(
        CacheMigration.started_at.desc()
    ).limit(5).all()
    
    if not migrations:
        print("❌ NO MIGRATION RECORDS FOUND!")
        return
    
    for i, migration in enumerate(migrations):
        print(f"\n[Migration {i+1}] {migration.migration_type}")
        print(f"  - Status: {migration.status}")
        print(f"  - Records Migrated: {migration.records_migrated}")
        print(f"  - Records Failed: {migration.records_failed}")
        print(f"  - From: {migration.source} -> To: {migration.destination}")
        print(f"  - Started: {migration.started_at}")
        print(f"  - Completed: {migration.completed_at}")
        print(f"  - Notes: {migration.notes}")
    
    # Check if latest migration is recorded
    latest = migrations[0]
    if latest.migration_type == "guest_to_user" and latest.status == "completed":
        print("\n[SUCCESS] MIGRATION TRACKING IS WORKING!")
        print(f"   Migration recorded: {latest.records_migrated} records migrated")
    else:
        print("\n[INFO] Latest migration may not be from this test")
    
    print("\n" + "="*60)

if __name__ == "__main__":
    test_migration_tracking()
