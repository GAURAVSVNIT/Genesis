"""
Database health check and validation module.
Ensures database integrity and consistency.
"""

from typing import List, Dict, Tuple, Optional
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import text, inspect
import time


class DatabaseValidator:
    """Validate database structure and data integrity."""
    
    def __init__(self, db: Session):
        """
        Initialize validator.
        
        Args:
            db: Database session
        """
        self.db = db
        self.issues = []
        self.warnings = []
    
    def validate_all(self) -> Dict:
        """
        Run all validation checks.
        
        Returns:
            Validation report
        """
        print("\n" + "="*80)
        print("🔍 DATABASE VALIDATION REPORT")
        print("="*80 + "\n")
        
        start = time.time()
        
        # Run checks
        self.check_table_existence()
        self.check_indexes()
        self.check_foreign_keys()
        self.check_data_consistency()
        self.check_table_counts()
        
        duration = time.time() - start
        
        # Report
        return self.generate_report(duration)
    
    def check_table_existence(self) -> bool:
        """Check if all required tables exist."""
        print("📋 Checking table existence...")
        
        required_tables = [
            # User tables
            "users", "user_settings", "api_keys",
            # Conversation tables
            "conversations", "messages", "conversation_folders",
            # Content tables
            "generated_content", "content_embeddings", "file_attachments", "usage_metrics",
            # Cache tables
            "conversation_cache", "message_cache", "prompt_cache", 
            "cache_embeddings", "cache_metrics", "cache_migrations", "cache_content_mapping",
            # Advanced tables
            "content_versions", "message_feedback", "rag_sources", 
            "conversation_context", "system_prompts",
            # Analytics tables
            "usage_statistics", "search_history", "activity_logs", "conversation_shares"
        ]
        
        inspector = inspect(self.db.get_bind())
        existing_tables = inspector.get_table_names()
        
        missing = [t for t in required_tables if t not in existing_tables]
        
        if missing:
            print(f"  ❌ Missing tables: {missing}")
            self.issues.append(f"Missing {len(missing)} tables: {missing}")
            return False
        else:
            print(f"  ✅ All {len(required_tables)} required tables exist")
            return True
    
    def check_indexes(self) -> bool:
        """Check if indexes are properly created."""
        print("\n📑 Checking indexes...")
        
        # Get indexes for critical tables
        critical_tables = [
            "conversations", "messages", "generated_content", 
            "prompt_cache", "message_cache"
        ]
        
        inspector = inspect(self.db.get_bind())
        issues = []
        
        for table in critical_tables:
            indexes = inspector.get_indexes(table)
            if not indexes:
                issues.append(f"Table '{table}' has no indexes")
        
        if issues:
            print(f"  ⚠️  Found {len(issues)} index issues")
            self.warnings.extend(issues)
            return False
        else:
            print(f"  ✅ Critical tables have indexes")
            return True
    
    def check_foreign_keys(self) -> bool:
        """Check foreign key relationships."""
        print("\n🔗 Checking foreign keys...")
        
        # Get foreign keys
        inspector = inspect(self.db.get_bind())
        
        # Check key relationships
        tables_to_check = [
            "messages",           # Should reference conversations
            "generated_content",  # Should reference users (optional)
            "content_embeddings", # Should reference generated_content
        ]
        
        orphaned = []
        
        for table in tables_to_check:
            fks = inspector.get_foreign_keys(table)
            if not fks:
                print(f"  ⚠️  Table '{table}' has no foreign keys")
        
        if orphaned:
            print(f"  ⚠️  Found potential orphaned records")
            self.warnings.append("Potential orphaned records found")
            return False
        else:
            print(f"  ✅ Foreign key relationships OK")
            return True
    
    def check_data_consistency(self) -> bool:
        """Check data consistency."""
        print("\n✔️  Checking data consistency...")
        
        consistency_ok = True
        
        try:
            # Check for conversations without messages
            orphaned_convos = self.db.execute(text("""
                SELECT c.id FROM conversations c
                LEFT JOIN messages m ON c.id = m.conversation_id
                WHERE m.id IS NULL
                LIMIT 5
            """)).fetchall()
            
            if orphaned_convos:
                print(f"  ⚠️  Found {len(orphaned_convos)} conversations with no messages")
                self.warnings.append("Some conversations have no messages")
                consistency_ok = False
            
            # Check for orphaned generated content
            orphaned_content = self.db.execute(text("""
                SELECT COUNT(*) as count FROM generated_content gc
                WHERE gc.user_id IS NOT NULL 
                AND NOT EXISTS (SELECT 1 FROM users u WHERE u.id = gc.user_id)
            """)).fetchone()
            
            if orphaned_content and orphaned_content[0] > 0:
                print(f"  ⚠️  Found {orphaned_content[0]} orphaned generated_content records")
                self.warnings.append(f"Found {orphaned_content[0]} orphaned generated_content")
                consistency_ok = False
            
            if consistency_ok:
                print(f"  ✅ Data consistency OK")
            
            return consistency_ok
            
        except Exception as e:
            print(f"  ⚠️  Could not check consistency: {e}")
            return True  # Don't fail if we can't check
    
    def check_table_counts(self) -> bool:
        """Get table record counts."""
        print("\n📊 Checking table record counts...")
        
        tables_to_count = [
            "users", "conversations", "messages", "generated_content",
            "conversation_cache", "message_cache", "prompt_cache",
            "content_embeddings", "usage_metrics"
        ]
        
        counts = {}
        
        for table in tables_to_count:
            try:
                result = self.db.execute(text(f"SELECT COUNT(*) FROM {table}")).scalar()
                counts[table] = result
                print(f"  {table:25} : {result:>6} records")
            except Exception as e:
                print(f"  {table:25} : ❌ Error: {e}")
        
        return True
    
    def generate_report(self, duration: float) -> Dict:
        """Generate validation report."""
        print("\n" + "="*80)
        print("📋 VALIDATION SUMMARY")
        print("="*80)
        
        success = len(self.issues) == 0
        
        print(f"\n  Status: {'✅ HEALTHY' if success else '❌ ISSUES FOUND'}")
        print(f"  Duration: {duration:.2f}s")
        print(f"  Issues: {len(self.issues)}")
        print(f"  Warnings: {len(self.warnings)}")
        
        if self.issues:
            print(f"\n  ❌ Critical Issues:")
            for issue in self.issues:
                print(f"     - {issue}")
        
        if self.warnings:
            print(f"\n  ⚠️  Warnings:")
            for warning in self.warnings:
                print(f"     - {warning}")
        
        print("\n" + "="*80 + "\n")
        
        return {
            "healthy": success,
            "duration_seconds": duration,
            "issues": self.issues,
            "warnings": self.warnings,
            "timestamp": datetime.utcnow().isoformat()
        }


class DatabaseRepair:
    """Repair common database issues."""
    
    def __init__(self, db: Session):
        """
        Initialize repair utility.
        
        Args:
            db: Database session
        """
        self.db = db
    
    def cleanup_orphaned_content(self) -> int:
        """
        Remove orphaned generated_content records.
        
        Returns:
            Number of records deleted
        """
        try:
            # Find orphaned records
            orphaned = self.db.execute(text("""
                SELECT gc.id FROM generated_content gc
                WHERE gc.user_id IS NOT NULL 
                AND NOT EXISTS (SELECT 1 FROM users u WHERE u.id = gc.user_id)
            """)).fetchall()
            
            count = len(orphaned)
            
            if count > 0:
                ids = [str(row[0]) for row in orphaned]
                placeholders = ",".join(["'" + id + "'" for id in ids])
                
                self.db.execute(text(f"""
                    DELETE FROM generated_content WHERE id IN ({placeholders})
                """))
                
                self.db.commit()
                print(f"✅ Removed {count} orphaned generated_content records")
            
            return count
            
        except Exception as e:
            print(f"❌ Error cleaning up orphaned content: {e}")
            self.db.rollback()
            return 0
    
    def cleanup_old_cache(self, days_old: int = 30) -> int:
        """
        Remove old cache entries.
        
        Args:
            days_old: Delete cache older than this many days
            
        Returns:
            Number of records deleted
        """
        try:
            # Delete old cache entries
            result = self.db.execute(text(f"""
                DELETE FROM prompt_cache 
                WHERE created_at < NOW() - INTERVAL '{days_old} days'
            """))
            
            count = result.rowcount
            
            self.db.commit()
            print(f"✅ Removed {count} cache entries older than {days_old} days")
            
            return count
            
        except Exception as e:
            print(f"❌ Error cleaning cache: {e}")
            self.db.rollback()
            return 0
    
    def reset_cache_metrics(self) -> bool:
        """Reset cache metrics."""
        try:
            self.db.execute(text("""
                UPDATE cache_metrics SET cache_hits = 0, cache_misses = 0, total_entries = 0
            """))
            self.db.commit()
            print("✅ Cache metrics reset")
            return True
        except Exception as e:
            print(f"❌ Error resetting metrics: {e}")
            self.db.rollback()
            return False


# CLI interface
if __name__ == "__main__":
    import sys
    from database.database import SessionLocal
    
    db = SessionLocal()
    
    try:
        validator = DatabaseValidator(db)
        report = validator.validate_all()
        
        if not report["healthy"] and len(sys.argv) > 1 and sys.argv[1] == "--repair":
            print("\n🔧 Running repairs...")
            repair = DatabaseRepair(db)
            repair.cleanup_orphaned_content()
            repair.cleanup_old_cache()
            
            print("\n✅ Repairs complete. Re-validating...")
            validator2 = DatabaseValidator(db)
            validator2.validate_all()
    
    finally:
        db.close()
