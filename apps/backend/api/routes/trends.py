"""API routes for trend analysis."""

from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
from pydantic import BaseModel
from intelligence.trend_collector import TrendCollector
from intelligence.trend_analyzer import TrendAnalyzer


router = APIRouter(prefix="/api/v1/trends", tags=["trends"])


class TrendAnalysisRequest(BaseModel):
    """Request model for trend analysis."""
    keywords: List[str]
    sources: Optional[List[str]] = None
    prompt: Optional[str] = None
    tone: Optional[str] = None


class TrendAnalysisResponse(BaseModel):
    """Response model for trend analysis."""
    timestamp: str
    keywords: List[str]
    detected_tone: Optional[str] = None
    overall_score: float
    trending_topics: List[dict]
    insights: List[str]
    recommendations: List[str]
    generation_context: Optional[dict] = None


@router.post("/analyze", response_model=TrendAnalysisResponse)
async def analyze_trends(request: TrendAnalysisRequest):
    """
    Analyze trends for given keywords with Redis caching.
    
    - **keywords**: List of keywords to analyze
    - **sources**: Optional list of sources (google_trends, twitter, reddit, linkedin)
    - **prompt**: Optional generation prompt for context
    - **tone**: Optional tone specification
    """
    try:
        # Initialize services (cache enabled by default)
        collector = TrendCollector(use_cache=True)
        analyzer = TrendAnalyzer()
        
        # Collect trends (uses Redis cache)
        trend_data = await collector.collect_all_trends(
            keywords=request.keywords,
            sources=request.sources
        )
        
        # Analyze trends
        if request.prompt:
            analysis = await analyzer.analyze_for_generation(
                prompt=request.prompt,
                keywords=request.keywords,
                trend_data=trend_data
            )
        else:
            analysis = await analyzer.analyze_trends(
                keywords=request.keywords,
                trend_data=trend_data,
                prompt=request.prompt,
                tone=request.tone
            )
        
        # Add cache info
        analysis["cached"] = trend_data.get("from_cache", False)
        
        return analysis
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Trend analysis failed: {str(e)}")


@router.get("/top")
async def get_top_trends(
    keywords: str = Query(..., description="Comma-separated keywords"),
    limit: int = Query(10, ge=1, le=50, description="Number of trends to return"),
    sources: Optional[str] = Query(None, description="Comma-separated sources")
):
    """
    Get top trending topics for given keywords.
    
    - **keywords**: Comma-separated keywords (e.g., "AI,healthcare")
    - **limit**: Number of trends to return (1-50)
    - **sources**: Optional comma-separated sources
    """
    try:
        # Parse keywords
        keyword_list = [k.strip() for k in keywords.split(",")]
        source_list = [s.strip() for s in sources.split(",")] if sources else None
        
        # Initialize services
        collector = TrendCollector()
        analyzer = TrendAnalyzer()
        
        # Collect and analyze trends
        trend_data = await collector.collect_all_trends(
            keywords=keyword_list,
            sources=source_list
        )
        
        analysis = await analyzer.analyze_trends(
            keywords=keyword_list,
            trend_data=trend_data
        )
        
        # Return top N topics
        top_topics = analysis["trending_topics"][:limit]
        
        return {
            "total_count": len(analysis["trending_topics"]),
            "trends": top_topics,
            "overall_score": analysis["overall_score"],
            "insights": analysis["insights"]
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch trends: {str(e)}")


@router.get("/sources")
async def get_available_sources():
    """
    Get list of available trend sources with their configuration status.
    """
    collector = TrendCollector()
    available_sources = collector.get_available_sources()
    
    all_sources = [
        {
            "id": "google_trends",
            "name": "Google Trends",
            "description": "Search trends and related queries from Google",
            "enabled": "google_trends" in available_sources,
            "requires": "SERPER_API_KEY"
        },
        {
            "id": "twitter",
            "name": "Twitter/X",
            "description": "Trending topics and hashtags from Twitter/X",
            "enabled": "twitter" in available_sources,
            "requires": "TWITTER_BEARER_TOKEN"
        },
        {
            "id": "reddit",
            "name": "Reddit",
            "description": "Trending posts and discussions from Reddit",
            "enabled": "reddit" in available_sources,
            "requires": "REDDIT_CLIENT_ID, REDDIT_CLIENT_SECRET"
        },
        {
            "id": "linkedin",
            "name": "LinkedIn",
            "description": "Professional trends from LinkedIn (limited)",
            "enabled": False,
            "requires": "Not available"
        }
    ]
    
    return {
        "sources": all_sources,
        "available_count": len(available_sources),
        "total_count": len(all_sources),
        "available_sources": available_sources
    }


@router.post("/generate-context")
async def generate_trend_context(
    prompt: str = Query(..., description="Generation prompt"),
    keywords: Optional[str] = Query(None, description="Comma-separated keywords (auto-extracted if not provided)")
):
    """
    Generate trend-based context for content generation.
    
    - **prompt**: The content generation prompt
    - **keywords**: Optional keywords (will be extracted from prompt if not provided)
    """
    try:
        # Initialize analyzer
        analyzer = TrendAnalyzer()
        
        # Extract keywords and tone if not provided
        if keywords:
            keyword_list = [k.strip() for k in keywords.split(",")]
            detected_tone = analyzer._detect_tone(prompt)
        else:
            # Use the new method to extract both
            keyword_list, detected_tone = analyzer.extract_keywords_and_tone(prompt)
        
        # Initialize services
        collector = TrendCollector()
        
        # Collect and analyze trends
        trend_data = await collector.collect_all_trends(keywords=keyword_list)
        analysis = await analyzer.analyze_for_generation(
            prompt=prompt,
            keywords=keyword_list,
            trend_data=trend_data
        )
        
        return {
            "prompt": prompt,
            "extracted_keywords": keyword_list,
            "detected_tone": detected_tone,
            "trend_context": analysis.get("generation_context", {}),
            "top_trends": analysis["trending_topics"][:5],
            "recommendations": analysis["recommendations"]
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate context: {str(e)}")


@router.post("/extract-keywords-tone")
async def extract_keywords_and_tone(
    prompt: str = Query(..., description="Text to analyze")
):
    """
    Extract keywords and detect tone from a prompt.
    
    - **prompt**: The text to analyze
    """
    try:
        analyzer = TrendAnalyzer()
        keywords, tone = analyzer.extract_keywords_and_tone(prompt)
        
        return {
            "prompt": prompt,
            "keywords": keywords,
            "detected_tone": tone,
            "tone_confidence": "high" if len(keywords) > 2 else "medium"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to extract: {str(e)}")


@router.delete("/cache")
async def invalidate_trend_cache(
    keywords: str = Query(..., description="Comma-separated keywords"),
    sources: Optional[str] = Query(None, description="Comma-separated sources")
):
    """
    Invalidate cached trend data for specific keywords.
    
    - **keywords**: Comma-separated keywords
    - **sources**: Optional comma-separated sources
    """
    try:
        keyword_list = [k.strip() for k in keywords.split(",")]
        source_list = [s.strip() for s in sources.split(",")] if sources else None
        
        collector = TrendCollector()
        await collector.invalidate_cache(keyword_list, source_list)
        
        return {
            "status": "success",
            "message": f"Cache invalidated for keywords: {keyword_list}"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Cache invalidation failed: {str(e)}")


@router.get("/cache/stats")
async def get_cache_stats():
    """
    Get Redis cache statistics for trend data.
    """
    try:
        from core.upstash_redis import UpstashRedisClient
        redis_client = UpstashRedisClient.get_instance()
        
        # Get all trend cache keys
        # Note: This is a simplified version, adjust based on your Redis setup
        return {
            "cache_enabled": True,
            "cache_ttl": 1800,
            "redis_connected": redis_client.ping() if hasattr(redis_client, 'ping') else True
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get cache stats: {str(e)}")
