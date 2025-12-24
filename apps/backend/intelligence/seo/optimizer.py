"""Complete SEO Optimizer - Main Module

Integrates all SEO optimization components:
- AI-powered content optimization
- Keyword analysis
- Readability scoring
- Hashtag optimization
- Metadata generation
- Platform-specific rules
- Improvement suggestions
"""

from typing import Dict, List, Optional
import json
import re
import asyncio
from langchain_google_genai import ChatGoogleGenerativeAI

from .config import SEOConfig, DEFAULT_CONFIG
from .keyword_analyzer import KeywordAnalyzer
from .readability_analyzer import ReadabilityAnalyzer
from .hashtag_optimizer import HashtagOptimizer
from .metadata_generator import MetadataGenerator
from .platform_rules import PlatformRules
from .suggestions import SuggestionGenerator


class SEOOptimizer:
    """Complete SEO optimization system with all features.
    
    Provides comprehensive SEO optimization including:
    - AI-powered content enhancement
    - Advanced keyword analysis
    - Readability optimization
    - Platform-specific formatting
    - Metadata generation
    - Actionable suggestions
    """
    
    def __init__(self, config: SEOConfig = None):
        """Initialize SEO optimizer with all components.
        
        Args:
            config: SEO configuration (uses defaults if None)
        """
        self.config = config or DEFAULT_CONFIG
        
        # Initialize AI model
        self.model = ChatGoogleGenerativeAI(
            model=self.config.model_name,
            temperature=self.config.temperature,
            max_output_tokens=self.config.max_tokens
        )
        
        # Initialize analyzers
        self.keyword_analyzer = KeywordAnalyzer(use_ai_for_lsi=self.config.enable_lsi_keywords)
        self.readability_analyzer = ReadabilityAnalyzer()
        self.hashtag_optimizer = HashtagOptimizer(enable_trending=self.config.enable_trending_hashtags)
        self.metadata_generator = MetadataGenerator(model_name=self.config.model_name)
        self.suggestion_generator = SuggestionGenerator()
    
    async def optimize(
        self,
        content: str,
        keywords: List[str],
        platform: str = "general",
        tone: Optional[str] = None,
        title: Optional[str] = None,
        context: Optional[str] = None,
        generate_metadata: bool = False,
        max_retries: int = None
    ) -> Dict:
        """Comprehensive SEO optimization.
        
        Args:
            content: Original content to optimize
            keywords: Target keywords
            platform: Target platform
            tone: Optional tone guidance
            title: Optional content title
            generate_metadata: Whether to generate metadata
            max_retries: Max retry attempts (overrides config)
        
        Returns:
            Complete optimization results dictionary
        """
        max_retries = max_retries or self.config.max_retries
        
        # Attempt optimization with retries
        for attempt in range(max_retries):
            try:
                result = await self._optimize_with_ai(content, keywords, platform, tone, context)
                break
            except Exception as e:
                if attempt == max_retries - 1:
                    # Final attempt failed, use fallback
                    if self.config.enable_fallback:
                        result = self._fallback_optimization(content, keywords, platform)
                        result["fallback_used"] = True
                    else:
                        raise
                else:
                    # Wait before retry with exponential backoff
                    await asyncio.sleep(self.config.retry_delay * (2 ** attempt))
        
        # Perform analyses
        if self.config.enable_keyword_analysis and keywords:
            keyword_analysis = self.keyword_analyzer.analyze(
                result.get("optimized_content", ""),
                keywords,
                include_lsi=self.config.enable_lsi_keywords
            )
            result["keyword_analysis"] = keyword_analysis
            
            # Add LSI keywords if generated
            if "lsi_keywords" in keyword_analysis:
                result["lsi_keywords"] = keyword_analysis["lsi_keywords"]
        
        # Readability analysis
        if self.config.enable_readability:
            readability = self.readability_analyzer.analyze(
                result.get("optimized_content", "")
            )
            result["readability"] = readability
        
        # Hashtag optimization
        if self.config.enable_hashtag_optimization:
            base_hashtags = result.get("hashtags", [])
            hashtag_opt = await self.hashtag_optimizer.optimize(
                result.get("optimized_content", ""),
                base_hashtags,
                platform
            )
            result["hashtags"] = hashtag_opt["hashtags"]
            result["hashtag_analysis"] = hashtag_opt
        
        # Platform compliance
        compliance = self._validate_platform_compliance(result, platform)
        result["platform_compliance"] = compliance
        
        # Calculate SEO score
        seo_score = self._calculate_seo_score(result, keywords, platform)
        result["seo_score"] = seo_score
        
        # Generate improvement suggestions
        suggestions = self.suggestion_generator.generate(
            seo_score,
            result.get("keyword_analysis"),
            result.get("readability"),
            compliance,
            platform
        )
        result["suggestions"] = suggestions
        result["categorized_suggestions"] = self.suggestion_generator.categorize_suggestions(suggestions)
        
        # Generate metadata if requested
        if generate_metadata and title:
            metadata = await self.metadata_generator.generate(
                content,
                title,
                keywords,
                platform
            )
            result["metadata"] = metadata
        
        return result
    
    async def _optimize_with_ai(
        self,
        content: str,
        keywords: List[str],
        platform: str,
        tone: Optional[str],
        context: Optional[str] = None
    ) -> Dict:
        """AI-powered content optimization."""
        prompt = self._build_optimization_prompt(content, keywords, platform, tone, context)
        
        response = await self.model.ainvoke(prompt)
        result = self._parse_response(response.content)
        
        return result
    
    def _build_optimization_prompt(
        self,
        content: str,
        keywords: List[str],
        platform: str,
        tone: Optional[str],
        context: Optional[str] = None
    ) -> str:
        """Build comprehensive optimization prompt."""
        platform_config = PlatformRules.get_config(platform)
        
        tone_guidance = f"\\nDesired Tone: {tone}" if tone else ""
        context_guidance = f"\\n\\nContext/Instructions:\\n{context}" if context else ""
        
        platform_guidance = f"""
PLATFORM: {platform_config.name}
Platform Requirements:
- Max length: {platform_config.max_length} chars
- Optimal length: {platform_config.optimal_length} chars
- Hashtags: {platform_config.optimal_hashtags} ({platform_config.hashtag_placement})
- CTA style: {platform_config.cta_style}

Formatting Guidelines:
{chr(10).join(f'- {rule}' for rule in platform_config.formatting_rules)}
"""
        
        prompt = f"""You are an expert SEO specialist. Optimize this content for {platform_config.name}.

Original Content:
{content}

Keywords: {', '.join(keywords)}{tone_guidance}{context_guidance}{platform_guidance}

Tasks:
1. Optimize content (stay within {platform_config.optimal_length} chars)
2. Integrate keywords naturally
3. Create compelling meta description (150-160 chars)
4. Suggest {platform_config.optimal_hashtags} relevant hashtags
5. Generate 3 title variations (max {platform_config.title_max_length} chars each)
6. Add {platform_config.cta_style} style CTA

Return valid JSON:
{{
    "optimized_content": "Your optimized content",
    "meta_description": "150-160 char description",
    "hashtags": ["#Tag1", "#Tag2", ...],
    "title_options": ["Title 1", "Title 2", "Title 3"],
    "call_to_action": "Your CTA"
}}

Return ONLY JSON, no other text."""
        
        return prompt
    
    def _parse_response(self, response_text: str) -> Dict:
        """Parse AI response with error handling."""
        cleaned = response_text.strip()
        
        # Remove markdown code blocks
        if "```json" in cleaned:
            cleaned = cleaned.split("```json")[1].split("```")[0].strip()
        elif "```" in cleaned:
            parts = cleaned.split("```")
            for part in parts:
                if "{" in part and "}" in part:
                    cleaned = part.strip()
                    break
        
        try:
            result = json.loads(cleaned)
            
            # Validate required fields
            required = ["optimized_content", "meta_description", "hashtags", "title_options", "call_to_action"]
            for field in required:
                if field not in result:
                    result[field] = self._get_default_value(field)
            
            return result
        except json.JSONDecodeError:
            return self._extract_fields_manually(response_text)
    
    def _fallback_optimization(self, content: str, keywords: List[str], platform: str) -> Dict:
        """Rule-based fallback optimization when AI fails."""
        # Basic keyword insertion
        optimized = content
        for keyword in keywords[:2]:
            if keyword.lower() not in content.lower():
                optimized = f"{keyword}: {optimized}"
        
        # Truncate to platform limits
        config = PlatformRules.get_config(platform)
        if len(optimized) > config.optimal_length:
            optimized = optimized[:config.optimal_length - 3] + "..."
        
        # Create meta description
        meta = content[:157] + "..." if len(content) > 160 else content
        
        # Create hashtags
        hashtags = [f"#{kw.replace(' ', '')}" for kw in keywords[:config.optimal_hashtags]]
        
        # Create titles
        titles = [
            content[:60],
            f"{keywords[0]}: {content[:50]}" if keywords else content[:60],
            content[:55] + "..."
        ]
        
        return {
            "optimized_content": optimized,
            "meta_description": meta,
            "hashtags": hashtags,
            "title_options": titles,
            "call_to_action": "Learn more!",
            "fallback": True
        }
    
    def _validate_platform_compliance(self, result: Dict, platform: str) -> Dict:
        """Validate platform compliance."""
        content = result.get("optimized_content", "")
        hashtags = result.get("hashtags", [])
        
        length_validation = PlatformRules.validate_content_length(content, platform)
        hashtag_validation = PlatformRules.validate_hashtag_count(hashtags, platform)
        
        platform_config = PlatformRules.get_config(platform)
        
        title_validation = []
        for title in result.get("title_options", []):
            if len(title) > platform_config.title_max_length:
                title_validation.append({
                    "valid": False,
                    "title": title[:50] + "...",
                    "length": len(title),
                    "max_length": platform_config.title_max_length
                })
        
        return {
            "content_length": length_validation,
            "hashtags": hashtag_validation,
            "titles": title_validation if title_validation else [{"valid": True}],
            "overall_compliant": length_validation["valid"] and hashtag_validation["valid"] and not title_validation
        }
    
    def _calculate_seo_score(self, optimized: Dict, keywords: List[str], platform: str) -> float:
        """Calculate comprehensive SEO score (0-100) with 6 metrics."""
        score = 0.0
        content = optimized.get("optimized_content", "").lower()
        
        # 1. Keywords (30%)
        if keywords:
            keyword_count = sum(1 for kw in keywords if kw.lower() in content)
            score += (keyword_count / len(keywords)) * self.config.keyword_weight
        
        # 2. Meta description (15%)
        meta = optimized.get("meta_description", "")
        meta_len = len(meta)
        if 150 <= meta_len <= 160:
            score += self.config.meta_weight
        elif 140 <= meta_len <= 170:
            score += self.config.meta_weight * 0.8
        elif meta_len > 0:
            score += self.config.meta_weight * 0.5
        
        # 3. Hashtags (15%)
        hashtags = optimized.get("hashtags", [])
        hashtag_validation = PlatformRules.validate_hashtag_count(hashtags, platform)
        if hashtag_validation["valid"]:
            if hashtag_validation["count"] == hashtag_validation["optimal_count"]:
                score += self.config.hashtag_weight
            else:
                score += self.config.hashtag_weight * 0.8
        elif len(hashtags) > 0:
            score += self.config.hashtag_weight * 0.5
        
        # 4. Titles (10%)
        titles = optimized.get("title_options", [])
        if len(titles) >= 3:
            score += self.config.title_weight
        elif len(titles) >= 2:
            score += self.config.title_weight * 0.7
        
        # 5. CTA (10%)
        if optimized.get("call_to_action", "").strip():
            score += self.config.cta_weight
        
        # 6. Readability (20%)
        if "readability" in optimized and "readability_score" in optimized["readability"]:
            readability_score = optimized["readability"]["readability_score"]
            score += (readability_score / 100) * self.config.readability_weight
        
        return min(100.0, round(score, 2))
    
    def _get_default_value(self, field: str):
        """Get default value for missing field."""
        defaults = {
            "optimized_content": "",
            "meta_description": "",
            "hashtags": [],
            "title_options": [],
            "call_to_action": ""
        }
        return defaults.get(field, "")
    
    def _extract_fields_manually(self, text: str) -> Dict:
        """Extract fields from malformed response."""
        return {
            "optimized_content": text[:500],
            "meta_description": text[:160],
            "hashtags": re.findall(r'#\w+', text)[:5],
            "title_options": [text[:60]],
            "call_to_action": ""
        }


# Convenience function
async def optimize_content(
    content: str,
    keywords: List[str],
    platform: str = "general",
    context: Optional[str] = None,
    config: SEOConfig = None
) -> Dict:
    """Quick content optimization.
    
    Args:
        content: Content to optimize
        keywords: Target keywords
        platform: Target platform
        config: Optional configuration
    
    Returns:
        Optimization results
    """
    optimizer = SEOOptimizer(config)
    return await optimizer.optimize(content, keywords, platform, context=context)
