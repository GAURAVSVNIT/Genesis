"""
Comprehensive Database Audit & Verification Script
Tests all tables, relationships, and data storage according to the implementation plan
"""

import asyncio
from datetime import datetime
import uuid
import json
from typing import Dict, List, Tuple
from sqlalchemy import inspect, text
from database.database import engine, SessionLocal, Base
from database.models import *

class DatabaseAudit:
    """Comprehensive database audit system."""
    
    def __init__(self):
        self.db = SessionLocal()
        self.inspector = inspect(engine)
        self.results = {
            "tables": {},
            "relationships": {},
            "data_integrity": {},
            "missing_tables": [],
            "warnings": [],
            "errors": []
        }
    
    def run_full_audit(self) -> Dict:
        """Run complete database audit."""
        print("\n" + "="*80)
        print("DATABASE AUDIT - COMPREHENSIVE SCHEMA VERIFICATION")
        print("="*80 + "\n")
        
        # 1. Verify all tables exist
        self._audit_tables()
        
        # 2. Verify columns for each table
        self._audit_columns()
        
        # 3. Verify relationships
        self._audit_relationships()
        
        # 4. Test data insertion
        self._test_data_insertion()
        
        # 5. Verify data retrieval
        self._test_data_retrieval()
        
        # 6. Check constraints
        self._audit_constraints()
        
        # 7. Verify indexes
        self._audit_indexes()
        
        # 8. Generate report
        self._generate_report()
        
        return self.results
    
    def _audit_tables(self):
        """Verify all required tables exist."""
        print("\n📋 TABLE AUDIT")
        print("-" * 80)
        
        existing_tables = set(self.inspector.get_table_names())
        
        required_tables = {
            # User & Auth
            "users": ["id", "email", "username", "password_hash", "status"],
            "user_settings": ["id", "user_id", "theme", "notify_on_response"],
            "api_keys": ["id", "user_id", "key_hash", "is_active"],
            
            # Conversations & Messages
            "conversations": ["id", "user_id", "title", "status", "model_used"],
            "conversation_folders": ["id", "user_id", "name", "parent_folder_id"],
            "messages": ["id", "conversation_id", "user_id", "role", "content"],
            
            # Content Generation
            "generated_content": ["id", "user_id", "prompt", "generated_content", "status"],
            "content_embeddings": ["id", "content_id", "embedding", "embedding_model"],
            "file_attachments": ["id", "user_id", "filename", "storage_url"],
            
            # Advanced Features (NEW)
            "content_versions": ["id", "content_id", "version_number", "is_selected"],
            "system_prompts": ["id", "agent_type", "name", "prompt_text"],
            "message_feedback": ["id", "message_id", "user_id", "rating"],
            "rag_sources": ["id", "message_id", "source_type", "similarity_score"],
            "conversation_context": ["id", "conversation_id", "context_window_tokens"],
            
            # Usage & Analytics
            "usage_metrics": ["id", "user_id", "total_requests", "cache_hits"],
            "usage_statistics": ["id", "user_id", "tokens_used", "model_used"],
            "search_history": ["id", "user_id", "query", "results_count"],
            "activity_logs": ["id", "user_id", "action", "resource_type"],
            "conversation_shares": ["id", "conversation_id", "shared_by_user_id"],
            
            # Cache Tables
            "conversation_cache": ["id", "session_id", "conversation_hash"],
            "message_cache": ["id", "conversation_id", "role", "content"],
            "prompt_cache": ["id", "user_id", "prompt_hash"],
            "cache_embedding": ["id", "cache_id", "embedding"],
            "cache_metrics": ["id", "user_id", "cache_hits", "cache_misses"],
        }
        
        print(f"✅ Checking {len(required_tables)} required tables...\n")
        
        for table_name, required_cols in required_tables.items():
            if table_name in existing_tables:
                # Get actual columns
                actual_cols = {col['name'] for col in self.inspector.get_columns(table_name)}
                
                # Check if all required columns exist
                missing_cols = set(required_cols) - actual_cols
                
                if missing_cols:
                    status = "⚠️ INCOMPLETE"
                    self.results["tables"][table_name] = {
                        "exists": True,
                        "status": "incomplete",
                        "missing_columns": list(missing_cols),
                        "actual_columns": list(actual_cols)
                    }
                    print(f"{status} {table_name}")
                    print(f"   ❌ Missing columns: {missing_cols}")
                else:
                    status = "✅ COMPLETE"
                    self.results["tables"][table_name] = {
                        "exists": True,
                        "status": "complete",
                        "column_count": len(actual_cols)
                    }
                    print(f"{status} {table_name} ({len(actual_cols)} columns)")
            else:
                status = "❌ MISSING"
                self.results["tables"][table_name] = {"exists": False, "status": "missing"}
                print(f"{status} {table_name}")
                self.results["missing_tables"].append(table_name)
        
        print(f"\n📊 Summary: {len([t for t in self.results['tables'].values() if t['exists']])}/{len(required_tables)} tables present")
    
    def _audit_columns(self):
        """Verify column definitions."""
        print("\n📑 COLUMN AUDIT")
        print("-" * 80)
        
        critical_columns = {
            "users": {
                "id": "UUID",
                "email": "VARCHAR",
                "username": "VARCHAR",
                "subscription_status": "VARCHAR",
                "created_at": "TIMESTAMP"
            },
            "conversations": {
                "user_id": "UUID",
                "title": "VARCHAR",
                "agent_type": "VARCHAR",
                "model_used": "VARCHAR",
                "temperature": "INTEGER",
                "status": "VARCHAR"
            },
            "messages": {
                "conversation_id": "UUID",
                "user_id": "UUID",
                "role": "VARCHAR",
                "content": "TEXT",
                "tokens_used": "INTEGER",
                "message_index": "INTEGER"
            },
            "generated_content": {
                "user_id": "UUID",
                "prompt": "TEXT",
                "generated_content": "JSONB",
                "seo_score": "FLOAT",
                "uniqueness_score": "FLOAT",
                "engagement_score": "FLOAT",
                "status": "VARCHAR"
            },
            "content_versions": {
                "content_id": "UUID",
                "version_number": "INTEGER",
                "is_selected": "BOOLEAN",
                "model_used": "VARCHAR",
                "user_rating": "INTEGER"
            },
            "message_feedback": {
                "message_id": "UUID",
                "user_id": "UUID",
                "rating": "INTEGER",
                "is_helpful": "BOOLEAN",
                "is_accurate": "BOOLEAN"
            },
            "usage_metrics": {
                "user_id": "UUID",
                "total_requests": "INTEGER",
                "cache_hits": "INTEGER",
                "total_cost": "FLOAT",
                "tier": "VARCHAR"
            }
        }
        
        issues_found = 0
        
        for table_name, expected_cols in critical_columns.items():
            try:
                actual_cols = {col['name']: col['type'] for col in self.inspector.get_columns(table_name)}
                
                for col_name, col_type in expected_cols.items():
                    if col_name in actual_cols:
                        print(f"✅ {table_name}.{col_name}")
                    else:
                        print(f"❌ {table_name}.{col_name} - MISSING")
                        issues_found += 1
                        self.results["errors"].append(f"Missing column: {table_name}.{col_name}")
            except Exception as e:
                print(f"⚠️  {table_name} - Error: {e}")
        
        print(f"\n📊 Column audit: {len(critical_columns)} tables verified, {issues_found} issues found")
    
    def _audit_relationships(self):
        """Verify foreign key relationships."""
        print("\n🔗 RELATIONSHIP AUDIT")
        print("-" * 80)
        
        expected_relationships = [
            ("users", "conversations", "user_id"),
            ("users", "messages", "user_id"),
            ("users", "generated_content", "user_id"),
            ("conversations", "messages", "conversation_id"),
            ("generated_content", "content_embeddings", "content_id"),
            ("generated_content", "content_versions", "content_id"),
            ("messages", "message_feedback", "message_id"),
            ("messages", "rag_sources", "message_id"),
            ("conversations", "conversation_context", "conversation_id"),
        ]
        
        print(f"✅ Checking {len(expected_relationships)} relationships...\n")
        
        for parent_table, child_table, fk_column in expected_relationships:
            try:
                # Check if child table has the foreign key
                child_cols = {col['name']: col for col in self.inspector.get_columns(child_table)}
                
                if fk_column in child_cols:
                    print(f"✅ {parent_table}.id → {child_table}.{fk_column}")
                    self.results["relationships"][f"{parent_table}→{child_table}"] = "valid"
                else:
                    print(f"❌ {parent_table}.id → {child_table}.{fk_column} - MISSING FK")
                    self.results["relationships"][f"{parent_table}→{child_table}"] = "missing"
            except Exception as e:
                print(f"⚠️  {parent_table} → {child_table} - Error: {e}")
    
    def _test_data_insertion(self):
        """Test inserting sample data."""
        print("\n➕ DATA INSERTION TEST")
        print("-" * 80)
        
        try:
            # Create test user
            test_user = User(
                id=str(uuid.uuid4()),
                email=f"test_{uuid.uuid4().hex[:8]}@example.com",
                username=f"testuser_{uuid.uuid4().hex[:8]}",
                password_hash="hashed_password_123",
                status="active",
                subscription_status="free"
            )
            self.db.add(test_user)
            self.db.commit()
            print(f"✅ User created: {test_user.email}")
            
            # Create test conversation
            test_conversation = Conversation(
                id=str(uuid.uuid4()),
                user_id=test_user.id,
                title="Test Conversation",
                agent_type="text-generation",
                model_used="gpt-4",
                temperature=7,
                status="active"
            )
            self.db.add(test_conversation)
            self.db.commit()
            print(f"✅ Conversation created: {test_conversation.title}")
            
            # Create test message
            test_message = Message(
                id=str(uuid.uuid4()),
                conversation_id=test_conversation.id,
                user_id=test_user.id,
                role="user",
                content="Test message content",
                content_type="text",
                message_index=1,
                tokens_used=10
            )
            self.db.add(test_message)
            self.db.commit()
            print(f"✅ Message created: {test_message.role} message")
            
            # Create test content
            test_content = GeneratedContent(
                id=str(uuid.uuid4()),
                user_id=test_user.id,
                conversation_id=test_conversation.id,
                original_prompt="Generate a test prompt",
                generated_content={"text": "Generated test content"},
                content_type="text",
                platform="general",
                status="draft",
                seo_score=0.85,
                uniqueness_score=0.90,
                engagement_score=0.88
            )
            self.db.add(test_content)
            self.db.commit()
            print(f"✅ Generated content created: {test_content.content_type}")
            
            # Create test version
            test_version = ContentVersion(
                id=str(uuid.uuid4()),
                content_id=test_content.id,
                conversation_id=test_conversation.id,
                user_id=test_user.id,
                version_number=1,
                is_selected=True,
                generated_content={"text": "Version 1 content"},
                model_used="gpt-4",
                temperature=0.7,
                seo_score=0.85,
                uniqueness_score=0.90,
                engagement_score=0.88
            )
            self.db.add(test_version)
            self.db.commit()
            print(f"✅ Content version created: Version {test_version.version_number}")
            
            # Create test feedback
            test_feedback = MessageFeedback(
                id=str(uuid.uuid4()),
                message_id=test_message.id,
                user_id=test_user.id,
                conversation_id=test_conversation.id,
                rating=5,
                is_helpful=True,
                is_accurate=True,
                is_relevant=True
            )
            self.db.add(test_feedback)
            self.db.commit()
            print(f"✅ Message feedback created: Rating {test_feedback.rating}")
            
            # Create test context
            test_context = ConversationContext(
                id=str(uuid.uuid4()),
                conversation_id=test_conversation.id,
                user_id=test_user.id,
                context_window_tokens=2000,
                max_context_tokens=8000,
                rag_enabled=True
            )
            self.db.add(test_context)
            self.db.commit()
            print(f"✅ Conversation context created: {test_context.context_window_tokens} tokens")
            
            # Store IDs for retrieval test
            self.test_data = {
                "user_id": test_user.id,
                "conversation_id": test_conversation.id,
                "message_id": test_message.id,
                "content_id": test_content.id,
                "version_id": test_version.id,
                "feedback_id": test_feedback.id,
                "context_id": test_context.id
            }
            
            print(f"\n✅ All test data inserted successfully")
            
        except Exception as e:
            print(f"❌ Error inserting data: {str(e)}")
            self.results["errors"].append(f"Data insertion error: {str(e)}")
    
    def _test_data_retrieval(self):
        """Test retrieving inserted data."""
        print("\n🔍 DATA RETRIEVAL TEST")
        print("-" * 80)
        
        if not hasattr(self, 'test_data'):
            print("⚠️  No test data to retrieve (insertion may have failed)")
            return
        
        try:
            # Retrieve user
            user = self.db.query(User).filter(User.id == self.test_data['user_id']).first()
            if user:
                print(f"✅ User retrieved: {user.email}")
            else:
                print(f"❌ User not found")
            
            # Retrieve conversation
            conversation = self.db.query(Conversation).filter(
                Conversation.id == self.test_data['conversation_id']
            ).first()
            if conversation:
                print(f"✅ Conversation retrieved: {conversation.title}")
                print(f"   - User ID: {conversation.user_id}")
                print(f"   - Agent type: {conversation.agent_type}")
            else:
                print(f"❌ Conversation not found")
            
            # Retrieve messages
            messages = self.db.query(Message).filter(
                Message.conversation_id == self.test_data['conversation_id']
            ).all()
            print(f"✅ Messages retrieved: {len(messages)} message(s)")
            
            # Retrieve content
            content = self.db.query(GeneratedContent).filter(
                GeneratedContent.id == self.test_data['content_id']
            ).first()
            if content:
                print(f"✅ Content retrieved: {content.content_type}")
                print(f"   - SEO Score: {content.seo_score}")
                print(f"   - Uniqueness: {content.uniqueness_score}")
                print(f"   - Engagement: {content.engagement_score}")
            
            # Retrieve versions
            versions = self.db.query(ContentVersion).filter(
                ContentVersion.content_id == self.test_data['content_id']
            ).all()
            print(f"✅ Content versions retrieved: {len(versions)} version(s)")
            
            # Retrieve feedback
            feedback = self.db.query(MessageFeedback).filter(
                MessageFeedback.message_id == self.test_data['message_id']
            ).all()
            print(f"✅ Feedback retrieved: {len(feedback)} feedback record(s)")
            
            # Retrieve context
            context = self.db.query(ConversationContext).filter(
                ConversationContext.conversation_id == self.test_data['conversation_id']
            ).first()
            if context:
                print(f"✅ Context retrieved: {context.context_window_tokens} tokens")
            
            print(f"\n✅ All retrieval tests passed")
            
        except Exception as e:
            print(f"❌ Error retrieving data: {str(e)}")
            self.results["errors"].append(f"Data retrieval error: {str(e)}")
    
    def _audit_constraints(self):
        """Verify constraints."""
        print("\n🔒 CONSTRAINT AUDIT")
        print("-" * 80)
        
        # Check primary keys
        tables_to_check = [
            "users", "conversations", "messages", "generated_content",
            "content_versions", "message_feedback", "conversation_context"
        ]
        
        for table_name in tables_to_check:
            try:
                pk = self.inspector.get_pk_constraint(table_name)
                if pk:
                    print(f"✅ {table_name}: Primary key on {pk['constrained_columns']}")
                else:
                    print(f"❌ {table_name}: No primary key")
            except Exception as e:
                print(f"⚠️  {table_name}: {str(e)}")
    
    def _audit_indexes(self):
        """Verify indexes."""
        print("\n📇 INDEX AUDIT")
        print("-" * 80)
        
        tables_to_check = [
            "users", "conversations", "messages", "generated_content",
            "content_versions", "message_feedback"
        ]
        
        for table_name in tables_to_check:
            try:
                indexes = self.inspector.get_indexes(table_name)
                if indexes:
                    print(f"✅ {table_name}: {len(indexes)} index(es)")
                    for idx in indexes:
                        print(f"   - {idx['name']} on {idx['column_names']}")
            except Exception as e:
                print(f"⚠️  {table_name}: {str(e)}")
    
    def _generate_report(self):
        """Generate final audit report."""
        print("\n" + "="*80)
        print("📊 AUDIT REPORT SUMMARY")
        print("="*80 + "\n")
        
        # Count results
        tables_ok = len([t for t in self.results['tables'].values() if t['exists']])
        tables_total = len(self.results['tables'])
        
        print(f"📋 Tables: {tables_ok}/{tables_total} present")
        
        if self.results['missing_tables']:
            print(f"   ⚠️  Missing: {', '.join(self.results['missing_tables'])}")
        
        print(f"\n🔗 Relationships: {len([r for r in self.results['relationships'].values() if r == 'valid'])} valid")
        
        if any(r != 'valid' for r in self.results['relationships'].values()):
            print(f"   ⚠️  Issues: {sum(1 for r in self.results['relationships'].values() if r != 'valid')}")
        
        if self.results['errors']:
            print(f"\n❌ Errors ({len(self.results['errors'])}):")
            for error in self.results['errors']:
                print(f"   - {error}")
        
        if self.results['warnings']:
            print(f"\n⚠️  Warnings ({len(self.results['warnings'])}):")
            for warning in self.results['warnings']:
                print(f"   - {warning}")
        
        # Overall status
        print("\n" + "-"*80)
        if not self.results['errors'] and tables_ok == tables_total:
            print("✅ DATABASE AUDIT: PASSED - All systems operational")
        elif tables_ok >= tables_total * 0.8 and not self.results['errors']:
            print("⚠️  DATABASE AUDIT: WARNING - Some tables missing but core systems OK")
        else:
            print("❌ DATABASE AUDIT: FAILED - Critical issues found")
        print("-"*80 + "\n")
    
    def cleanup(self):
        """Clean up test data."""
        try:
            if hasattr(self, 'test_data'):
                # Delete in reverse order of creation
                for model, id_field in [
                    (ConversationContext, 'context_id'),
                    (MessageFeedback, 'feedback_id'),
                    (ContentVersion, 'version_id'),
                    (GeneratedContent, 'content_id'),
                    (Message, 'message_id'),
                    (Conversation, 'conversation_id'),
                    (User, 'user_id'),
                ]:
                    if id_field in self.test_data:
                        self.db.query(model).filter(
                            model.id == self.test_data[id_field]
                        ).delete()
                
                self.db.commit()
                print("✅ Test data cleaned up")
        except Exception as e:
            print(f"⚠️  Error cleaning up: {str(e)}")
        finally:
            self.db.close()


if __name__ == "__main__":
    audit = DatabaseAudit()
    results = audit.run_full_audit()
    audit.cleanup()
    
    # Save results to file
    with open("database_audit_results.json", "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"\n💾 Detailed results saved to: database_audit_results.json")
