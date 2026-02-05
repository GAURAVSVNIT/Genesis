"""
Check metrics and migration tables content and determine if they should be auto-populated
"""

from database.database import SessionLocal
from database.models.cache import CacheMetrics, CacheMigration
import json

def check_metrics_and_migrations():
    """Check what's in metrics and migrations tables"""
    
    db = SessionLocal()
    
    print("=" * 80)
    print("METRICS & MIGRATIONS TABLE AUDIT")
    print("=" * 80)
    
    # Check cache_metrics
    print("\n[TABLE: cache_metrics]")
    print("Purpose: Track cache performance metrics (hits, misses, response times, etc)")
    print("-" * 80)
    
    metrics = db.query(CacheMetrics).all()
    if metrics:
        print(f"Total Records: {len(metrics)}")
        for i, metric in enumerate(metrics, 1):
            print(f"\nMetric Record {i}:")
            print(f"  id: {metric.id}")
            print(f"  total_entries: {metric.total_entries}")
            print(f"  cache_hits: {metric.cache_hits}")
            print(f"  cache_misses: {metric.cache_misses}")
            print(f"  total_requests: {metric.total_requests}")
            print(f"  hit_rate: {metric.hit_rate}%")
            print(f"  avg_response_time: {metric.avg_response_time}ms")
            print(f"  avg_generation_time: {metric.avg_generation_time}ms")
            print(f"  storage_size_mb: {metric.storage_size_mb}MB")
            print(f"  recorded_at: {metric.recorded_at}")
    else:
        print("No metrics records found")
    
    # Check cache_migrations
    print("\n" + "=" * 80)
    print("\n[TABLE: cache_migrations]")
    print("Purpose: Track data migrations between storage systems (Redis->Postgres, etc)")
    print("-" * 80)
    
    migrations = db.query(CacheMigration).all()
    if migrations:
        print(f"Total Records: {len(migrations)}")
        for i, migration in enumerate(migrations, 1):
            print(f"\nMigration Record {i}:")
            print(f"  id: {migration.id}")
            print(f"  version: {migration.version}")
            print(f"  migration_type: {migration.migration_type}")
            print(f"  status: {migration.status}")
            print(f"  records_migrated: {migration.records_migrated}")
            print(f"  records_failed: {migration.records_failed}")
            print(f"  started_at: {migration.started_at}")
            print(f"  completed_at: {migration.completed_at}")
            print(f"  source: {migration.source}")
            print(f"  destination: {migration.destination}")
            print(f"  notes: {migration.notes}")
    else:
        print("No migration records found")
    
    # Analysis
    print("\n" + "=" * 80)
    print("ANALYSIS & RECOMMENDATIONS")
    print("=" * 80)
    
    print("\n[cache_metrics Table]")
    print("Current State: Has 1 record (likely placeholder/test data)")
    print("\nShould it be auto-populated?")
    print("  YES - This should be populated periodically:")
    print("  • Every N requests (e.g., every 100 requests)")
    print("  • Every N seconds (e.g., every 60 seconds)")
    print("  • On demand via an API endpoint")
    print("\nWhat to track:")
    print("  • cache_hits: Number of times cached data was retrieved successfully")
    print("  • cache_misses: Number of times cache miss occurred")
    print("  • hit_rate: Percentage of successful cache hits")
    print("  • avg_response_time: Average response time in milliseconds")
    print("  • avg_generation_time: Average generation time for embeddings")
    print("  • storage_size_mb: Total size of cached data")
    
    print("\n[cache_migrations Table]")
    print("Current State: Has 1 record (guest-to-user migration)")
    print("\nShould it be auto-populated?")
    print("  YES - This should be populated when:")
    print("  • Guest session converts to authenticated user")
    print("  • Data is moved between Redis and PostgreSQL")
    print("  • Data is archived or cleaned up")
    print("\nImplementation Status:")
    print("  • guest_to_user migration: Already implemented in guest.py")
    print("  • Other migrations: Need implementation")
    
    db.close()

if __name__ == "__main__":
    check_metrics_and_migrations()
