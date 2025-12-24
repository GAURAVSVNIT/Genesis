"""Hashtag optimization with trending discovery and relevance scoring.

Provides intelligent hashtag suggestions based on:
- Content relevance
- Trending topics
- Platform-specific best practices
- Historical performance (when available)
"""

from typing import Dict, List, Optional
import asyncio
from collections import Counter
try:
    import httpx
    HTTPX_AVAILABLE = True
except ImportError:
    HTTPX_AVAILABLE = False


class HashtagOptimizer:
    """Optimizes hashtags for social media content.
    
    Features:
    - Relevance scoring
    - Trending hashtag discovery
    - Platform-appropriate counts
    - Mix of broad and niche tags
    """
    
    def __init__(self, enable_trending: bool = True):
        """Initialize hashtag optimizer.
        
        Args:
            enable_trending: Whether to fetch trending hashtags
        """
        self.enable_trending = enable_trending and HTTPX_AVAILABLE
        self._trending_cache = {}
    
    async def optimize(
        self,
        content: str,
        base_hashtags: List[str],
        platform: str = "general",
        max_count: int = None
    ) -> Dict:
        """Optimize hashtags for content.
        
        Args:
            content: Content to analyze
            base_hashtags: Initial hashtag suggestions
            platform: Target platform
            max_count: Maximum hashtags to return
        
        Returns:
            Dictionary with optimized hashtags and scores
        """
        # Clean and validate base hashtags
        cleaned = self._clean_hashtags(base_hashtags)
        
        # Score relevance to content
        scored = self._score_relevance(cleaned, content)
        
        # Get platform-specific count
        from .platform_rules import PlatformRules
        config = PlatformRules.get_config(platform)
        target_count = max_count or config.optimal_hashtags
        
        # Add trending if enabled
        if self.enable_trending:
            trending = await self._get_trending(platform)
            scored.extend([(tag, 0.8) for tag in trending if tag not in [h[0] for h in scored]])
        
        # Sort by score and select top
        scored.sort(key=lambda x: x[1], reverse=True)
        selected = [tag for tag, score in scored[:target_count]]
        
        # Categorize hashtags
        categorized = self._categorize_hashtags(selected, content)
        
        return {
            "hashtags": selected,
            "categorized": categorized,
            "scores": {tag: score for tag, score in scored[:target_count]},
            "total_count": len(selected),
            "platform_optimal": target_count
        }
    
    def _clean_hashtags(self, hashtags: List[str]) -> List[str]:
        """Clean and format hashtags."""
        cleaned = []
        for tag in hashtags:
            # Remove # if present
            tag = tag.strip().lstrip('#')
            # Remove spaces
            tag = tag.replace(' ', '')
            # Add back #
            if tag:
                cleaned.append(f"#{tag}")
        return list(dict.fromkeys(cleaned))  # Remove duplicates, preserve order
    
    def _score_relevance(self, hashtags: List[str], content: str) -> List[tuple]:
        """Score hashtag relevance to content.
        
        Returns:
            List of (hashtag, score) tuples
        """
        content_lower = content.lower()
        scored = []
        
        for tag in hashtags:
            tag_text = tag.lstrip('#').lower()
            
            # Check if tag appears in content
            if tag_text in content_lower:
                score = 1.0
            else:
                # Check word overlap
                tag_words = tag_text.split()
                content_words = content_lower.split()
                overlap = sum(1 for word in tag_words if word in content_words)
                score = overlap / len(tag_words) if tag_words else 0.5
            
            scored.append((tag, score))
        
        return scored
    
    async def _get_trending(self, platform: str) -> List[str]:
        """Get trending hashtags for platform."""
        # Check cache
        if platform in self._trending_cache:
            return self._trending_cache[platform]
            
        try:
            # Import here to avoid circular dependencies if any
            from intelligence.trend_collector import TrendCollector
            collector = TrendCollector()
            
            # Map platform names to collector sources
            source_map = {
                "twitter": "twitter",
                "linkedin": "linkedin", 
                "reddit": "reddit",
                "google": "google_trends"
            }
            
            # Default to checking all relevant sources for general/instagram
            sources = [source_map.get(platform)] if platform in source_map else None
            
            # Fetch trends for "technology" or general topics if no specific keywords provided
            # In a real scenario, we might want to pass context/keywords here
            trends = await collector.collect_all_trends(["technology", "innovation"], sources=sources)
            
            collected_tags = set()
            for topic in trends.get("trending_topics", []):
                # Extract hashtags from titles or create them
                title = topic.get("title", "")
                # Simple extraction of words > 4 chars as potential hashtags
                words = [w for w in title.split() if len(w) > 4 and w.isalnum()]
                for w in words[:2]:
                    collected_tags.add(f"#{w.capitalize()}")
                    
            if collected_tags:
                result = list(collected_tags)[:10]
                self._trending_cache[platform] = result
                return result
                
        except Exception as e:
            print(f"Error fetching trends: {e}")
            
        # Fallback to placeholders
        trending_by_platform = {
            "twitter": ["#Tech", "#Innovation", "#AI"],
            "instagram": ["#InstaDaily", "#PhotoOfTheDay", "#Love"],
            "linkedin": ["#Leadership", "#Innovation", "#Business"],
            "facebook": ["#Community", "#Family", "#Friends"],
            "general": ["#Trending", "#Popular", "#Viral"]
        }
        
        trending = trending_by_platform.get(platform, trending_by_platform["general"])
        self._trending_cache[platform] = trending
        
        return trending
    
    def _categorize_hashtags(self, hashtags: List[str], content: str) -> Dict:
        """Categorize hashtags as broad, niche, or branded.
        
        Returns:
            Dict with categories
        """
        # Simple heuristic categorization
        broad = []
        niche = []
        branded = []
        
        for tag in hashtags:
            tag_text = tag.lstrip('#').lower()
            
            # Check if in content (likely branded/niche)
            if tag_text in content.lower():
                if len(tag_text) > 15:
                    branded.append(tag)
                else:
                    niche.append(tag)
            else:
                # Likely broad/trending
                broad.append(tag)
        
        return {
            "broad": broad,
            "niche": niche,
            "branded": branded
        }
    
    def suggest_hashtag_strategy(self, platform: str) -> Dict:
        """Get hashtag strategy recommendations for platform."""
        from .platform_rules import PlatformRules
        config = PlatformRules.get_config(platform)
        
        strategies = {
            "twitter": {
                "recommendation": "Use 1-2 highly relevant hashtags",
                "placement": "End of tweet",
                "tips": [
                    "Focus on trending topics when relevant",
                    "Use hashtags that are already popular",
                    "Avoid hashtag stuffing"
                ]
            },
            "instagram": {
                "recommendation": "Use 10-15 relevant hashtags minimum",
                "placement": "First comment or after line break",
                "tips": [
                    "Mix popular (100k-1M) and niche (1k-10k) hashtags",
                    "Use 5 broad + 5 medium + 5 niche strategy",
                    "Research competitor hashtags",
                    "Create a branded hashtag"
                ]
            },
            "linkedin": {
                "recommendation": "Use 3-5 professional hashtags",
                "placement": "End of post",
                "tips": [
                    "Use industry-specific hashtags",
                    "Include skill-based hashtags",
                    "Mix broad professional terms with niche topics"
                ]
            },
            "facebook": {
                "recommendation": "Use 0-2 hashtags sparingly",
                "placement": "End of post",
                "tips": [
                    "Hashtags less effective on Facebook",
                    "Use only for specific campaigns",
                    "Focus on content quality over hashtags"
                ]
            }
        }
        
        return strategies.get(platform, {
            "recommendation": f"Use {config.optimal_hashtags} relevant hashtags",
            "placement": config.hashtag_placement,
            "tips": ["Research your audience", "Test different combinations"]
        })
