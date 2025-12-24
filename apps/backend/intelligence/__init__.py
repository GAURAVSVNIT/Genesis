"""Intelligence layer for AI-powered content analysis."""

from .trend_analyzer import TrendAnalyzer

# SEO Package - Complete Suite
from .seo import (
    SEOOptimizer,
    KeywordAnalyzer,
    ReadabilityAnalyzer,
    HashtagOptimizer,
    MetadataGenerator,
    SEOConfig,
    PlatformRules,
    PlatformConfig
)

# Legacy imports for backward compatibility
from .seo.optimizer import optimize_content

__all__ = [
    # SEO Suite
    "SEOOptimizer",
    "KeywordAnalyzer",
    "ReadabilityAnalyzer",
    "HashtagOptimizer",
    "MetadataGenerator",
    "SEOConfig",
    "PlatformRules",
    "PlatformConfig",
    "optimize_content",
    
    # Other Intelligence
    "TrendAnalyzer"
]
