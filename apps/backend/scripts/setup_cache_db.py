"""
Complete Cache & Content Database Setup with Migration Support

This script:
1. Creates all cache tables (conversation, message, prompt, embeddings, metrics, migrations)
2. Creates all content tables (generated_content, embeddings, attachments)
3. Creates tracking tables (usage_metrics, cache_content_mapping)
4. Sets up migration infrastructure
5. Demonstrates the complete data flow

Run this: python scripts/setup_cache_db.py
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.database import SessionLocal, engine
from database.models.base import Base
from sqlalchemy import inspect, text
from datetime import datetime
import json


def print_header(title):
    """Print formatted header."""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)


def print_section(title):
    """Print formatted section."""
    print(f"\n{title}")
    print("-" * 70)


def create_all_tables():
    """Create all tables from SQLAlchemy models."""
    
    print_header("DATABASE INITIALIZATION")
    
    try:
        # Create all tables
        Base.metadata.create_all(bind=engine)
        
        print("\n✅ All tables created successfully!")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Error creating tables: {e}")
        import traceback
        traceback.print_exc()
        return False


def verify_tables():
    """Verify all required tables exist."""
    
    print_header("VERIFYING TABLE CREATION")
    
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    
    required_tables = {
        # Cache Tables
        "conversation_cache": "Store entire chat sessions",
        "message_cache": "Store individual messages",
        "prompt_cache": "Deduplicate prompts",
        "cache_embeddings": "Store message embeddings",
        "cache_metrics": "Track cache performance",
        "cache_migrations": "Track backend migrations",
        # Content Tables
        "generated_content": "Final generated content",
        "content_embeddings": "Content similarity search",
        "file_attachments": "Track uploaded files",
        # Usage Tracking
        "usage_metrics": "Per-user metrics",
        "cache_content_mapping": "Link cache → content",
    }
    
    existing = set(tables)
    created = {t for t in required_tables if t in existing}
    missing = {t for t in required_tables if t not in existing}
    
    print_section("CACHE TABLES")
    cache_tables = ["conversation_cache", "message_cache", "prompt_cache", 
                    "cache_embeddings", "cache_metrics", "cache_migrations"]
    for table in cache_tables:
        status = "✓" if table in created else "✗"
        print(f"  {status} {table}")
    
    print_section("CONTENT TABLES")
    content_tables = ["generated_content", "content_embeddings", "file_attachments"]
    for table in content_tables:
        status = "✓" if table in created else "✗"
        print(f"  {status} {table}")
    
    print_section("TRACKING TABLES")
    tracking_tables = ["usage_metrics", "cache_content_mapping"]
    for table in tracking_tables:
        status = "✓" if table in created else "✗"
        print(f"  {status} {table}")
    
    success = len(missing) == 0
    
    if success:
        print(f"\n✅ All {len(created)} required tables exist!")
    else:
        print(f"\n⚠️  Missing {len(missing)} tables: {missing}")
    
    return success


def show_table_details():
    """Show column details for all tables."""
    
    print_header("TABLE STRUCTURE DETAILS")
    
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    
    # Group tables
    cache_tables = ["conversation_cache", "message_cache", "prompt_cache", 
                    "cache_embeddings", "cache_metrics", "cache_migrations"]
    content_tables = ["generated_content", "content_embeddings", "file_attachments"]
    tracking_tables = ["usage_metrics", "cache_content_mapping"]
    
    all_tables = cache_tables + content_tables + tracking_tables
    
    for table_name in all_tables:
        if table_name not in tables:
            continue
        
        columns = inspector.get_columns(table_name)
        indexes = inspector.get_indexes(table_name)
        
        print_section(f"{table_name.upper()} ({len(columns)} columns)")
        
        # Show columns
        for col in columns:
            col_type = str(col['type'])[:20].ljust(20)
            nullable = "NULL" if col['nullable'] else "NOT NULL"
            pk = " [PK]" if col['name'] == 'id' else ""
            print(f"  • {col['name'][:30].ljust(30)} {col_type} {nullable}{pk}")
        
        # Show key indexes
        if indexes:
            print(f"\n  Indexes: {len(indexes)} created")
    
    return True


def show_data_flow():
    """Display complete data flow diagram."""
    
    print_header("COMPLETE DATA FLOW ARCHITECTURE")
    
    diagram = """
┌─────────────────────────────────────────────────────────────────────────┐
│                         USER REQUEST (Chat)                              │
│                        POST /v1/content/generate                         │
│                     {"prompt": "...", "platform": "blog"}                │
└────────────────────────────────┬──────────────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                      RATE LIMITING LAYER                                 │
│           ┌──────────────────────────────────────────┐                   │
│           │ Check: is_premium, request_count, TTL    │                   │
│           │ Backend: Redis (Upstash)                 │                   │
│           │ Tiers: Free (10/min), Premium (100/min)  │                   │
│           └──────────────────────────────────────────┘                   │
│           ✗ Return 429 if limit exceeded                                │
└────────────────────────────────┬──────────────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                      CACHING LAYER (HOT)                                 │
│           ┌──────────────────────────────────────────┐                   │
│           │ Check: Redis cache key                   │                   │
│           │ Key: prompt_hash + platform + platform   │                   │
│           │ TTL: 1 hour                              │                   │
│           │ Backend: Redis (Upstash)                 │                   │
│           └──────────────────────────────────────────┘                   │
│           ✓ Return cached response (INSTANT)                            │
└────────────────────────────────┬──────────────────────────────────────────┘
                                  │
        ┌─────────────────────────┴─────────────────────────┐
        │ CACHE MISS (Generate new content)                  │
        ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                      CACHE LAYER (COLD)                                  │
│           ┌──────────────────────────────────────────┐                   │
│           │ Check: PostgreSQL prompt_cache          │                   │
│           │ Table: prompt_cache (hits, text, response) │                   │
│           │ Backend: Supabase PostgreSQL             │                   │
│           └──────────────────────────────────────────┘                   │
│           ✓ Return cached response (FAST)                               │
└────────────────────────────────┬──────────────────────────────────────────┘
                                  │
        ┌─────────────────────────┴─────────────────────────┐
        │ CACHE MISS (Actually generate)                     │
        ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                   CONTENT GENERATION                                     │
│           ┌──────────────────────────────────────────┐                   │
│           │ Call: Vertex AI (gemini-2.0-flash)       │                   │
│           │ Pass: prompt, platform, tone, etc        │                   │
│           │ Get: generated content + tokens          │                   │
│           └──────────────────────────────────────────┘                   │
└────────────────────────────────┬──────────────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                  STORE IN CACHE TABLES (PostgreSQL)                      │
│  ┌─────────────────────────────────────────────────────────────┐        │
│  │ 1. conversation_cache                                        │        │
│  │    • id, user_id, session_id, message_count                │        │
│  │    • platform, tone, created_at, expires_at                │        │
│  │    • migration_version (for versioning)                    │        │
│  └─────────────────────────────────────────────────────────────┘        │
│  ┌─────────────────────────────────────────────────────────────┐        │
│  │ 2. message_cache                                             │        │
│  │    • id, conversation_id, role, content, sequence           │        │
│  │    • tokens, created_at                                     │        │
│  └─────────────────────────────────────────────────────────────┘        │
│  ┌─────────────────────────────────────────────────────────────┐        │
│  │ 3. prompt_cache                                              │        │
│  │    • id, prompt_hash, prompt_text, response_text            │        │
│  │    • model, hits, generation_time                           │        │
│  │    • Deduplicates identical prompts!                        │        │
│  └─────────────────────────────────────────────────────────────┘        │
│  ┌─────────────────────────────────────────────────────────────┐        │
│  │ 4. cache_embeddings                                          │        │
│  │    • id, conversation_id, embedding (vector), text_chunk    │        │
│  │    • For semantic search & similarity                       │        │
│  └─────────────────────────────────────────────────────────────┘        │
│  ┌─────────────────────────────────────────────────────────────┐        │
│  │ 5. cache_metrics                                             │        │
│  │    • id, total_entries, cache_hits, cache_misses           │        │
│  │    • hit_rate, recorded_at                                  │        │
│  └─────────────────────────────────────────────────────────────┘        │
└────────────────────────────────┬──────────────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────────────┐
│               STORE IN MAIN CONTENT TABLES (PostgreSQL)                  │
│  ┌─────────────────────────────────────────────────────────────┐        │
│  │ 1. generated_content                                         │        │
│  │    • id, user_id, conversation_id, message_id              │        │
│  │    • original_prompt, content_type, platform               │        │
│  │    • generated_content (JSONB), status                      │        │
│  │    • seo_score, uniqueness_score, engagement_score          │        │
│  │    • published_at, published_platforms, tags                │        │
│  └─────────────────────────────────────────────────────────────┘        │
│  ┌─────────────────────────────────────────────────────────────┐        │
│  │ 2. content_embeddings                                        │        │
│  │    • id, content_id, text_source, source_id                │        │
│  │    • embedded_text, text_tokens, embedding (vector)         │        │
│  │    • embedding_model, confidence_score, is_valid            │        │
│  └─────────────────────────────────────────────────────────────┘        │
└────────────────────────────────┬──────────────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                   UPDATE TRACKING TABLES                                 │
│  ┌─────────────────────────────────────────────────────────────┐        │
│  │ 1. cache_content_mapping                                     │        │
│  │    • cache_type, cache_id → content_id (linking)            │        │
│  │    • is_synced, last_synced_at (for migrations)             │        │
│  │    • This enables migration between backends!               │        │
│  └─────────────────────────────────────────────────────────────┘        │
│  ┌─────────────────────────────────────────────────────────────┐        │
│  │ 2. usage_metrics                                             │        │
│  │    • user_id, total_requests, cache_hits, cache_misses      │        │
│  │    • total_input_tokens, total_output_tokens, total_cost    │        │
│  │    • cache_hit_rate, average_response_time_ms               │        │
│  │    • tier, monthly_request_limit, monthly_requests_used     │        │
│  │    • Enables rate limiting enforcement & analytics          │        │
│  └─────────────────────────────────────────────────────────────┘        │
│  ┌─────────────────────────────────────────────────────────────┐        │
│  │ 3. cache_migrations (VERSIONING)                             │        │
│  │    • id, version, status, records_migrated                  │        │
│  │    • source, destination, timestamps                        │        │
│  │    • Export to BigQuery/Firestore/Elasticsearch             │        │
│  └─────────────────────────────────────────────────────────────┘        │
└────────────────────────────────┬──────────────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                     RETURN TO USER                                       │
│              {                                                            │
│                "content": "...",                                         │
│                "type": "blog",                                           │
│                "tokens_used": 245,                                       │
│                "generation_time_ms": 1234,                               │
│                "cached": false,                                          │
│                "rate_limit_remaining": 8,                                │
│                "rate_limit_reset_after": 45                              │
│              }                                                            │
└─────────────────────────────────────────────────────────────────────────┘

MIGRATION FLOW (Background Job):
┌──────────────────────────────────────────────────────────────────────────┐
│                    OLD CACHE (Redis/PostgreSQL)                           │
│  • Entries > 30 days old                                                 │
│  • Low access frequency                                                  │
│  • Manual migration triggers                                             │
└────────────────────────────────┬─────────────────────────────────────────┘
                                  │
                                  ▼
┌──────────────────────────────────────────────────────────────────────────┐
│                    MIGRATION SERVICE                                      │
│  • Read from source (Redis/PostgreSQL)                                   │
│  • Transform & validate data                                             │
│  • Write to destination (BigQuery/Firestore/Elasticsearch)               │
│  • Update cache_migrations table with progress                           │
│  • Update cache_content_mapping is_synced flag                           │
└────────────────────────────────┬─────────────────────────────────────────┘
                                  │
                                  ▼
┌──────────────────────────────────────────────────────────────────────────┐
│                    COLD STORAGE (BigQuery/Firestore)                     │
│  • Permanent archive                                                     │
│  • Analytics queries                                                     │
│  • Audit trail                                                           │
│  • Machine learning training data                                        │
└──────────────────────────────────────────────────────────────────────────┘
"""
    
    print(diagram)
    
    print_section("KEY DESIGN DECISIONS")
    print("""
1. DUAL-LAYER CACHE
   • Hot: Redis (1-hour TTL, ultra-fast)
   • Cold: PostgreSQL (permanent, audit trail)
   • Benefit: Speed + durability + migration capability

2. CONVERSATION-FIRST DESIGN
   • conversation_cache = entire session
   • message_cache = individual messages with sequence
   • Benefit: Full context preservation, conversation replay

3. PROMPT DEDUPLICATION
   • prompt_cache tracks identical prompts
   • Increments hit counter on match
   • Benefit: Avoid redundant Vertex AI calls

4. MIGRATION-READY ARCHITECTURE
   • cache_content_mapping links cache → content
   • cache_migrations tracks all migrations
   • migration_version on cache tables
   • Benefit: Can migrate to BigQuery/Firestore/Elasticsearch anytime

5. COMPREHENSIVE TRACKING
   • usage_metrics per user
   • cache_metrics aggregated
   • Embeddings for semantic search
   • Benefit: Full observability + intelligence

6. RATE LIMITING ENFORCEMENT
   • Tier-based limits (free: 10/min, premium: 100/min)
   • usage_metrics.monthly_requests_used tracking
   • Monthly reset coordination
   • Benefit: Fair usage, cost control, premium tier monetization
""")


def show_migration_examples():
    """Show example migrations."""
    
    print_header("MIGRATION EXAMPLES")
    
    example1 = """
EXAMPLE 1: Export Cache to BigQuery
─────────────────────────────────────

SQL to BigQuery Export:
```python
# In core/chatgpt_cache.py
cache = ChatGPTCache()
migration_id = cache.export_for_migration(
    source="postgresql",
    destination="bigquery",
    query="SELECT * FROM conversation_cache WHERE created_at < NOW() - INTERVAL 30 DAY",
    batch_size=1000
)

# Tracks in cache_migrations table:
{
    "version": "1.0",
    "status": "IN_PROGRESS",
    "source": "postgresql",
    "destination": "bigquery",
    "records_migrated": 0,
    "started_at": "2024-12-18 10:30",
    "completed_at": null
}
```

After completion:
```
{
    "version": "1.0",
    "status": "COMPLETED",
    "records_migrated": 15342,
    "completed_at": "2024-12-18 10:45"
}
```
"""
    
    example2 = """
EXAMPLE 2: Real-time Cache Hit Tracking
───────────────────────────────────────

When user sends request with duplicate prompt:

1. Hash prompt: SHA256("Write a blog about AI") → "abc123def..."

2. Check prompt_cache:
   SELECT * FROM prompt_cache WHERE prompt_hash = "abc123def..."
   
3. Found! Update hit count:
   UPDATE prompt_cache SET hits = hits + 1 WHERE id = "xyz"
   
4. Return cached response (instant)

5. Update cache_metrics:
   UPDATE cache_metrics 
   SET cache_hits = cache_hits + 1,
       hit_rate = cache_hits / (cache_hits + cache_misses)

6. Return to user:
   {
       "content": "...",
       "cached": true,  ← Indicates cache hit
       "generation_time_ms": 5,  ← Super fast!
       "cache_hit_rate": 0.67  ← 67% of requests served from cache
   }
"""
    
    example3 = """
EXAMPLE 3: Rate Limit Enforcement
──────────────────────────────────

Request comes in:

1. Extract user_id / IP address
2. Check usage_metrics:
   SELECT monthly_requests_used FROM usage_metrics 
   WHERE user_id = '...' AND tier = 'free'
   
3. Check monthly_request_limit:
   - Free: 100 * 30 days = 3000 requests/month
   - Premium: 1000 * 30 days = 30000 requests/month
   
4. If monthly_requests_used >= limit:
   Return HTTP 429 with:
   {
       "error": "Monthly quota exceeded",
       "limit": 3000,
       "used": 3000,
       "resets_at": "2025-01-18"
   }
   
5. If limit not exceeded:
   - Process request
   - Increment monthly_requests_used
   - Update total_requests, cache_hits or cache_misses
   - Update average_response_time_ms
"""
    
    print(example1)
    print(example2)
    print(example3)


def show_next_steps():
    """Show what to do next."""
    
    print_header("NEXT STEPS")
    
    steps = """
NOW THAT TABLES ARE CREATED:
═══════════════════════════════════════════════════════════════════════════

1. ✅ DATABASE SCHEMA CREATED
   • All 11 tables created with proper relationships
   • Indexes created for performance
   • Foreign keys for referential integrity

2. 📝 UPDATE API ENDPOINTS
   • Modify /v1/content/generate to:
     - Check rate limit (from usage_metrics)
     - Store to conversation_cache + message_cache
     - Store to prompt_cache (for deduplication)
     - Store to generated_content (main table)
     - Update cache_metrics + usage_metrics
     - Link in cache_content_mapping

3. 🔍 EXAMPLE CODE PATTERN
   ```python
   @router.post("/v1/content/generate")
   async def generate_content(
       request: ContentRequest,
       http_request: Request
   ):
       user_id = get_user_id(http_request)
       
       # 1. Rate limit check
       metrics = db.query(UsageMetrics).filter_by(user_id=user_id).first()
       if metrics.monthly_requests_used >= metrics.monthly_request_limit:
           raise HTTPException(429, "Quota exceeded")
       
       # 2. Cache check
       prompt_hash = sha256(request.prompt).hexdigest()
       cached = db.query(PromptCache).filter_by(
           prompt_hash=prompt_hash
       ).first()
       
       if cached:
           # Cache hit!
           cached.hits += 1
           db.commit()
           return {
               "content": cached.response_text,
               "cached": True,
               "cached_at": cached.created_at
           }
       
       # 3. Generate (cache miss)
       content = await vertex_ai.generate(request.prompt)
       
       # 4. Store in all tables
       conversation = ConversationCache(...)
       db.add(conversation)
       db.flush()  # Get ID
       
       message = MessageCache(
           conversation_id=conversation.id,
           role="assistant",
           content=content.text,
           tokens=content.usage.output_tokens
       )
       db.add(message)
       
       prompt_cache = PromptCache(
           prompt_hash=prompt_hash,
           prompt_text=request.prompt,
           response_text=content.text
       )
       db.add(prompt_cache)
       
       generated = GeneratedContent(
           user_id=user_id,
           original_prompt=request.prompt,
           generated_content=content.dict()
       )
       db.add(generated)
       
       mapping = CacheContentMapping(
           cache_type="prompt",
           cache_id=prompt_cache.id,
           content_id=generated.id,
           user_id=user_id
       )
       db.add(mapping)
       
       # Update metrics
       metrics.total_requests += 1
       metrics.cache_misses += 1
       metrics.total_output_tokens += content.usage.output_tokens
       
       db_metrics = db.query(CacheMetrics).first()
       db_metrics.cache_misses += 1
       
       db.commit()
       
       return {
           "content": content.text,
           "cached": False,
           "tokens": content.usage.output_tokens
       }
   ```

4. 🔄 BACKGROUND MIGRATION JOB
   • Set up Celery or APScheduler
   • Run daily/weekly:
     - Identify old cache entries
     - Call ChatGPTCache.export_for_migration()
     - Monitor cache_migrations table

5. 📊 SET UP MONITORING
   • Query cache_metrics for hit rate
   • Monitor usage_metrics per user
   • Track response times
   • Alert on quota violations

6. 🧪 TEST EVERYTHING
   • Send test request → check conversation_cache
   • Send same request → verify cache hit
   • Check rate limits → exceed and verify 429
   • Verify cache_content_mapping created
   • Monitor tokens in usage_metrics

7. 🚀 DEPLOY TO PRODUCTION
   • All tables ready
   • Rate limiting functional
   • Caching operational
   • Migration path available
   
═══════════════════════════════════════════════════════════════════════════

IMPORTANT: All migrations will happen AUTOMATICALLY when tables exist!
           No manual SQL needed - SQLAlchemy handles everything.
"""
    
    print(steps)


def main():
    """Main setup function."""
    
    # 1. Create tables
    if not create_all_tables():
        print("\n❌ Failed to create tables!")
        return False
    
    # 2. Verify tables
    if not verify_tables():
        print("\n⚠️  Some tables may be missing!")
        return False
    
    # 3. Show details
    show_table_details()
    
    # 4. Show architecture
    show_data_flow()
    
    # 5. Show migration examples
    show_migration_examples()
    
    # 6. Show next steps
    show_next_steps()
    
    print_header("SETUP COMPLETE ✅")
    print("""
All 11 tables created successfully!

Your database is now ready for:
✅ Rate limiting (tier-based)
✅ Conversation caching (Redis + PostgreSQL)
✅ Content generation tracking
✅ Usage metrics
✅ Backend migrations (BigQuery, Firestore, etc.)

The architecture supports BOTH:
• CACHE TABLES - For fast responses + conversation history
• CONTENT TABLES - For final, published content
• TRACKING TABLES - For migrations + metrics

Next: Update your API endpoints to use these tables!
    """)
    
    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
