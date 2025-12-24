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
        self.twitter_api_key = os.getenv("TWITTER_API_KEY")
        self.twitter_api_secret = os.getenv("TWITTER_API_SECRET")
        
        self.reddit_client_id = os.getenv("REDDIT_CLIENT_ID")
        self.reddit_client_secret = os.getenv("REDDIT_CLIENT_SECRET")
        self.reddit_user_agent = os.getenv("REDDIT_USER_AGENT", "TrendAnalyzer/1.0")
        self.serper_api_key = os.getenv("SERPER_API_KEY")
        self.use_cache = use_cache
        self.cache_ttl = 1800  # 30 minutes
        
    async def _get_twitter_token(self) -> Optional[str]:
        """Generate Bearer Token from API Key/Secret if needed."""
        if self.twitter_bearer_token:
            return self.twitter_bearer_token
            
        if not self.twitter_api_key or not self.twitter_api_secret:
            return None
            
        try:
            import base64
            credentials = f"{self.twitter_api_key}:{self.twitter_api_secret}"
            encoded_creds = base64.b64encode(credentials.encode()).decode()
            
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(
                    "https://api.twitter.com/oauth2/token",
                    headers={
                        "Authorization": f"Basic {encoded_creds}",
                        "Content-Type": "application/x-www-form-urlencoded;charset=UTF-8"
                    },
                    data={"grant_type": "client_credentials"}
                )
                
                if response.status_code == 200:
                    data = response.json()
                    token = data.get("access_token")
                    if token:
                        self.twitter_bearer_token = token  # Cache it
                        return token
                        
            print("❌ Failed to generate Twitter Bearer Token")
        except Exception as e:
            print(f"❌ Error generating Twitter token: {e}")
            
        return None
        
    def _get_cache_key(self, keywords: List[str], sources: List[str]) -> str:
        """Generate cache key for trend data."""
        keyword_str = "-".join(sorted(keywords))
        source_str = "-".join(sorted(sources))
        return f"trends:data:{keyword_str}:{source_str}"
    
    def get_available_sources(self) -> List[str]:
        """Get list of sources that have API keys configured."""
        available = []
        
        if self.serper_api_key:
            available.append("google_trends")
        
        if self.twitter_bearer_token or (self.twitter_api_key and self.twitter_api_secret):
            available.append("twitter")
        
        if self.reddit_client_id and self.reddit_client_secret:
            available.append("reddit")
        
        # LinkedIn doesn't require API key (placeholder)
        # available.append("linkedin")
        
        return available

    async def collect_all_trends(
        self,
        keywords: List[str],
        sources: Optional[List[str]] = None
    ) -> Dict:
        """
        Collect trends from multiple sources concurrently with Redis caching.
        Only uses sources that have API keys configured.
        
        Args:
            keywords: List of keywords to analyze
            sources: List of sources to use (auto-detects available if None)
            
        Returns:
            Aggregated trend data from all sources
        """
        # Auto-detect available sources if not specified
        if not sources:
            sources = self.get_available_sources()
            if not sources:
                print("⚠️ No API keys configured. Using mock data for testing.")
                return self._get_mock_trends(keywords)
        else:
            # Filter sources to only those available
            available_sources = self.get_available_sources()
            sources = [s for s in sources if s in available_sources]
            
            if not sources:
                print(f"⚠️ None of the requested sources have API keys configured.")
                print(f"   Available sources: {available_sources if available_sources else 'None'}")
                return self._get_mock_trends(keywords)
        
        print(f"📡 Using sources: {sources}")
        
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
        if self.use_cache and aggregated["trending_topics"]:
            await self._cache_trends(keywords, sources, aggregated)

        return aggregated
    
    def _get_mock_trends(self, keywords: List[str]) -> Dict:
        """Generate mock trend data when no APIs are available."""
        mock_topics = [
            {
                "title": f"Latest developments in {keywords[0] if keywords else 'technology'}",
                "snippet": "Mock trend data for testing without API keys",
                "source": "mock",
                "type": "placeholder",
                "relevance_score": 50
            },
            {
                "title": f"Understanding {keywords[0] if keywords else 'innovation'} trends",
                "snippet": "This is placeholder data. Configure API keys for real trends.",
                "source": "mock",
                "type": "placeholder",
                "relevance_score": 45
            },
            {
                "title": f"How {keywords[0] if keywords else 'AI'} is changing the industry",
                "snippet": "Add SERPER_API_KEY to .env for Google Trends data",
                "source": "mock",
                "type": "placeholder",
                "relevance_score": 40
            }
        ]
        
        return {
            "timestamp": datetime.now().isoformat(),
            "keywords": keywords,
            "sources": {"mock": {"note": "No API keys configured. Add API keys to .env for real data."}},
            "trending_topics": mock_topics,
            "summary": {
                "total_topics": len(mock_topics),
                "sources_count": 0,
                "fetched_at": datetime.now().isoformat(),
                "is_mock_data": True
            },
            "from_cache": False
        }
    
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
        # Get token (either cached or generated)
        token = await self._get_twitter_token()
        
        if not token:
            return {"error": "Twitter API credentials not configured", "trending_topics": []}

        query = " OR ".join(keywords)
        
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                # Search for recent tweets
                response = await client.get(
                    "https://api.twitter.com/2/tweets/search/recent",
                    headers={
                        "Authorization": f"Bearer {token}"
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
