"""Asynchronous trend collector from multiple sources."""

import asyncio
from typing import Dict, List, Optional
import httpx
from datetime import datetime
import os
import json
from core.upstash_redis import UpstashRedisClient


class TrendCollector:
    """Collect trends from Google Trends, Twitter/X, Reddit, and LinkedIn asynchronously."""

    def __init__(self, use_cache: bool = True):
        """Initialize the trend collector with API credentials."""
        self.twitter_bearer_token = os.getenv("TWITTER_BEARER_TOKEN")
        self.reddit_client_id = os.getenv("REDDIT_CLIENT_ID")
        self.reddit_client_secret = os.getenv("REDDIT_CLIENT_SECRET")
        self.reddit_user_agent = os.getenv("REDDIT_USER_AGENT", "TrendAnalyzer/1.0")
        self.serper_api_key = os.getenv("SERPER_API_KEY")
        self.use_cache = use_cache
        self.cache_ttl = 1800  # 30 minutes
        
    def _get_cache_key(self, keywords: List[str], sources: List[str]) -> str:
        """Generate cache key for trend data."""
        keyword_str = "-".join(sorted(keywords))
        source_str = "-".join(sorted(sources))
        return f"trends:data:{keyword_str}:{source_str}"

    async def collect_all_trends(
        self,
        keywords: List[str],
        sources: Optional[List[str]] = None
    ) -> Dict:
        """
        Collect trends from multiple sources concurrently with Redis caching.
        
        Args:
            keywords: List of keywords to analyze
            sources: List of sources to use (defaults to all available)
            
        Returns:
            Aggregated trend data from all sources
        """
        if not sources:
            sources = ["google_trends", "twitter", "reddit", "linkedin"]
        
        # Check cache first
        if self.use_cache:
            cached_data = await self._get_cached_trends(keywords, sources)
            if cached_data:
                print(f"✅ Using cached trends for: {keywords}")
                cached_data["from_cache"] = True
                return cached_data
        
        print(f"⏳ Fetching fresh trends for: {keywords}")
        
        # Create tasks for all sources concurrently
        tasks = []
        if "google_trends" in sources:
            tasks.append(self._fetch_google_trends(keywords))
        if "twitter" in sources:
            tasks.append(self._fetch_twitter_trends(keywords))
        if "reddit" in sources:
            tasks.append(self._fetch_reddit_trends(keywords))
        if "linkedin" in sources:
            tasks.append(self._fetch_linkedin_trends(keywords))

        # Execute all tasks concurrently
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Aggregate results
        aggregated = {
            "timestamp": datetime.now().isoformat(),
            "keywords": keywords,
            "sources": {},
            "trending_topics": [],
            "summary": {},
            "from_cache": False
        }

        # Map results to source names
        source_mapping = []
        if "google_trends" in sources:
            source_mapping.append("google_trends")
        if "twitter" in sources:
            source_mapping.append("twitter")
        if "reddit" in sources:
            source_mapping.append("reddit")
        if "linkedin" in sources:
            source_mapping.append("linkedin")

        for source, result in zip(source_mapping, results):
            if not isinstance(result, Exception):
                aggregated["sources"][source] = result
                if "trending_topics" in result:
                    aggregated["trending_topics"].extend(result["trending_topics"])

        # Deduplicate topics
        aggregated["trending_topics"] = self._deduplicate_topics(
            aggregated["trending_topics"]
        )

        # Add summary statistics
        aggregated["summary"] = {
            "total_topics": len(aggregated["trending_topics"]),
            "sources_count": len(aggregated["sources"]),
            "fetched_at": datetime.now().isoformat()
        }
        
        # Cache the results
        if self.use_cache:
            await self._cache_trends(keywords, sources, aggregated)

        return aggregated
    
    async def _get_cached_trends(self, keywords: List[str], sources: List[str]) -> Optional[Dict]:
        """Get cached trend data from Redis."""
        try:
            redis_client = UpstashRedisClient.get_instance()
            cache_key = self._get_cache_key(keywords, sources)
            
            cached_data = redis_client.get(cache_key)
            if cached_data:
                return json.loads(cached_data)
        except Exception as e:
            print(f"Redis cache read error: {e}")
        return None
    
    async def _cache_trends(self, keywords: List[str], sources: List[str], data: Dict):
        """Cache trend data in Redis."""
        try:
            redis_client = UpstashRedisClient.get_instance()
            cache_key = self._get_cache_key(keywords, sources)
            
            redis_client.setex(cache_key, self.cache_ttl, json.dumps(data))
            print(f"💾 Cached trends for: {keywords} (TTL: {self.cache_ttl}s)")
        except Exception as e:
            print(f"Redis cache write error: {e}")
    
    async def invalidate_cache(self, keywords: List[str], sources: Optional[List[str]] = None):
        """Invalidate cached trend data."""
        try:
            redis_client = UpstashRedisClient.get_instance()
            if not sources:
                sources = ["google_trends", "twitter", "reddit", "linkedin"]
            
            cache_key = self._get_cache_key(keywords, sources)
            redis_client.delete(cache_key)
            print(f"🗑️ Invalidated cache for: {keywords}")
        except Exception as e:
            print(f"Redis cache invalidation error: {e}")

    async def _fetch_google_trends(self, keywords: List[str]) -> Dict:
        """
        Fetch Google Trends data using Serper API.
        
        Args:
            keywords: Keywords to search for
            
        Returns:
            Google trends data
        """
        if not self.serper_api_key:
            return {"error": "Serper API key not configured", "trending_topics": []}

        query = " ".join(keywords)
        
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                # Fetch search trends
                response = await client.post(
                    "https://google.serper.dev/search",
                    headers={
                        "X-API-KEY": self.serper_api_key,
                        "Content-Type": "application/json"
                    },
                    json={
                        "q": query,
                        "gl": "us",
                        "hl": "en",
                        "num": 20
                    }
                )
                
                if response.status_code != 200:
                    return {"error": f"API error: {response.status_code}", "trending_topics": []}
                
                data = response.json()
                
                return {
                    "trending_topics": [
                        {
                            "title": item.get("title", ""),
                            "url": item.get("link", ""),
                            "snippet": item.get("snippet", ""),
                            "source": "google",
                            "type": "search"
                        }
                        for item in data.get("organic", [])[:10]
                    ],
                    "related_searches": data.get("relatedSearches", []),
                    "people_also_ask": data.get("peopleAlsoAsk", [])
                }
                
        except Exception as e:
            return {"error": str(e), "trending_topics": []}

    async def _fetch_twitter_trends(self, keywords: List[str]) -> Dict:
        """
        Fetch Twitter/X trends.
        
        Args:
            keywords: Keywords to search for
            
        Returns:
            Twitter trends data
        """
        if not self.twitter_bearer_token:
            return {"error": "Twitter API token not configured", "trending_topics": []}

        query = " OR ".join(keywords)
        
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                # Search for recent tweets
                response = await client.get(
                    "https://api.twitter.com/2/tweets/search/recent",
                    headers={
                        "Authorization": f"Bearer {self.twitter_bearer_token}"
                    },
                    params={
                        "query": query,
                        "max_results": 10,
                        "tweet.fields": "public_metrics,created_at"
                    }
                )
                
                if response.status_code != 200:
                    return {"error": f"API error: {response.status_code}", "trending_topics": []}
                
                data = response.json()
                
                return {
                    "trending_topics": [
                        {
                            "title": tweet.get("text", "")[:100] + "...",
                            "engagement": tweet.get("public_metrics", {}).get("like_count", 0),
                            "source": "twitter",
                            "type": "social",
                            "created_at": tweet.get("created_at")
                        }
                        for tweet in data.get("data", [])
                    ]
                }
                
        except Exception as e:
            return {"error": str(e), "trending_topics": []}

    async def _fetch_reddit_trends(self, keywords: List[str]) -> Dict:
        """
        Fetch Reddit trends.
        
        Args:
            keywords: Keywords to search for
            
        Returns:
            Reddit trends data
        """
        if not self.reddit_client_id or not self.reddit_client_secret:
            return {"error": "Reddit API credentials not configured", "trending_topics": []}

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                # Get access token
                auth_response = await client.post(
                    "https://www.reddit.com/api/v1/access_token",
                    auth=(self.reddit_client_id, self.reddit_client_secret),
                    data={"grant_type": "client_credentials"},
                    headers={"User-Agent": self.reddit_user_agent}
                )
                
                if auth_response.status_code != 200:
                    return {"error": "Reddit auth failed", "trending_topics": []}
                
                access_token = auth_response.json().get("access_token")
                
                # Search for posts
                query = " ".join(keywords)
                search_response = await client.get(
                    "https://oauth.reddit.com/search",
                    headers={
                        "Authorization": f"Bearer {access_token}",
                        "User-Agent": self.reddit_user_agent
                    },
                    params={
                        "q": query,
                        "sort": "hot",
                        "limit": 10,
                        "t": "day"
                    }
                )
                
                if search_response.status_code != 200:
                    return {"error": "Reddit search failed", "trending_topics": []}
                
                data = search_response.json()
                
                return {
                    "trending_topics": [
                        {
                            "title": post.get("data", {}).get("title", ""),
                            "url": post.get("data", {}).get("url", ""),
                            "score": post.get("data", {}).get("score", 0),
                            "source": "reddit",
                            "type": "social",
                            "subreddit": post.get("data", {}).get("subreddit", "")
                        }
                        for post in data.get("data", {}).get("children", [])
                    ]
                }
                
        except Exception as e:
            return {"error": str(e), "trending_topics": []}

    async def _fetch_linkedin_trends(self, keywords: List[str]) -> Dict:
        """
        Fetch LinkedIn trends using web scraping.
        
        Note: LinkedIn doesn't provide a public API, so this is a placeholder.
        Full implementation would require authentication and proper scraping.
        
        Args:
            keywords: Keywords to search for
            
        Returns:
            LinkedIn trends data
        """
        # LinkedIn requires authentication for most content
        # This is a placeholder that returns mock data
        return {
            "trending_topics": [],
            "note": "LinkedIn integration requires authentication and is not yet implemented"
        }

    def _deduplicate_topics(self, topics: List[Dict]) -> List[Dict]:
        """
        Remove duplicate topics based on title similarity.
        
        Args:
            topics: List of trend topics
            
        Returns:
            Deduplicated list of topics
        """
        seen_titles = set()
        unique_topics = []
        
        for topic in topics:
            title = topic.get("title", "").lower().strip()
            
            if title and title not in seen_titles and len(title) > 10:
                seen_titles.add(title)
                unique_topics.append(topic)
        
        return unique_topics[:25]  # Return top 25 unique topics
