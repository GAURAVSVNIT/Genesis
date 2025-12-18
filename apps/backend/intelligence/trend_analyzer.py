"""Trend analysis and scoring service."""

import asyncio
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import math
import re


class TrendAnalyzer:
    """Analyze and score trends for content generation."""

    def __init__(self):
        """Initialize the trend analyzer."""
        self.min_score = 0
        self.max_score = 100
        
        # Tone indicators for detection
        self.tone_indicators = {
            "professional": ["business", "corporate", "professional", "executive", "enterprise", "industry"],
            "casual": ["friendly", "casual", "fun", "easy", "simple", "everyday"],
            "technical": ["technical", "advanced", "detailed", "in-depth", "comprehensive", "expert"],
            "educational": ["learn", "tutorial", "guide", "explain", "understand", "beginner"],
            "persuasive": ["convince", "persuade", "why", "benefits", "advantages", "should"],
            "informative": ["information", "facts", "about", "overview", "introduction", "what"],
            "urgent": ["urgent", "now", "immediately", "breaking", "alert", "latest"],
            "analytical": ["analyze", "compare", "evaluate", "assess", "review", "examine"]
        }

    async def analyze_trends(
        self,
        keywords: List[str],
        trend_data: Dict,
        prompt: Optional[str] = None,
        tone: Optional[str] = None
    ) -> Dict:
        """
        Analyze trends and calculate relevance scores.
        
        Args:
            keywords: Keywords from the generation prompt
            trend_data: Raw trend data from TrendCollector
            prompt: Original generation prompt (optional)
            tone: Detected or specified tone (optional)
            
        Returns:
            Analyzed trend data with scores and insights
        """
        # Detect tone if not provided
        if not tone and prompt:
            tone = self._detect_tone(prompt)
        
        analyzed = {
            "timestamp": datetime.now().isoformat(),
            "keywords": keywords,
            "detected_tone": tone,
            "overall_score": 0,
            "trending_topics": [],
            "insights": [],
            "recommendations": []
        }

        # Score each topic
        scored_topics = []
        for topic in trend_data.get("trending_topics", []):
            score = self._calculate_topic_score(topic, keywords, prompt)
            topic["relevance_score"] = score
            scored_topics.append(topic)

        # Sort by relevance score
        scored_topics.sort(key=lambda x: x.get("relevance_score", 0), reverse=True)
        analyzed["trending_topics"] = scored_topics

        # Calculate overall trend score
        if scored_topics:
            top_scores = [t.get("relevance_score", 0) for t in scored_topics[:5]]
            analyzed["overall_score"] = sum(top_scores) / len(top_scores)

        # Generate insights
        analyzed["insights"] = self._generate_insights(
            scored_topics,
            trend_data,
            keywords
        )

        # Generate recommendations
        analyzed["recommendations"] = self._generate_recommendations(
            scored_topics,
            keywords
        )

        return analyzed

    def _calculate_topic_score(
        self,
        topic: Dict,
        keywords: List[str],
        prompt: Optional[str] = None
    ) -> float:
        """
        Calculate relevance score for a single topic.
        
        Args:
            topic: Topic data
            keywords: Search keywords
            prompt: Original prompt
            
        Returns:
            Relevance score (0-100)
        """
        score = 0.0

        # Keyword matching (40 points)
        keyword_score = self._calculate_keyword_match(topic, keywords)
        score += keyword_score * 0.4

        # Source credibility (20 points)
        source_score = self._calculate_source_score(topic)
        score += source_score * 0.2

        # Engagement metrics (20 points)
        engagement_score = self._calculate_engagement_score(topic)
        score += engagement_score * 0.2

        # Recency (10 points)
        recency_score = self._calculate_recency_score(topic)
        score += recency_score * 0.1

        # Content quality (10 points)
        quality_score = self._calculate_quality_score(topic)
        score += quality_score * 0.1

        return min(self.max_score, max(self.min_score, score))

    def _calculate_keyword_match(self, topic: Dict, keywords: List[str]) -> float:
        """Calculate keyword matching score."""
        title = topic.get("title", "").lower()
        snippet = topic.get("snippet", "").lower()
        combined_text = f"{title} {snippet}"

        matches = 0
        for keyword in keywords:
            if keyword.lower() in combined_text:
                matches += 1

        # Calculate percentage match
        if keywords:
            match_percentage = (matches / len(keywords)) * 100
            return min(100, match_percentage)

        return 0.0

    def _calculate_source_score(self, topic: Dict) -> float:
        """Calculate source credibility score."""
        source = topic.get("source", "").lower()
        topic_type = topic.get("type", "").lower()

        # Score based on source credibility
        source_scores = {
            "google": 90,
            "twitter": 70,
            "reddit": 65,
            "linkedin": 80,
            "news": 85
        }

        type_scores = {
            "news": 85,
            "search": 80,
            "social": 65
        }

        base_score = source_scores.get(source, 50)
        type_score = type_scores.get(topic_type, 50)

        return (base_score + type_score) / 2

    def _calculate_engagement_score(self, topic: Dict) -> float:
        """Calculate engagement score based on metrics."""
        score = 50  # Base score

        # Check for engagement metrics
        engagement = topic.get("engagement", 0)
        reddit_score = topic.get("score", 0)

        if engagement > 0:
            # Logarithmic scaling for engagement
            score += min(30, math.log(engagement + 1) * 5)

        if reddit_score > 0:
            score += min(30, math.log(reddit_score + 1) * 5)

        # Check for URL (indicates full content)
        if topic.get("url"):
            score += 10

        # Check for snippet (indicates detailed info)
        if topic.get("snippet"):
            score += 10

        return min(100, score)

    def _calculate_recency_score(self, topic: Dict) -> float:
        """Calculate recency score."""
        created_at = topic.get("created_at")

        if not created_at:
            return 50  # Default score if no timestamp

        try:
            created_time = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
            age_hours = (datetime.now() - created_time).total_seconds() / 3600

            # Newer is better
            if age_hours < 1:
                return 100
            elif age_hours < 6:
                return 90
            elif age_hours < 24:
                return 75
            elif age_hours < 72:
                return 50
            else:
                return 30

        except Exception:
            return 50

    def _calculate_quality_score(self, topic: Dict) -> float:
        """Calculate content quality score."""
        score = 50  # Base score

        title = topic.get("title", "")
        snippet = topic.get("snippet", "")

        # Title quality
        if len(title) > 20:
            score += 20
        elif len(title) > 10:
            score += 10

        # Snippet quality
        if len(snippet) > 50:
            score += 20
        elif len(snippet) > 20:
            score += 10

        # Check for special characters or spam indicators
        spam_indicators = ["!!!", "click here", "buy now", "limited time"]
        text = f"{title} {snippet}".lower()

        for indicator in spam_indicators:
            if indicator in text:
                score -= 20

        return max(0, min(100, score))

    def _generate_insights(
        self,
        scored_topics: List[Dict],
        trend_data: Dict,
        keywords: List[str]
    ) -> List[str]:
        """Generate insights from trend data."""
        insights = []

        # Number of trending topics
        topic_count = len(scored_topics)
        insights.append(f"Found {topic_count} trending topics related to your keywords.")

        # Top source
        if scored_topics:
            sources = {}
            for topic in scored_topics[:10]:
                source = topic.get("source", "unknown")
                sources[source] = sources.get(source, 0) + 1

            top_source = max(sources.items(), key=lambda x: x[1])
            insights.append(f"Most trending content is from {top_source[0]} ({top_source[1]} items).")

        # High relevance topics
        high_relevance = [t for t in scored_topics if t.get("relevance_score", 0) > 70]
        if high_relevance:
            insights.append(f"{len(high_relevance)} topics have high relevance (>70% match).")
        else:
            insights.append("No highly relevant topics found. Consider broadening your keywords.")

        # Source diversity
        unique_sources = len(trend_data.get("sources", {}))
        insights.append(f"Data collected from {unique_sources} different sources.")

        return insights

    def _generate_recommendations(
        self,
        scored_topics: List[Dict],
        keywords: List[str]
    ) -> List[str]:
        """Generate recommendations for content generation."""
        recommendations = []

        if not scored_topics:
            return ["No trends found. Try different keywords."]

        # Top trending topics
        top_topics = scored_topics[:3]
        if top_topics:
            recommendations.append(
                f"Focus on these trending topics: {', '.join([t.get('title', '')[:50] for t in top_topics])}"
            )

        # Keyword suggestions
        all_titles = " ".join([t.get("title", "") for t in scored_topics[:10]])
        common_words = self._extract_common_words(all_titles, keywords)
        if common_words:
            recommendations.append(
                f"Consider incorporating these trending keywords: {', '.join(common_words[:5])}"
            )

        # Source recommendations
        sources_used = set(t.get("source") for t in scored_topics[:10])
        if "news" in sources_used:
            recommendations.append("News sources are actively covering this topic - consider a timely angle.")

        if "reddit" in sources_used:
            recommendations.append("Active community discussions - consider addressing common questions.")

        return recommendations

    def _extract_common_words(self, text: str, exclude_words: List[str]) -> List[str]:
        """Extract common words from text."""
        # Remove punctuation and convert to lowercase
        words = re.findall(r'\b[a-z]{4,}\b', text.lower())

        # Exclude stop words and existing keywords
        stop_words = {"this", "that", "with", "from", "have", "been", "will", "your", "more", "about", "into", "what", "when", "where", "which", "write", "create"}
        exclude_set = set(w.lower() for w in exclude_words) | stop_words

        # Count word frequency
        word_freq = {}
        for word in words:
            if word not in exclude_set:
                word_freq[word] = word_freq.get(word, 0) + 1

        # Sort by frequency
        sorted_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)

        # Return words (removed frequency > 1 requirement for short prompts)
        return [word for word, freq in sorted_words[:10]]

    async def analyze_for_generation(
        self,
        prompt: str,
        keywords: List[str],
        trend_data: Dict
    ) -> Dict:
        """
        Analyze trends specifically for content generation.
        
        Args:
            prompt: Generation prompt
            keywords: Extracted keywords
            trend_data: Trend data from collector
            
        Returns:
            Analysis optimized for content generation
        """
        # Detect tone from prompt
        detected_tone = self._detect_tone(prompt)
        
        # Perform standard analysis with tone
        analysis = await self.analyze_trends(keywords, trend_data, prompt, detected_tone)

        # Add generation-specific insights
        top_topics = analysis["trending_topics"][:5]
        
        generation_context = {
            "trend_keywords": self._extract_trend_keywords(top_topics),
            "trending_angles": self._extract_trending_angles(top_topics),
            "suggested_tone": self._suggest_tone(top_topics),
            "target_audience": self._identify_audience(top_topics)
        }

        analysis["generation_context"] = generation_context

        return analysis

    def _extract_trend_keywords(self, topics: List[Dict]) -> List[str]:
        """Extract keywords from trending topics."""
        all_text = " ".join([
            f"{t.get('title', '')} {t.get('snippet', '')}"
            for t in topics
        ])

        return self._extract_common_words(all_text, [])[:10]

    def _extract_trending_angles(self, topics: List[Dict]) -> List[str]:
        """Extract trending angles/perspectives."""
        angles = []

        for topic in topics[:5]:
            title = topic.get("title", "")
            if title:
                angles.append(title[:80])

        return angles

    def _suggest_tone(self, topics: List[Dict]) -> str:
        """Suggest content tone based on trends."""
        sources = [t.get("source", "") for t in topics]

        if "news" in sources:
            return "professional and informative"
        elif "reddit" in sources or "twitter" in sources:
            return "conversational and engaging"
        else:
            return "balanced and authoritative"

    def _identify_audience(self, topics: List[Dict]) -> str:
        """Identify target audience based on trends."""
        sources = [t.get("source", "") for t in topics]

        if "linkedin" in sources:
            return "professionals and business audience"
        elif "reddit" in sources:
            return "engaged community members"
        elif "twitter" in sources:
            return "social media users and general public"
        else:
            return "general audience"
    
    def _detect_tone(self, text: str) -> str:
        """
        Detect tone from text using keyword matching.
        
        Args:
            text: Text to analyze for tone
            
        Returns:
            Detected tone (e.g., 'professional', 'casual', 'technical')
        """
        text_lower = text.lower()
        tone_scores = {}
        
        # Score each tone based on indicator presence
        for tone, indicators in self.tone_indicators.items():
            score = sum(1 for indicator in indicators if indicator in text_lower)
            if score > 0:
                tone_scores[tone] = score
        
        # Return tone with highest score
        if tone_scores:
            return max(tone_scores.items(), key=lambda x: x[1])[0]
        
        # Default tone
        return "informative"
    
    def extract_keywords_and_tone(self, prompt: str) -> Tuple[List[str], str]:
        """
        Extract both keywords and tone from a prompt.
        
        Args:
            prompt: User's content generation prompt
            
        Returns:
            Tuple of (keywords, tone)
        """
        # Extract keywords
        keywords = self._extract_common_words(prompt, [])
        
        # Detect tone
        tone = self._detect_tone(prompt)
        
        return keywords[:5], tone
