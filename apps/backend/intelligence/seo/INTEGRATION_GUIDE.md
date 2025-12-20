# SEO Optimizer - Complete Integration Guide

## 📋 Table of Contents
1. [Quick Start](#quick-start)
2. [API Key Setup](#api-key-setup)
3. [Basic Usage](#basic-usage)
4. [Backend Integration](#backend-integration)
5. [Frontend Connection](#frontend-connection)
6. [Database Integration](#database-integration)
7. [Advanced Usage](#advanced-usage)
8. [Deployment](#deployment)

---

## 🚀 Quick Start

### 1. Set Up API Key

**Get Gemini API Key:**
- Go to https://makersuite.google.com/app/apikey
- Create/Get your API key

**Set Environment Variable:**

```bash
# Windows PowerShell
$env:GOOGLE_API_KEY="your_api_key_here"

# Windows CMD
set GOOGLE_API_KEY=your_api_key_here

# Linux/Mac
export GOOGLE_API_KEY=your_api_key_here
```

**Or use .env file:**
```env
# .env file in backend directory
GOOGLE_API_KEY=your_api_key_here
```

### 2. Install Dependencies

```bash
pip install langchain-google-genai pydantic python-dotenv textstat httpx
```

---

## 🔑 API Key Setup

### Method 1: Environment Variable

```python
import os
os.environ["GOOGLE_API_KEY"] = "your_api_key"
```

### Method 2: .env File

Create `.env` file:
```env
GOOGLE_API_KEY=AIzaSy...your_key_here
```

Load in your code:
```python
from dotenv import load_dotenv
load_dotenv()
```

### Method 3: Direct Configuration

```python
from intelligence.seo import SEOOptimizer, SEOConfig

config = SEOConfig()
# API key will be loaded from environment
optimizer = SEOOptimizer(config)
```

---

## 💻 Basic Usage

### Example 1: Simple Optimization

```python
import asyncio
from intelligence.seo import SEOOptimizer

async def optimize_content():
    # Initialize optimizer
    optimizer = SEOOptimizer()
    
    # Your content
    content = """
    Artificial intelligence is transforming healthcare. 
    Doctors now use AI for faster and more accurate diagnoses.
    """
    
    # Optimize
    result = await optimizer.optimize(
        content=content,
        keywords=["AI", "healthcare", "diagnosis"],
        platform="linkedin",
        tone="professional"
    )
    
    # Results
    print(f"SEO Score: {result['seo_score']}/100")
    print(f"\nOptimized Content:\n{result['optimized_content']}")
    print(f"\nHashtags: {', '.join(result['hashtags'])}")
    print(f"\nMeta Description:\n{result['meta_description']}")
    
    return result

# Run
if __name__ == "__main__":
    result = asyncio.run(optimize_content())
```

### Example 2: With Custom Configuration

```python
from intelligence.seo import SEOOptimizer, SEOConfig

# Custom config
config = SEOConfig(
    temperature=0.8,          # More creative
    keyword_weight=35.0,      # Higher keyword importance
    readability_weight=25.0,  # Higher readability importance
    max_retries=5             # More retries
)

optimizer = SEOOptimizer(config)
result = await optimizer.optimize(...)
```

### Example 3: Platform-Specific

```python
# For Twitter
twitter_result = await optimizer.optimize(
    content="AI is changing the world!",
    keywords=["AI", "innovation"],
    platform="twitter",        # 280 char limit
    tone="casual"
)

# For LinkedIn
linkedin_result = await optimizer.optimize(
    content="Long-form professional content...",
    keywords=["leadership", "business"],
    platform="linkedin",       # 3000 char limit
    tone="professional"
)

# For Blog
blog_result = await optimizer.optimize(
    content="Full blog post content...",
    keywords=["tutorial", "guide"],
    platform="blog",           # 50000 char limit
    tone="informative",
    title="Complete Guide to...",
    generate_metadata=True     # Get OG tags, Schema.org
)
```

---

## 🔌 Backend Integration

### Integration with FastAPI (main.py)

```python
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from intelligence.seo import SEOOptimizer, SEOConfig
import asyncio

app = FastAPI()

# Initialize optimizer once
config = SEOConfig()
seo_optimizer = SEOOptimizer(config)

class SEORequest(BaseModel):
    content: str
    keywords: List[str]
    platform: str = "general"
    tone: str = "professional"
    title: Optional[str] = None
    generate_metadata: bool = False

class SEOResponse(BaseModel):
    seo_score: float
    optimized_content: str
    meta_description: str
    hashtags: List[str]
    title_options: List[str]
    call_to_action: str
    suggestions: List[str]
    keyword_analysis: dict
    readability: dict
    platform_compliance: dict

@app.post("/api/seo/optimize", response_model=SEOResponse)
async def optimize_content(request: SEORequest):
    """Optimize content for SEO."""
    try:
        result = await seo_optimizer.optimize(
            content=request.content,
            keywords=request.keywords,
            platform=request.platform,
            tone=request.tone,
            title=request.title,
            generate_metadata=request.generate_metadata
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/seo/platforms")
async def get_platforms():
    """Get available platforms and their rules."""
    from intelligence.seo import PlatformRules
    
    platforms = {}
    for name, config in PlatformRules.PLATFORMS.items():
        platforms[name] = {
            "name": config.name,
            "optimal_length": config.optimal_length,
            "max_length": config.max_length,
            "optimal_hashtags": config.optimal_hashtags,
            "max_hashtags": config.max_hashtags
        }
    return platforms

@app.post("/api/seo/analyze-keywords")
async def analyze_keywords(content: str, keywords: List[str]):
    """Analyze keyword usage in content."""
    from intelligence.seo import KeywordAnalyzer
    
    analyzer = KeywordAnalyzer()
    result = await analyzer.analyze(content, keywords)
    return result

@app.post("/api/seo/analyze-readability")
async def analyze_readability(content: str):
    """Analyze content readability."""
    from intelligence.seo import ReadabilityAnalyzer
    
    analyzer = ReadabilityAnalyzer()
    result = analyzer.analyze(content)
    return result

@app.post("/api/seo/generate-metadata")
async def generate_metadata(content: str, keywords: List[str], title: str):
    """Generate SEO metadata."""
    from intelligence.seo import MetadataGenerator, SEOConfig
    
    config = SEOConfig()
    generator = MetadataGenerator(config)
    result = await generator.generate(content, keywords, title)
    return result

# Run with: uvicorn main:app --reload --port 8000
```

### Test Your API

```bash
# Terminal 1: Start server
cd D:\padhai\GENECIS\Genesis\apps\backend
uvicorn main:app --reload --port 8000

# Terminal 2: Test endpoint
curl -X POST "http://localhost:8000/api/seo/optimize" \
  -H "Content-Type: application/json" \
  -d '{
    "content": "AI is transforming healthcare",
    "keywords": ["AI", "healthcare"],
    "platform": "twitter"
  }'
```

---

## 🌐 Frontend Connection

### Example 1: Fetch from React/Next.js

```javascript
// Frontend API call
async function optimizeContent(content, keywords, platform) {
  const response = await fetch('http://localhost:8000/api/seo/optimize', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      content,
      keywords,
      platform,
      tone: 'professional',
      generate_metadata: true
    })
  });
  
  if (!response.ok) {
    throw new Error('SEO optimization failed');
  }
  
  return await response.json();
}

// Usage in component
const handleOptimize = async () => {
  try {
    const result = await optimizeContent(
      userContent,
      ['AI', 'tech'],
      'linkedin'
    );
    
    setSeoScore(result.seo_score);
    setOptimizedContent(result.optimized_content);
    setHashtags(result.hashtags);
    setSuggestions(result.suggestions);
  } catch (error) {
    console.error('Error:', error);
  }
};
```

### Example 2: Vue.js Integration

```javascript
// In Vue component
export default {
  data() {
    return {
      content: '',
      keywords: [],
      platform: 'general',
      result: null,
      loading: false
    }
  },
  methods: {
    async optimizeContent() {
      this.loading = true;
      try {
        const response = await axios.post('/api/seo/optimize', {
          content: this.content,
          keywords: this.keywords,
          platform: this.platform
        });
        this.result = response.data;
      } catch (error) {
        console.error('Optimization error:', error);
      } finally {
        this.loading = false;
      }
    }
  }
}
```

### Example 3: Real-time Analysis

```javascript
// Debounced real-time analysis
import { debounce } from 'lodash';

const analyzeRealTime = debounce(async (content, keywords) => {
  const response = await fetch('/api/seo/analyze-keywords', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ content, keywords })
  });
  
  const analysis = await response.json();
  updateUI(analysis);
}, 1000); // Wait 1 second after user stops typing

// In your input handler
onContentChange = (newContent) => {
  setContent(newContent);
  analyzeRealTime(newContent, keywords);
};
```

---

## 💾 Database Integration

### Save Results to Database

```python
from sqlalchemy import Column, Integer, String, Float, JSON, DateTime
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()

class SEOOptimization(Base):
    __tablename__ = "seo_optimizations"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer)
    original_content = Column(String)
    optimized_content = Column(String)
    seo_score = Column(Float)
    keywords = Column(JSON)
    platform = Column(String)
    hashtags = Column(JSON)
    meta_description = Column(String)
    suggestions = Column(JSON)
    keyword_analysis = Column(JSON)
    readability = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)

# FastAPI endpoint with DB
@app.post("/api/seo/optimize")
async def optimize_and_save(request: SEORequest, user_id: int, db: Session):
    # Optimize
    result = await seo_optimizer.optimize(
        content=request.content,
        keywords=request.keywords,
        platform=request.platform
    )
    
    # Save to database
    optimization = SEOOptimization(
        user_id=user_id,
        original_content=request.content,
        optimized_content=result["optimized_content"],
        seo_score=result["seo_score"],
        keywords=request.keywords,
        platform=request.platform,
        hashtags=result["hashtags"],
        meta_description=result["meta_description"],
        suggestions=result["suggestions"],
        keyword_analysis=result["keyword_analysis"],
        readability=result["readability"]
    )
    db.add(optimization)
    db.commit()
    
    return result
```

---

## 🎯 Advanced Usage

### 1. Batch Processing

```python
async def optimize_multiple(contents: List[dict]):
    """Optimize multiple pieces of content."""
    tasks = []
    for item in contents:
        task = optimizer.optimize(
            content=item['content'],
            keywords=item['keywords'],
            platform=item['platform']
        )
        tasks.append(task)
    
    results = await asyncio.gather(*tasks)
    return results

# Usage
contents = [
    {"content": "Post 1...", "keywords": ["AI"], "platform": "twitter"},
    {"content": "Post 2...", "keywords": ["tech"], "platform": "linkedin"},
]
results = await optimize_multiple(contents)
```

### 2. Custom Scoring Weights

```python
# E-commerce focus (keywords + CTA more important)
ecommerce_config = SEOConfig(
    keyword_weight=35.0,
    cta_weight=20.0,
    readability_weight=15.0,
    meta_weight=15.0,
    hashtag_weight=10.0,
    title_weight=5.0
)

# Content marketing focus (readability + meta more important)
content_config = SEOConfig(
    readability_weight=30.0,
    meta_weight=25.0,
    keyword_weight=20.0,
    title_weight=15.0,
    hashtag_weight=5.0,
    cta_weight=5.0
)
```

### 3. A/B Testing Different Tones

```python
async def test_tones(content, keywords, platform):
    """Test different tones and return all results."""
    tones = ["professional", "casual", "inspirational"]
    results = {}
    
    for tone in tones:
        result = await optimizer.optimize(
            content=content,
            keywords=keywords,
            platform=platform,
            tone=tone
        )
        results[tone] = {
            "score": result["seo_score"],
            "content": result["optimized_content"]
        }
    
    # Return best scoring version
    best = max(results.items(), key=lambda x: x[1]["score"])
    return best

# Usage
best_tone, best_result = await test_tones(content, keywords, "linkedin")
print(f"Best tone: {best_tone} with score {best_result['score']}")
```

### 4. Webhook Integration

```python
# Send results to external service
import httpx

@app.post("/api/seo/optimize-with-webhook")
async def optimize_with_webhook(request: SEORequest, webhook_url: str):
    result = await seo_optimizer.optimize(...)
    
    # Send to webhook
    async with httpx.AsyncClient() as client:
        await client.post(webhook_url, json={
            "event": "seo_optimization_complete",
            "data": result
        })
    
    return result
```

---

## 🚀 Deployment

### 1. Environment Variables in Production

```bash
# .env.production
GOOGLE_API_KEY=your_production_key
SEO_TEMPERATURE=0.7
SEO_MAX_RETRIES=3
DATABASE_URL=postgresql://...
```

### 2. Docker Deployment

```dockerfile
# Dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV GOOGLE_API_KEY=""
ENV PORT=8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

```yaml
# docker-compose.yml
version: '3.8'

services:
  backend:
    build: .
    ports:
      - "8000:8000"
    environment:
      - GOOGLE_API_KEY=${GOOGLE_API_KEY}
    volumes:
      - ./intelligence:/app/intelligence
```

### 3. CORS Configuration

```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "https://yourdomain.com"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

---

## 📊 Monitoring & Logging

```python
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@app.post("/api/seo/optimize")
async def optimize_content(request: SEORequest):
    logger.info(f"Optimization request - Platform: {request.platform}, Keywords: {request.keywords}")
    
    try:
        result = await seo_optimizer.optimize(...)
        logger.info(f"Optimization successful - Score: {result['seo_score']}")
        return result
    except Exception as e:
        logger.error(f"Optimization failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
```

---

## 🧪 Testing

```python
# Test with pytest
import pytest
from intelligence.seo import SEOOptimizer

@pytest.mark.asyncio
async def test_optimization():
    optimizer = SEOOptimizer()
    result = await optimizer.optimize(
        content="Test content",
        keywords=["test"],
        platform="general"
    )
    
    assert result["seo_score"] > 0
    assert len(result["optimized_content"]) > 0
    assert len(result["hashtags"]) > 0

# Run tests
# pytest tests/test_seo.py
```

---

## 📞 Support & Resources

**Documentation:** `intelligence/seo/README.md`  
**Test Script:** `test_seo_final.py`  
**Demo:** `intelligence/demo_seo_complete.py` (requires API key)  
**Location:** `intelligence/seo/`

**Platforms Supported:**
- Twitter/X (280 chars)
- LinkedIn (3000 chars)
- Instagram (2200 chars)
- Facebook (63,206 chars)
- Blog/Website (50,000 chars)
- General (10,000 chars)

**Components:**
- SEOOptimizer (main)
- KeywordAnalyzer
- ReadabilityAnalyzer
- HashtagOptimizer
- MetadataGenerator
- SuggestionGenerator
- PlatformRules
- SEOConfig

---

**Version:** 2.0.0  
**Status:** Production Ready  
**Last Updated:** December 21, 2025
