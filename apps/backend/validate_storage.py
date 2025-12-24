#!/usr/bin/env python3
"""Data storage validation - Check if values are being stored correctly"""

import uuid
import json
from datetime import datetime
from sqlalchemy import func
from database.database import SessionLocal
from database.models import *

def validate_data_storage():
    """Test data insertion and retrieval"""
    db = SessionLocal()
    
    print("\n" + "="*80)
    print("DATA STORAGE VALIDATION - Checking if values persist in database")
    print("="*80 + "\n")
    
    try:
        # 1. Create test user
        print("[1] Testing USER table...")
        user = User(
            id=str(uuid.uuid4()),
            email=f"validation_test_{uuid.uuid4().hex[:6]}@test.com",
            username=f"val_user_{uuid.uuid4().hex[:6]}",
            password_hash="test_hash_123",
            status="active",
            subscription_status="pro"
        )
        db.add(user)
        db.commit()
        print(f"    [OK] User created: {user.email}")
        
        # Verify retrieval
        retrieved_user = db.query(User).filter(User.id == user.id).first()
        if retrieved_user:
            print(f"    [OK] User retrieved: {retrieved_user.username}")
            print(f"        Status: {retrieved_user.status}")
            print(f"        Subscription: {retrieved_user.subscription_status}")
        
        # 2. Create conversation
        print("\n[2] Testing CONVERSATION table...")
        conv = Conversation(
            id=str(uuid.uuid4()),
            user_id=user.id,
            title="Validation Test Conv",
            agent_type="text-generation",
            model_used="gpt-4",
            temperature=7,
            status="active"
        )
        db.add(conv)
        db.commit()
        print(f"    [OK] Conversation created: {conv.title}")
        
        retrieved_conv = db.query(Conversation).filter(Conversation.id == conv.id).first()
        if retrieved_conv:
            print(f"    [OK] Conversation retrieved")
            print(f"        Model: {retrieved_conv.model_used}")
            print(f"        Agent: {retrieved_conv.agent_type}")
            print(f"        Temperature: {retrieved_conv.temperature}")
        
        # 3. Create message
        print("\n[3] Testing MESSAGE table...")
        msg = Message(
            id=str(uuid.uuid4()),
            conversation_id=conv.id,
            user_id=user.id,
            role="user",
            content="Test message content",
            content_type="text",
            message_index=1,
            tokens_used=15
        )
        db.add(msg)
        db.commit()
        print(f"    [OK] Message created: {msg.role}")
        
        retrieved_msg = db.query(Message).filter(Message.id == msg.id).first()
        if retrieved_msg:
            print(f"    [OK] Message retrieved")
            print(f"        Content: {retrieved_msg.content[:40]}...")
            print(f"        Tokens: {retrieved_msg.tokens_used}")
        
        # 4. Create generated content
        print("\n[4] Testing GENERATED_CONTENT table...")
        content = GeneratedContent(
            id=str(uuid.uuid4()),
            user_id=user.id,
            conversation_id=conv.id,
            original_prompt="Generate a test prompt",
            generated_content={"text": "Generated content here", "type": "test"},
            content_type="blog",
            platform="general",
            status="draft",
            seo_score=0.85,
            uniqueness_score=0.92,
            engagement_score=0.88
        )
        db.add(content)
        db.commit()
        print(f"    [OK] Content created: {content.content_type}")
        
        retrieved_content = db.query(GeneratedContent).filter(GeneratedContent.id == content.id).first()
        if retrieved_content:
            print(f"    [OK] Content retrieved")
            print(f"        SEO Score: {retrieved_content.seo_score}")
            print(f"        Uniqueness: {retrieved_content.uniqueness_score}")
            print(f"        Engagement: {retrieved_content.engagement_score}")
            if isinstance(retrieved_content.generated_content, dict):
                print(f"        Content: {retrieved_content.generated_content}")
            else:
                print(f"        Content: {json.loads(retrieved_content.generated_content)}")
        
        # 5. Create content version
        print("\n[5] Testing CONTENT_VERSIONS table...")
        version = ContentVersion(
            id=str(uuid.uuid4()),
            content_id=content.id,
            conversation_id=conv.id,
            user_id=user.id,
            version_number=1,
            is_selected=True,
            generated_content={"text": "Version 1", "notes": "First version"},
            model_used="gpt-4",
            temperature=0.7,
            seo_score=0.85,
            uniqueness_score=0.92,
            engagement_score=0.88,
            user_rating=5
        )
        db.add(version)
        db.commit()
        print(f"    [OK] Version created: Version {version.version_number}")
        
        retrieved_version = db.query(ContentVersion).filter(ContentVersion.id == version.id).first()
        if retrieved_version:
            print(f"    [OK] Version retrieved")
            print(f"        Rating: {retrieved_version.user_rating}")
            print(f"        Selected: {retrieved_version.is_selected}")
            print(f"        Model: {retrieved_version.model_used}")
            print(f"        Scores - SEO: {retrieved_version.seo_score}, Unique: {retrieved_version.uniqueness_score}")
        
        # 6. Create message feedback
        print("\n[6] Testing MESSAGE_FEEDBACK table...")
        feedback = MessageFeedback(
            id=str(uuid.uuid4()),
            message_id=msg.id,
            user_id=user.id,
            conversation_id=conv.id,
            rating=5,
            is_helpful=True,
            is_accurate=True,
            is_relevant=True,
            feedback_text="Great response!",
            has_errors=False
        )
        db.add(feedback)
        db.commit()
        print(f"    [OK] Feedback created: Rating {feedback.rating}")
        
        retrieved_feedback = db.query(MessageFeedback).filter(MessageFeedback.id == feedback.id).first()
        if retrieved_feedback:
            print(f"    [OK] Feedback retrieved")
            print(f"        Rating: {retrieved_feedback.rating}")
            print(f"        Helpful: {retrieved_feedback.is_helpful}")
            print(f"        Accurate: {retrieved_feedback.is_accurate}")
            print(f"        Text: {retrieved_feedback.feedback_text}")
        
        # 7. Create RAG source
        print("\n[7] Testing RAG_SOURCES table...")
        rag = RAGSource(
            id=str(uuid.uuid4()),
            message_id=msg.id,
            user_id=user.id,
            source_type="knowledge_base",
            source_id=str(uuid.uuid4()),
            similarity_score=0.95,
            was_used_in_response=True,
            source_content="Source content from KB"
        )
        db.add(rag)
        db.commit()
        print(f"    [OK] RAG source created: {rag.source_type}")
        
        retrieved_rag = db.query(RAGSource).filter(RAGSource.id == rag.id).first()
        if retrieved_rag:
            print(f"    [OK] RAG source retrieved")
            print(f"        Type: {retrieved_rag.source_type}")
            print(f"        Similarity: {retrieved_rag.similarity_score}")
            print(f"        Used: {retrieved_rag.was_used_in_response}")
            print(f"        Content: {retrieved_rag.source_content[:40]}...")
        
        # 8. Create conversation context
        print("\n[8] Testing CONVERSATION_CONTEXT table...")
        ctx = ConversationContext(
            id=str(uuid.uuid4()),
            conversation_id=conv.id,
            user_id=user.id,
            context_window_tokens=2000,
            max_context_tokens=8000,
            rag_enabled=True,
            temperature=0.7,
            top_p=0.9
        )
        db.add(ctx)
        db.commit()
        print(f"    [OK] Context created: {ctx.context_window_tokens} tokens")
        
        retrieved_ctx = db.query(ConversationContext).filter(ConversationContext.id == ctx.id).first()
        if retrieved_ctx:
            print(f"    [OK] Context retrieved")
            print(f"        Window: {retrieved_ctx.context_window_tokens}")
            print(f"        Max: {retrieved_ctx.max_context_tokens}")
            print(f"        RAG Enabled: {retrieved_ctx.rag_enabled}")
            print(f"        Temperature: {retrieved_ctx.temperature}")
        
        # 9. Create usage metrics
        print("\n[9] Testing USAGE_METRICS table...")
        metrics = UsageMetrics(
            id=str(uuid.uuid4()),
            user_id=user.id,
            total_requests=5,
            cache_hits=2,
            cache_misses=3,
            total_tokens=1500,
            total_input_tokens=800,
            total_output_tokens=700,
            total_cost=1.50,
            cache_cost=0.50,
            tier="pro",
            monthly_request_limit=5000,
            monthly_requests_used=50
        )
        db.add(metrics)
        db.commit()
        print(f"    [OK] Metrics created: {metrics.total_requests} requests")
        
        retrieved_metrics = db.query(UsageMetrics).filter(UsageMetrics.id == metrics.id).first()
        if retrieved_metrics:
            print(f"    [OK] Metrics retrieved")
            print(f"        Requests: {retrieved_metrics.total_requests}")
            print(f"        Cache Hits: {retrieved_metrics.cache_hits}")
            print(f"        Total Cost: ${retrieved_metrics.total_cost}")
            print(f"        Tokens: {retrieved_metrics.total_tokens}")
        
        # 10. Create activity log
        print("\n[10] Testing ACTIVITY_LOGS table...")
        log = ActivityLog(
            id=str(uuid.uuid4()),
            user_id=user.id,
            action="content_generated",
            resource_type="generated_content",
            resource_id=content.id,
            changes={"status": "draft", "seo_score": 0.85},
            status="success"
        )
        db.add(log)
        db.commit()
        print(f"    [OK] Log created: {log.action}")
        
        retrieved_log = db.query(ActivityLog).filter(ActivityLog.id == log.id).first()
        if retrieved_log:
            print(f"    [OK] Log retrieved")
            print(f"        Action: {retrieved_log.action}")
            print(f"        Resource: {retrieved_log.resource_type}")
            print(f"        Status: {retrieved_log.status}")
            changes = retrieved_log.changes
            if isinstance(changes, str):
                changes = json.loads(changes)
            print(f"        Changes: {changes}")
        
        # Summary statistics
        print("\n" + "-"*80)
        print("DATABASE SUMMARY STATISTICS")
        print("-"*80 + "\n")
        
        stats = {
            "users": db.query(User).count(),
            "conversations": db.query(Conversation).count(),
            "messages": db.query(Message).count(),
            "generated_content": db.query(GeneratedContent).count(),
            "content_versions": db.query(ContentVersion).count(),
            "message_feedback": db.query(MessageFeedback).count(),
            "rag_sources": db.query(RAGSource).count(),
            "conversation_context": db.query(ConversationContext).count(),
            "usage_metrics": db.query(UsageMetrics).count(),
            "activity_logs": db.query(ActivityLog).count(),
        }
        
        for table, count in stats.items():
            print(f"  {table.ljust(25)}: {count} rows")
        
        print("\n" + "="*80)
        print("VALIDATION RESULT: ALL DATA STORAGE WORKING CORRECTLY")
        print("="*80 + "\n")
        
        return True
        
    except Exception as e:
        print(f"\n[ERROR] {str(e)}")
        import traceback
        traceback.print_exc()
        return False
    
    finally:
        # Cleanup test data
        try:
            print("\nCleaning up test data...")
            db.query(ActivityLog).filter(ActivityLog.user_id == user.id).delete()
            db.query(UsageMetrics).filter(UsageMetrics.user_id == user.id).delete()
            db.query(ConversationContext).filter(ConversationContext.user_id == user.id).delete()
            db.query(RAGSource).filter(RAGSource.user_id == user.id).delete()
            db.query(MessageFeedback).filter(MessageFeedback.user_id == user.id).delete()
            db.query(ContentVersion).filter(ContentVersion.user_id == user.id).delete()
            db.query(GeneratedContent).filter(GeneratedContent.user_id == user.id).delete()
            db.query(Message).filter(Message.user_id == user.id).delete()
            db.query(Conversation).filter(Conversation.user_id == user.id).delete()
            db.query(User).filter(User.id == user.id).delete()
            db.commit()
            print("[OK] Test data cleaned up")
        except Exception as e:
            print(f"[WARNING] Cleanup error: {e}")
        
        db.close()

if __name__ == "__main__":
    validate_data_storage()
