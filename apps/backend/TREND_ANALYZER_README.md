# Trend Analyzer - Latest Trends for AI Content Generation

## Overview

The Trend Analyzer fetches the latest trends from multiple sources (Google Trends, Twitter/X, Reddit, LinkedIn) to enhance AI content generation with current, relevant information.

## Features

✅ **Asynchronous Data Fetching** - Concurrent API calls for minimal latency  
✅ **Multi-Source Integration** - Google Trends, Twitter/X, Reddit, LinkedIn  
✅ **Smart Scoring System** - Relevance scoring based on multiple factors  
✅ **Redis Caching** - 30-minute TTL for faster responses and reduced API calls  
✅ **Tone Detection** - Automatic detection of content tone from prompts  
✅ **Keyword Extraction** - Intelligent keyword extraction with tone analysis  
✅ **Generation Context** - Optimized insights for content generation  
✅ **RESTful API** - Easy integration with your frontend  

## Architecture

```
┌─────────────────────────────────────────────────────┐
│              Trend Analyzer System                   │
│                                                      │
│  ┌──────────────────────────────────────────────┐   │
│  │  TrendCollector (Async)                      │   │
│  │  ├─ Google Trends (Serper API)              │   │
│  │  ├─ Twitter/X API                            │   │
│  │  ├─ Reddit API                               │   │
│  │  └─ LinkedIn (Web Scraping)                  │   │
│  └──────────────────────────────────────────────┘   │
│                      ↓                               │
│  ┌──────────────────────────────────────────────┐   │
│  │  TrendAnalyzer                               │   │
│  │  ├─ Topic Scoring                            │   │
│  │  ├─ Relevance Analysis                       │   │
│  │  ├─ Insights Generation                      │   │
│  │  └─ Content Recommendations                  │   │
│  └──────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────┘
```

## Setup Instructions

### 1. Install Dependencies

```bash
cd d:\padhai\GENECIS\Genesis\apps\backend
pip install -r requirements.txt
```

### 2. Configure API Keys

Copy the example environment file:

```bash
cp .env.example .env
```

Edit `.env` and add your API keys:

```env
# Serper API (for Google Trends)
SERPER_API_KEY=your_serper_api_key_here

# Twitter/X API
TWITTER_BEARER_TOKEN=your_twitter_bearer_token_here

# Reddit API
REDDIT_CLIENT_ID=your_reddit_client_id_here
REDDIT_CLIENT_SECRET=your_reddit_client_secret_here
REDDIT_USER_AGENT=TrendAnalyzer/1.0
```

### 3. Get API Keys

#### Serper API (Google Trends)
1. Go to [https://serper.dev/](https://serper.dev/)
2. Sign up for a free account
3. Get your API key from the dashboard
4. Free tier: 100 requests/month

#### Twitter/X API
1. Go to [https://developer.twitter.com/](https://developer.twitter.com/)
2. Create a developer account
3. Create a new app
4. Generate a Bearer Token
5. Free tier: Limited requests

#### Reddit API
1. Go to [https://www.reddit.com/prefs/apps](https://www.reddit.com/prefs/apps)
2. Click "Create App" or "Create Another App"
3. Select "script" as the app type
4. Copy your `client_id` and `client_secret`
5. Free tier: Generous rate limits

### 4. Start the Backend

```bash
python -m uvicorn main:app --reload --port 8000
```

## API Endpoints

### 1. Analyze Trends

**POST** `/api/v1/trends/analyze`

Analyze trends for given keywords with full context.

```json
{
  "keywords": ["AI", "healthcare"],
  "sources": ["google_trends", "twitter", "reddit"],
  "prompt": "Write an article about AI in healthcare",
  "tone": "professional"
}
```

**Response:**
```json
{
  "timestamp": "2025-12-18T10:30:00",
  "keywords": ["AI", "healthcare"],
  "detected_tone": "professional",
  "overall_score": 85.5,
  "trending_topics": [...],
  "insights": [...],
  "recommendations": [...],
  "generation_context": {
    "trend_keywords": [...],
    "trending_angles": [...],
    "suggested_tone": "professional and informative",
    "target_audience": "professionals and business audience"
  }
}
```

### 2. Extract Keywords and Tone

**POST** `/api/v1/trends/extract-keywords-tone?prompt=Your prompt here`

Extract keywords and detect tone from any text.

**Response:**
```json
{
  "prompt": "Write a professional article about AI",
  "keywords": ["professional", "article", "AI"],
  "detected_tone": "professional",
  "tone_confidence": "high"
}
```

### 3. Get Top Trends

**GET** `/api/v1/trends/top?keywords=AI,healthcare&limit=10`

Get top trending topics.

**Response:**
```json
{
  "total_count": 25,
  "trends": [...],
  "overall_score": 85.5,
  "insights": [...]
}
```

### 4. Generate Trend Context

**POST** `/api/v1/trends/generate-context?prompt=Write about AI&keywords=AI,innovation`

Generate trend-based context for content generation.

**Response:**
```json
{
  "prompt": "Write about AI",
  "extracted_keywords": ["AI", "innovation"],
  "detected_tone": "informative",
  "trend_context": {...},
  "top_trends": [...],
  "recommendations": [...]
}
```

### 5. Get Available Sources

**GET** `/api/v1/trends/sources`

List all available trend sources.

### 6. Invalidate Cache

**DELETE** `/api/v1/trends/cache?keywords=AI,healthcare&sources=google_trends`

Clear cached trend data for specific keywords.

**Response:**
```json
{
  "status": "success",
  "message": "Cache invalidated for keywords: ['AI', 'healthcare']"
}
```

### 7. Get Cache Statistics

**GET** `/api/v1/trends/cache/stats`

Get Redis cache information and statistics.

**Response:**
```json
{
  "cache_enabled": true,
  "cache_ttl": 1800,
  "redis_connected": true
}
```

## Redis Caching

The trend analyzer uses **Redis for caching** to improve performance and reduce API costs.

### Cache Benefits:

✅ **Faster Responses** - Cached data returns instantly  
✅ **Reduced API Calls** - Save on API quota and costs  
✅ **Better Performance** - 30-minute TTL for frequently requested trends  
✅ **Rate Limit Protection** - Avoid hitting API rate limits  

### Cache Configuration:

- **TTL**: 30 minutes (1800 seconds)
- **Key Format**: `trends:data:{keywords}:{sources}`
- **Storage**: Upstash Redis (already configured)

### Usage Example:

```python
from intelligence.trend_collector import TrendCollector

# With caching (default)
collector = TrendCollector(use_cache=True)
trends = await collector.collect_all_trends(["AI", "healthcare"])

# Check if from cache
if trends.get("from_cache"):
    print("Using cached data")
else:
    print("Fresh data fetched")

# Disable cache
collector_no_cache = TrendCollector(use_cache=False)
trends = await collector_no_cache.collect_all_trends(["AI"])

# Invalidate cache
await collector.invalidate_cache(["AI", "healthcare"])
```

### Cache Management:

```bash
# Invalidate specific cache
curl -X DELETE "http://localhost:8000/api/v1/trends/cache?keywords=AI,healthcare"

# Get cache stats
curl "http://localhost:8000/api/v1/trends/cache/stats"
```

## Tone Detection

The system automatically detects the tone of your content from the prompt and uses it to enhance trend analysis.

### Supported Tones:

- **Professional** - Business, corporate, enterprise content
- **Casual** - Friendly, fun, everyday content
- **Technical** - Advanced, detailed, expert-level content
- **Educational** - Learning, tutorials, guides
- **Persuasive** - Convincing, argumentative content
- **Informative** - Factual, objective information
- **Urgent** - Breaking news, time-sensitive content
- **Analytical** - Comparative, evaluative content

### Example:

```python
from intelligence.trend_analyzer import TrendAnalyzer

analyzer = TrendAnalyzer()

# Extract keywords and tone together
keywords, tone = analyzer.extract_keywords_and_tone(
    "Write a professional business report about AI"
)

print(f"Keywords: {keywords}")  # ['professional', 'business', 'report', 'AI']
print(f"Tone: {tone}")  # 'professional'
```

## Usage Example

### Python Example

```python
import httpx
import asyncio

async def fetch_trends():
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://localhost:8000/api/v1/trends/analyze",
            json={
                "keywords": ["AI", "healthcare"],
                "sources": ["google_trends", "reddit"],
                "prompt": "Write an article about AI in healthcare"
            }
        )
        data = response.json()
        
        print(f"Overall Score: {data['overall_score']}")
        print(f"Top Trends: {data['trending_topics'][:5]}")
        print(f"Recommendations: {data['recommendations']}")

asyncio.run(fetch_trends())
```

### cURL Example

```bash
curl -X POST "http://localhost:8000/api/v1/trends/analyze" \
  -H "Content-Type: application/json" \
  -d '{
    "keywords": ["AI", "healthcare"],
    "sources": ["google_trends", "reddit"]
  }'
```

## Scoring System

Each trend topic is scored based on:

- **Keyword Match (40%)** - How well the topic matches your keywords
- **Source Credibility (20%)** - Trustworthiness of the source
- **Engagement (20%)** - Social metrics (likes, shares, scores)
- **Recency (10%)** - How recent the trend is
- **Quality (10%)** - Content quality indicators

**Score Range:** 0-100 (higher is more relevant)

## Performance

- **Latency:** ~2-5 seconds for multi-source fetch
- **Concurrent Requests:** All sources fetched in parallel
- **Rate Limiting:** Respects API rate limits
- **Caching:** Can be added for improved performance

## Troubleshooting

### API Key Errors

```
Error: "Serper API key not configured"
```

**Solution:** Add `SERPER_API_KEY` to your `.env` file.

### Import Errors

```
ModuleNotFoundError: No module named 'httpx'
```

**Solution:** Run `pip install -r requirements.txt`

### CORS Issues

If you get CORS errors from frontend:

1. Check that frontend URL is in allowed origins (main.py)
2. Restart the backend server

## Next Steps

1. ✅ **Add Caching** - Implement Redis caching for trend data
2. ✅ **Rate Limiting** - Add rate limiting to prevent API abuse
3. ✅ **Historical Tracking** - Store trends in database for historical analysis
4. ✅ **Real-time Updates** - WebSocket support for live trend updates
5. ✅ **Frontend Dashboard** - Create React components for visualization

## Contributing

To add a new trend source:

1. Add async method to `TrendCollector`
2. Update `collect_all_trends()` to include the new source
3. Add source configuration to `.env.example`
4. Update this README

## License

Part of the Genesis AI Content Creation platform.
