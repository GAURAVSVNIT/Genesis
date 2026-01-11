"""SEO Configuration System

Centralized configuration for all SEO optimization components.
Supports environment-based settings and customization.
"""

from typing import Dict, Optional
from pydantic import BaseModel, Field
import os


class SEOConfig(BaseModel):
    """Configuration for SEO optimization system."""
    
    # Model Settings
    model_name: str = Field(
        default="gemini-2.5-flash",
        description="AI model for content optimization (gemini-2.5-flash, gpt-4o-mini, etc.)"
    )
    temperature: float = Field(
        default=0.7,
        ge=0.0,
        le=1.0,
        description="Model creativity (0.0-1.0)"
    )
    max_tokens: int = Field(
        default=8192,
        description="Maximum tokens for AI response"
    )
    
    # Scoring Weights (must sum to 100)
    keyword_weight: float = Field(default=30.0, description="Keyword presence weight")
    meta_weight: float = Field(default=15.0, description="Meta description weight")
    hashtag_weight: float = Field(default=15.0, description="Hashtag optimization weight")
    title_weight: float = Field(default=10.0, description="Title quality weight")
    cta_weight: float = Field(default=10.0, description="CTA presence weight")
    readability_weight: float = Field(default=20.0, description="Readability weight")
    
    # Keyword Analysis Settings
    min_keyword_density: float = Field(default=0.5, description="Minimum keyword density %")
    optimal_keyword_density_min: float = Field(default=1.0, description="Optimal min density %")
    optimal_keyword_density_max: float = Field(default=2.5, description="Optimal max density %")
    max_keyword_density: float = Field(default=4.0, description="Maximum before stuffing %")
    
    # Meta Description Settings
    meta_description_min: int = Field(default=150, description="Min meta description chars")
    meta_description_max: int = Field(default=160, description="Max meta description chars")
    meta_description_variations: int = Field(default=3, description="Number of variations to generate")
    
    # Title Settings
    title_min: int = Field(default=50, description="Minimum title length")
    title_max: int = Field(default=60, description="Maximum title length")
    title_variations: int = Field(default=3, description="Number of title variations")
    
    # Hashtag Settings
    enable_trending_hashtags: bool = Field(default=True, description="Fetch trending hashtags")
    trending_cache_ttl: int = Field(default=1800, description="Trending cache TTL in seconds (30 min)")
    max_lsi_keywords: int = Field(default=10, description="Max LSI keyword suggestions")
    
    # Error Handling
    enable_fallback: bool = Field(default=True, description="Enable fallback optimization")
    max_retries: int = Field(default=3, description="Max API retry attempts")
    retry_delay: float = Field(default=1.0, description="Initial retry delay in seconds")
    
    # Performance
    enable_caching: bool = Field(default=True, description="Enable Redis caching")
    cache_ttl: int = Field(default=3600, description="Default cache TTL in seconds")
    
    # Features
    enable_keyword_analysis: bool = Field(default=True, description="Enable keyword analysis")
    enable_readability: bool = Field(default=True, description="Enable readability analysis")
    enable_lsi_keywords: bool = Field(default=False, description="Enable LSI suggestions (requires AI)")
    enable_hashtag_optimization: bool = Field(default=True, description="Enable hashtag optimizer")
    
    class Config:
        """Pydantic config."""
        validate_assignment = True
    
    @classmethod
    def from_env(cls) -> "SEOConfig":
        """Load configuration from environment variables.
        
        Environment variables:
            SEO_MODEL_NAME: AI model name
            SEO_TEMPERATURE: Model temperature
            SEO_ENABLE_LSI: Enable LSI keywords (true/false)
            SEO_MAX_RETRIES: Maximum retry attempts
            SEO_ENABLE_CACHING: Enable caching (true/false)
        """
        config = cls()
        
        # Override from environment
        if model := os.getenv("SEO_MODEL_NAME"):
            config.model_name = model
        
        if temp := os.getenv("SEO_TEMPERATURE"):
            try:
                config.temperature = float(temp)
            except ValueError:
                pass
        
        if lsi := os.getenv("SEO_ENABLE_LSI"):
            config.enable_lsi_keywords = lsi.lower() in ("true", "1", "yes")
        
        if retries := os.getenv("SEO_MAX_RETRIES"):
            try:
                config.max_retries = int(retries)
            except ValueError:
                pass
        
        if caching := os.getenv("SEO_ENABLE_CACHING"):
            config.enable_caching = caching.lower() in ("true", "1", "yes")
        
        return config
    
    def validate_weights(self) -> bool:
        """Validate that all scoring weights sum to 100."""
        total = (
            self.keyword_weight +
            self.meta_weight +
            self.hashtag_weight +
            self.title_weight +
            self.cta_weight +
            self.readability_weight
        )
        return abs(total - 100.0) < 0.01
    
    def to_dict(self) -> Dict:
        """Convert config to dictionary."""
        return self.model_dump()


# Global default configuration
DEFAULT_CONFIG = SEOConfig()
