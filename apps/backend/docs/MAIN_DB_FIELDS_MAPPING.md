# 📊 Main Database Fields Mapping - What's Being Captured

## Summary: ⚠️ PARTIALLY - Main DB missing quality scores & embeddings

---

## 📝 GENERATED_CONTENT - Main Content Storage

### Fields Being Captured ✅

| Field | Source | Status | Purpose |
|-------|--------|--------|---------|
| `user_id` | Request context | ✅ Stored | Content owner |
| `conversation_id` | Generated UUID | ✅ Stored | Session link |
| `message_id` | Assistant message ID | ✅ Stored | Message link |
| `original_prompt` | request.prompt | ✅ Stored | Audit trail |
| `requirements` | safety_level dict | ✅ Stored | Configuration |
| `content_type` | Hard-coded "text" | ✅ Stored | Media type |
| `platform` | Hard-coded "api" | ✅ Stored | Destination |
| `generated_content` | Full response JSONB | ✅ Stored | Actual content |
| `status` | "generated" | ✅ Stored | Workflow state |
| `created_at` | Auto-timestamp | ✅ Stored | Creation time |
| `updated_at` | Auto-timestamp | ✅ Stored | Last update |

### Fields NOT Being Captured ❌

| Field | Why Not | Should Capture |
|-------|---------|-----------------|
| `seo_score` | No SEO analysis | Need SEO API/plugin |
| `uniqueness_score` | No plagiarism check | Need plagiarism API |
| `engagement_score` | No ML analysis | Need engagement classifier |
| `published_platforms` | Not published yet | Will set on publish |
| `published_at` | Not published yet | Will set on publish |
| `published_urls` | Not published yet | Will set on publish |
| `tags` | No auto-generation | Could add NLP tagging |

---

## 📊 CONTENT_EMBEDDINGS - Vector Search

### Fields Being Captured ❌ **NONE - NOT IMPLEMENTED YET**

| Field | Should Capture | Status |
|-------|-----------------|--------|
| `content_id` | generated_content.id | ❌ Missing |
| `text_source` | "generated_content" | ❌ Missing |
| `source_id` | content ID | ❌ Missing |
| `embedded_text` | Generated content text | ❌ Missing |
| `text_length` | Character count | ❌ Missing |
| `text_tokens` | Token count | ❌ Missing |
| `embedding` | Vector embedding array | ❌ Missing |
| `embedding_model` | Model used (e.g., all-MiniLM-L6-v2) | ❌ Missing |
| `embedding_dimensions` | Size (e.g., 384) | ❌ Missing |
| `confidence_score` | Quality metric | ❌ Missing |
| `is_valid` | Quality check | ❌ Missing |

**Why Missing:** No embedding service is called - would need to integrate with embedding model (e.g., Sentence Transformers, OpenAI Embeddings)

---

## 📊 USAGE_METRICS - Per-User Tracking

### Fields Being Captured ✅

| Field | Source | Status | Purpose |
|-------|--------|--------|---------|
| `user_id` | Request context | ✅ Stored | User tracking |
| `total_requests` | Incremented | ✅ Stored | Request counter |
| `cache_hits` | Incremented | ✅ Stored | Cache hit counter |
| `cache_misses` | Incremented | ✅ Stored | Cache miss counter |
| `total_input_tokens` | Rough estimate | ✅ Stored | Input tracking |
| `total_output_tokens` | Rough estimate | ✅ Stored | Output tracking |
| `total_tokens` | Sum | ✅ Stored | Total tracking |
| `average_response_time_ms` | Calculated | ✅ Stored | Performance |
| `cache_hit_rate` | hits / total | ✅ Stored | Efficiency |
| `tier` | From param | ✅ Stored | User tier |
| `monthly_request_limit` | From tier | ✅ Stored | Rate limit |
| `monthly_requests_used` | Incremented | ✅ Stored | Monthly tracking |

### Fields NOT Being Captured ❌

| Field | Why Not | Should Capture |
|-------|---------|-----------------|
| `total_cost` | No pricing config | Need cost calculation |
| `cache_cost` | No pricing config | Need cache cost rates |

---

## 🔗 CACHE_CONTENT_MAPPING - Linking

### Fields Being Captured ✅

| Field | Source | Status | Purpose |
|-------|--------|--------|---------|
| `cache_type` | "prompt" | ✅ Stored | Cache table type |
| `cache_id` | prompt_cache.id | ✅ Stored | Cache entry |
| `content_id` | generated_content.id | ✅ Stored | Content entry |
| `user_id` | Request context | ✅ Stored | User tracking |
| `cache_backend` | "postgresql" | ✅ Stored | Cache location |
| `content_backend` | "postgresql" | ✅ Stored | Content location |
| `is_synced` | true | ✅ Stored | Sync status |
| `last_synced_at` | datetime.now() | ✅ Stored | Sync time |
| `created_at` | Auto-timestamp | ✅ Stored | Creation time |
| `updated_at` | Auto-timestamp | ✅ Stored | Last update |

---

## 📈 Comparison: Cache vs Main DB

| Aspect | Cache Tables | Main Tables | Gap |
|--------|--------------|------------|-----|
| **Prompt Tracking** | ✅ Hash + text | ✅ Text only | Minor |
| **Message Sequence** | ✅ Full sequence | ❌ None | Major |
| **Hit Counting** | ✅ Incremented | ❌ N/A | N/A |
| **Quality Scores** | ❌ N/A | ❌ Not captured | Major |
| **Embeddings** | ✅ Vectors stored | ❌ Not created | Major |
| **Performance Metrics** | ✅ Generation time | ✅ Response time | Minor |
| **User Metrics** | ❌ Individual | ✅ Aggregated | Different scope |
| **Cost Tracking** | ❌ N/A | ❌ Not tracked | Major |
| **Migration Ready** | ✅ Full support | ✅ Via mapping | Good |

---

## 🚨 What Needs to Be Added to Main DB

### 1. Quality Score Calculation

**What's needed:**
```python
# After content generation, calculate:
seo_score = await calculate_seo_score(content)        # 0-1
uniqueness_score = await check_plagiarism(content)    # 0-1
engagement_score = await predict_engagement(content)  # 0-1
```

**Update endpoint:**
```python
generated_content = GeneratedContent(
    # ... existing fields ...
    seo_score=seo_score,                 # ← Add this
    uniqueness_score=uniqueness_score,   # ← Add this
    engagement_score=engagement_score,   # ← Add this
)
```

---

### 2. Content Embeddings Creation

**What's needed:**
```python
# After content generation, create embedding:
from sentence_transformers import SentenceTransformer

model = SentenceTransformer('all-MiniLM-L6-v2')
embedding_vector = model.encode(content)

content_embedding = ContentEmbedding(
    content_id=generated_content.id,
    text_source="generated_content",
    source_id=generated_content.id,
    embedded_text=content,
    text_length=len(content),
    text_tokens=len(content.split()),
    embedding=embedding_vector.tolist(),  # Convert to list
    embedding_model="all-MiniLM-L6-v2",
    embedding_dimensions=384,
    confidence_score=1.0,
    is_valid=True
)
db.add(content_embedding)
```

---

### 3. Cost Calculation

**What's needed:**
```python
# After tracking tokens, calculate cost:
INPUT_COST_PER_1K = 0.00075   # gemini-2.0-flash
OUTPUT_COST_PER_1K = 0.003

input_cost = (input_tokens / 1000) * INPUT_COST_PER_1K
output_cost = (output_tokens / 1000) * OUTPUT_COST_PER_1K
total_request_cost = input_cost + output_cost

user_metrics.total_cost += total_request_cost
user_metrics.cache_cost += 0  # Cache hits have $0 cost

# For cache hits:
user_metrics.cache_cost += 0  # No cost for cached response
```

---

## ✅ Current Main DB Capture Summary

```
✅ Basic Content Storage
  ├─ user_id
  ├─ prompt (original)
  ├─ response (generated)
  ├─ timestamp
  └─ status (draft/published/archived)

✅ Relationship Tracking
  ├─ conversation_id (session link)
  ├─ message_id (message link)
  └─ cache_content_mapping (migration link)

✅ Configuration Tracking
  ├─ platform
  ├─ safety_level
  └─ content_type

⚠️ Partially Implemented
  ├─ usage_metrics (tracks requests but not costs)
  └─ published info (fields exist but not populated)

❌ Missing Completely
  ├─ Quality scores (seo, uniqueness, engagement)
  ├─ Content embeddings (vectors for search)
  ├─ Cost tracking (pricing per request)
  └─ Published URLs (distribution tracking)
```

---

## 🎯 Recommendation: Priority Order to Add

### 🔴 High Priority (Use Immediately)
1. **Cost Calculation** - Track spending
2. **Content Embeddings** - Enable semantic search

### 🟡 Medium Priority (Add Soon)
3. **Quality Scores** - Track content quality
4. **Publishing Metadata** - Track distribution

### 🟢 Low Priority (Nice to Have)
5. **Auto-Tagging** - Automatic categorization
6. **Advanced Metrics** - Performance analytics

---

## 📋 Conclusion

| Aspect | Status |
|--------|--------|
| **Cache Tables** | ✅ 95% complete |
| **Main DB Content** | ⚠️ 60% complete |
| **Main DB Metrics** | ⚠️ 60% complete |
| **Main DB Quality** | ❌ 0% complete |
| **Embeddings** | ❌ 0% complete |

**Cache is production-ready. Main DB needs:**
- Quality score calculation
- Embedding generation
- Cost tracking
- Publishing workflow

Would you like me to implement any of these?
