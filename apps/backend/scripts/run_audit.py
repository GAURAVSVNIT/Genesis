#!/usr/bin/env python3
"""Quick database audit - no emoji issues"""

from sqlalchemy import inspect
from database.database import engine, SessionLocal
from database.models import *

def audit():
    db = SessionLocal()
    inspector = inspect(engine)
    
    print("\n" + "="*80)
    print("DATABASE AUDIT - TABLE VERIFICATION")
    print("="*80 + "\n")
    
    required_tables = {
        # Core
        "users": ["id", "email", "username"],
        "conversations": ["id", "user_id", "title"],
        "messages": ["id", "conversation_id", "role"],
        
        # Content
        "generated_content": ["id", "user_id", "seo_score"],
        "content_embeddings": ["id", "content_id"],
        
        # Advanced (NEW)
        "content_versions": ["id", "content_id", "version_number"],
        "message_feedback": ["id", "message_id", "user_id"],
        "rag_sources": ["id", "message_id"],
        "conversation_context": ["id", "conversation_id"],
        
        # Analytics
        "usage_metrics": ["id", "user_id"],
        "activity_logs": ["id", "user_id"],
    }
    
    existing = set(inspector.get_table_names())
    
    print("TABLE STATUS:\n")
    ok_count = 0
    for table, required_cols in required_tables.items():
        if table in existing:
            actual_cols = {c['name'] for c in inspector.get_columns(table)}
            missing = set(required_cols) - actual_cols
            if missing:
                print(f"[OK] {table} - has {len(actual_cols)} columns (missing: {missing})")
            else:
                print(f"[OK] {table} - {len(actual_cols)} columns")
                ok_count += 1
        else:
            print(f"[MISSING] {table}")
    
    print(f"\n{'-'*80}")
    print(f"Result: {ok_count}/{len(required_tables)} tables OK")
    print(f"Total DB tables: {len(existing)}")
    print(f"Actual tables: {sorted(existing)}")
    
    # Try to verify data can be inserted
    print(f"\n{'-'*80}")
    print("DATA INSERTION TEST:\n")
    
    import uuid
    try:
        # Test user insertion
        test_user = User(
            id=str(uuid.uuid4()),
            email=f"audit_test_{uuid.uuid4().hex[:6]}@test.com",
            username=f"audit_test_{uuid.uuid4().hex[:6]}",
            password_hash="test_hash",
            status="active"
        )
        db.add(test_user)
        db.commit()
        print(f"[OK] User insertion - ID: {test_user.id[:8]}...")
        
        # Test conversation
        test_conv = Conversation(
            id=str(uuid.uuid4()),
            user_id=test_user.id,
            title="Audit Test",
            status="active"
        )
        db.add(test_conv)
        db.commit()
        print(f"[OK] Conversation insertion")
        
        # Test message
        test_msg = Message(
            id=str(uuid.uuid4()),
            conversation_id=test_conv.id,
            user_id=test_user.id,
            role="user",
            content="test",
            message_index=1
        )
        db.add(test_msg)
        db.commit()
        print(f"[OK] Message insertion")
        
        # Clean up
        db.delete(test_msg)
        db.delete(test_conv)
        db.delete(test_user)
        db.commit()
        print(f"[OK] Cleanup successful")
        
    except Exception as e:
        print(f"[ERROR] {str(e)}")
    finally:
        db.close()
    
    print(f"\n{'='*80}")
    print("AUDIT COMPLETE")
    print(f"{'='*80}\n")

if __name__ == "__main__":
    audit()
