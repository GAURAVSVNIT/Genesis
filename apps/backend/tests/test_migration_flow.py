#!/usr/bin/env python
"""
Verify and test the guest-to-user migration flow during login/signup.
This script validates that guest conversations are properly migrated when users authenticate.
"""

from database.database import SessionLocal
from database.models.cache import ConversationCache, MessageCache, CacheMigration
from datetime import datetime
import uuid
import json
import hashlib
import sys

def create_test_guest_session():
    """Create a test guest session with conversations and messages."""
    print("=" * 80)
    print("TESTING GUEST-TO-USER MIGRATION FLOW")
    print("=" * 80)
    print()
    
    db = SessionLocal()
    
    try:
        guest_id = str(uuid.uuid4())
        session_id = str(uuid.uuid4())
        
        print(f"[1] Creating test guest session...")
        print(f"    Guest ID: {guest_id}")
        print(f"    Session ID: {session_id}")
        print()
        
        conv1_id = str(uuid.uuid4())
        conv1_hash = hashlib.sha256(guest_id.encode()).hexdigest()[:64]
        
        conversation1 = ConversationCache(
            id=conv1_id,
            user_id=guest_id,
            session_id=session_id,
            title="First Guest Conversation",
            conversation_hash=conv1_hash,
            message_count=0,
            platform="guest",
            tone="neutral",
            migration_version="1.0"
        )
        db.add(conversation1)
        db.flush()
        
        for i in range(3):
            msg_hash = hashlib.md5(f"Message {i}".encode()).hexdigest()
            message = MessageCache(
                id=str(uuid.uuid4()),
                conversation_id=conv1_id,
                role="user" if i % 2 == 0 else "assistant",
                content=f"Test message {i}",
                message_hash=msg_hash,
                tokens=3,
                sequence=i,
                migration_version="1.0"
            )
            db.add(message)
        
        db.flush()
        print(f"    [OK] Created conversation 1 with 3 messages")
        
        conv2_id = str(uuid.uuid4())
        conversation2 = ConversationCache(
            id=conv2_id,
            user_id=guest_id,
            session_id=str(uuid.uuid4()),
            title="Second Guest Conversation",
            conversation_hash=hashlib.sha256(f"{guest_id}_2".encode()).hexdigest()[:64],
            message_count=0,
            platform="guest",
            tone="friendly",
            migration_version="1.0"
        )
        db.add(conversation2)
        db.flush()
        
        for i in range(2):
            msg_hash = hashlib.md5(f"Message {i} - Conv2".encode()).hexdigest()
            message = MessageCache(
                id=str(uuid.uuid4()),
                conversation_id=conv2_id,
                role="user" if i % 2 == 0 else "assistant",
                content=f"Test message {i} from conversation 2",
                message_hash=msg_hash,
                tokens=4,
                sequence=i,
                migration_version="1.0"
            )
            db.add(message)
        
        db.commit()
        print(f"    [OK] Created conversation 2 with 2 messages")
        print()
        
        print("[2] Verifying guest data before migration...")
        print()
        
        guest_conversations = db.query(ConversationCache).filter_by(
            user_id=guest_id,
            platform="guest"
        ).all()
        
        total_messages = 0
        for conv in guest_conversations:
            messages = db.query(MessageCache).filter_by(conversation_id=conv.id).all()
            print(f"    Conversation: {conv.title}")
            print(f"      Messages: {len(messages)}")
            print(f"      Platform: {conv.platform}")
            print(f"      User ID: {conv.user_id}")
            total_messages += len(messages)
        
        print()
        print(f"    Total guest conversations: {len(guest_conversations)}")
        print(f"    Total messages: {total_messages}")
        print()
        
        return guest_id, session_id, len(guest_conversations), total_messages
        
    except Exception as e:
        print(f"ERROR: Failed to create test guest session: {e}")
        db.rollback()
        db.close()
        return None, None, None, None
    finally:
        db.close()

def simulate_login_migration(guest_id: str):
    """Simulate the migration that happens during login/signup."""
    print("[3] Simulating login/signup - migrating guest to authenticated user...")
    print()
    
    db = SessionLocal()
    authenticated_user_id = str(uuid.uuid4())
    
    try:
        print(f"    Authenticated User ID: {authenticated_user_id}")
        print()
        
        guest_conversations = db.query(ConversationCache).filter_by(
            user_id=guest_id,
            platform="guest"
        ).all()
        
        if not guest_conversations:
            print("    [WARNING] No guest conversations to migrate")
            print()
            return authenticated_user_id
        
        print(f"    Found {len(guest_conversations)} guest conversations to migrate")
        print()
        
        conversations_migrated = 0
        messages_migrated = 0
        
        for guest_conv in guest_conversations:
            print(f"    Migrating: {guest_conv.title}")
            
            guest_conv.user_id = authenticated_user_id
            guest_conv.platform = "authenticated"
            
            guest_messages = db.query(MessageCache).filter_by(
                conversation_id=guest_conv.id
            ).all()
            
            for guest_msg in guest_messages:
                if not guest_msg.message_hash:
                    guest_msg.message_hash = hashlib.md5(guest_msg.content.encode()).hexdigest()
                messages_migrated += 1
            
            conversations_migrated += 1
            print(f"      [OK] Migrated {len(guest_messages)} messages")
        
        db.commit()
        
        print()
        print(f"    Migration Result:")
        print(f"      [OK] Conversations migrated: {conversations_migrated}")
        print(f"      [OK] Messages migrated: {messages_migrated}")
        print()
        
        migration_log = CacheMigration(
            id=str(uuid.uuid4()),
            version="1.0",
            migration_type="guest_to_user",
            status="completed",
            records_migrated=conversations_migrated + messages_migrated,
            records_failed=0,
            source="guest_session",
            destination="authenticated_user",
            notes=f"Migrated {conversations_migrated} conversations from guest {guest_id} to user {authenticated_user_id}",
            completed_at=datetime.utcnow()
        )
        db.add(migration_log)
        db.commit()
        
        return authenticated_user_id
        
    except Exception as e:
        print(f"    ERROR: Migration failed: {e}")
        db.rollback()
        return None
    finally:
        db.close()

def verify_migrated_data(guest_id: str, authenticated_user_id: str):
    """Verify that the data was properly migrated."""
    print("[4] Verifying migrated data...")
    print()
    
    db = SessionLocal()
    
    try:
        guest_conversations = db.query(ConversationCache).filter_by(
            user_id=guest_id,
            platform="guest"
        ).all()
        
        if guest_conversations:
            print(f"    [WARNING] Found {len(guest_conversations)} guest conversations still with guest platform")
            return False
        else:
            print(f"    [OK] No guest conversations with guest platform found")
        
        auth_conversations = db.query(ConversationCache).filter_by(
            user_id=authenticated_user_id,
            platform="authenticated"
        ).all()
        
        if not auth_conversations:
            print(f"    [ERROR] No authenticated conversations found for user {authenticated_user_id}")
            return False
        
        print(f"    [OK] Found {len(auth_conversations)} authenticated conversations")
        print()
        
        total_messages = 0
        for conv in auth_conversations:
            messages = db.query(MessageCache).filter_by(conversation_id=conv.id).all()
            print(f"    Conversation: {conv.title}")
            print(f"      Messages: {len(messages)}")
            print(f"      Platform: {conv.platform}")
            print(f"      User ID: {conv.user_id}")
            
            for msg in messages:
                if not msg.message_hash:
                    print(f"      [WARNING] Message {msg.id} has no hash!")
                    return False
            
            total_messages += len(messages)
        
        print()
        print(f"    [OK] All messages have proper hashes")
        print(f"    [OK] Total migrated messages: {total_messages}")
        print()
        
        return True
        
    except Exception as e:
        print(f"    ERROR: Verification failed: {e}")
        return False
    finally:
        db.close()

def cleanup_test_data(guest_id: str, authenticated_user_id: str):
    """Clean up test data."""
    print("[5] Cleaning up test data...")
    print()
    
    db = SessionLocal()
    
    try:
        auth_conversations = db.query(ConversationCache).filter_by(
            user_id=authenticated_user_id
        ).all()
        
        messages_deleted = 0
        for conv in auth_conversations:
            messages_deleted += db.query(MessageCache).filter_by(
                conversation_id=conv.id
            ).delete()
        
        conversations_deleted = db.query(ConversationCache).filter_by(
            user_id=authenticated_user_id
        ).delete()
        
        guest_conversations = db.query(ConversationCache).filter_by(
            user_id=guest_id
        ).all()
        
        for conv in guest_conversations:
            messages_deleted += db.query(MessageCache).filter_by(
                conversation_id=conv.id
            ).delete()
        
        guest_conv_deleted = db.query(ConversationCache).filter_by(
            user_id=guest_id
        ).delete()
        
        db.commit()
        
        print(f"    [OK] Deleted {conversations_deleted + guest_conv_deleted} conversations")
        print(f"    [OK] Deleted {messages_deleted} messages")
        print()
        
    except Exception as e:
        print(f"    [WARNING] Cleanup failed: {e}")
        db.rollback()
    finally:
        db.close()

def print_migration_summary():
    """Print summary of migration flow."""
    print("=" * 80)
    print("MIGRATION FLOW SUMMARY")
    print("=" * 80)
    print()
    
    print("Guest-to-User Migration Process:")
    print()
    print("  1. Guest Interaction (Before Login)")
    print("     - Guest uses app without authentication")
    print("     - Conversations stored in Redis (hot cache)")
    print("     - Messages also persisted in PostgreSQL conversation_cache")
    print("     - user_id = guest_id (UUID)")
    print("     - platform = 'guest'")
    print()
    
    print("  2. User Signs Up / Logs In")
    print("     - Authentication system creates authenticated user")
    print("     - Frontend calls /migrate/{guest_id} endpoint")
    print("     - Backend queries all guest conversations")
    print()
    
    print("  3. Data Migration")
    print("     - For each guest conversation:")
    print("       a. Update user_id to authenticated_user_id")
    print("       b. Update platform from 'guest' to 'authenticated'")
    print("       c. Ensure all messages have message_hash")
    print("     - Redis cache can be cleared or migrated separately")
    print()
    
    print("  4. Post-Migration")
    print("     - All guest data now belongs to authenticated user")
    print("     - Full conversation history preserved")
    print("     - Migration logged in cache_migrations table")
    print("     - User can continue from where they left off")
    print()
    
    print("Key Implementation Details:")
    print("  - Migration is in-place (no duplication)")
    print("  - Atomic transaction (all-or-nothing)")
    print("  - Preserves message order via sequence field")
    print("  - Content hashing enables deduplication")
    print("  - migration_version field allows schema evolution")
    print()

if __name__ == "__main__":
    try:
        print_migration_summary()
        
        guest_id, session_id, conv_count, msg_count = create_test_guest_session()
        if not guest_id:
            print("Failed to create test guest session")
            sys.exit(1)
        
        authenticated_user_id = simulate_login_migration(guest_id)
        if not authenticated_user_id:
            print("Failed to simulate login migration")
            sys.exit(1)
        
        if not verify_migrated_data(guest_id, authenticated_user_id):
            print("Data verification failed")
            sys.exit(1)
        
        cleanup_test_data(guest_id, authenticated_user_id)
        
        print("=" * 80)
        print("STATUS: Migration flow test PASSED")
        print("=" * 80)
        print()
        
        sys.exit(0)
        
    except Exception as e:
        print(f"FATAL ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
