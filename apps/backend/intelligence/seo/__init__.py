"""SEO Optimization Package - Complete Suite

A comprehensive SEO optimization system with:
- Content optimization with AI
- Keyword analysis and optimization
- Readability scoring
- Platform-specific rules
- Hashtag optimization
- Metadata generation
- Configuration management
"""

from .optimizer import SEOOptimizer
from .keyword_analyzer import KeywordAnalyzer
from .readability_analyzer import ReadabilityAnalyzer
from .hashtag_optimizer import HashtagOptimizer
from .metadata_generator import MetadataGenerator
from .suggestions import SuggestionGenerator
from .config import SEOConfig
from .platform_rules import PlatformRules, PlatformConfig

__all__ = [
    "SEOOptimizer",
    "KeywordAnalyzer",
    "ReadabilityAnalyzer",
    "HashtagOptimizer",
    "MetadataGenerator",
    "SuggestionGenerator",
    "SEOConfig",
    "PlatformRules",
    "PlatformConfig"
]

__version__ = "2.0.0"
