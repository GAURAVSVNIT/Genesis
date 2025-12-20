"""Platform-specific rules and configurations for SEO optimization.

Defines character limits, hashtag requirements, and formatting guidelines
for each supported social media platform and content type.
"""

from typing import Dict, List
from dataclasses import dataclass


@dataclass
class PlatformConfig:
    """Configuration for platform-specific optimization rules."""
    
    name: str
    max_length: int
    optimal_length: int
    min_hashtags: int
    max_hashtags: int
    optimal_hashtags: int
    hashtag_placement: str  # 'inline', 'end', 'separate'
    cta_style: str
    title_max_length: int
    meta_description_max: int
    allows_links: bool
    formatting_rules: List[str]


class PlatformRules:
    """Platform-specific rules and configurations."""
    
    PLATFORMS = {
        "twitter": PlatformConfig(
            name="Twitter/X",
            max_length=280,
            optimal_length=240,
            min_hashtags=1,
            max_hashtags=2,
            optimal_hashtags=2,
            hashtag_placement="end",
            cta_style="direct_action",
            title_max_length=60,
            meta_description_max=160,
            allows_links=True,
            formatting_rules=[
                "Keep it concise and punchy",
                "Use line breaks for readability",
                "Front-load important information",
                "Use emoji sparingly"
            ]
        ),
        "linkedin": PlatformConfig(
            name="LinkedIn",
            max_length=3000,
            optimal_length=1500,
            min_hashtags=3,
            max_hashtags=5,
            optimal_hashtags=4,
            hashtag_placement="end",
            cta_style="professional_engagement",
            title_max_length=70,
            meta_description_max=160,
            allows_links=True,
            formatting_rules=[
                "Start with a hook or question",
                "Use short paragraphs (2-3 lines)",
                "Include white space for readability",
                "End with a question to drive engagement",
                "Professional tone"
            ]
        ),
        "instagram": PlatformConfig(
            name="Instagram",
            max_length=2200,
            optimal_length=300,
            min_hashtags=10,
            max_hashtags=30,
            optimal_hashtags=15,
            hashtag_placement="separate",
            cta_style="community_building",
            title_max_length=60,
            meta_description_max=150,
            allows_links=False,
            formatting_rules=[
                "Visual storytelling focus",
                "Use line breaks generously",
                "Front-load first 125 characters (before 'more')",
                "Emoji usage encouraged",
                "Tell a story or share value"
            ]
        ),
        "facebook": PlatformConfig(
            name="Facebook",
            max_length=63206,
            optimal_length=80,
            min_hashtags=0,
            max_hashtags=2,
            optimal_hashtags=1,
            hashtag_placement="end",
            cta_style="conversational",
            title_max_length=60,
            meta_description_max=160,
            allows_links=True,
            formatting_rules=[
                "Conversational and personal",
                "Ask questions to drive comments",
                "Use emotion and storytelling",
                "Keep it scannable"
            ]
        ),
        "blog": PlatformConfig(
            name="Blog/Website",
            max_length=50000,
            optimal_length=2000,
            min_hashtags=0,
            max_hashtags=0,
            optimal_hashtags=0,
            hashtag_placement="none",
            cta_style="value_driven",
            title_max_length=60,
            meta_description_max=160,
            allows_links=True,
            formatting_rules=[
                "Use H2 and H3 headings for structure",
                "Short paragraphs (3-4 sentences)",
                "Include internal and external links",
                "Use bullet points and lists",
                "Add relevant images with alt text",
                "Clear introduction and conclusion"
            ]
        ),
        "general": PlatformConfig(
            name="General",
            max_length=10000,
            optimal_length=500,
            min_hashtags=2,
            max_hashtags=5,
            optimal_hashtags=3,
            hashtag_placement="end",
            cta_style="flexible",
            title_max_length=60,
            meta_description_max=160,
            allows_links=True,
            formatting_rules=[
                "Clear and concise",
                "Engaging and readable",
                "Well-structured"
            ]
        )
    }
    
    @classmethod
    def get_config(cls, platform: str) -> PlatformConfig:
        """Get configuration for a specific platform."""
        platform_lower = platform.lower()
        return cls.PLATFORMS.get(platform_lower, cls.PLATFORMS["general"])
    
    @classmethod
    def validate_content_length(cls, content: str, platform: str) -> Dict[str, any]:
        """Validate if content meets platform length requirements."""
        config = cls.get_config(platform)
        length = len(content)
        
        if length > config.max_length:
            return {
                "valid": False,
                "length": length,
                "max_length": config.max_length,
                "optimal_length": config.optimal_length,
                "message": f"Content exceeds {config.name} max length of {config.max_length} characters"
            }
        
        if length > config.optimal_length:
            return {
                "valid": True,
                "length": length,
                "max_length": config.max_length,
                "optimal_length": config.optimal_length,
                "message": f"Content is longer than optimal length ({config.optimal_length}). Consider shortening."
            }
        
        return {
            "valid": True,
            "length": length,
            "max_length": config.max_length,
            "optimal_length": config.optimal_length,
            "message": "Content length is optimal"
        }
    
    @classmethod
    def validate_hashtag_count(cls, hashtags: List[str], platform: str) -> Dict[str, any]:
        """Validate if hashtag count is appropriate for platform."""
        config = cls.get_config(platform)
        count = len(hashtags)
        
        if count < config.min_hashtags:
            return {
                "valid": False,
                "count": count,
                "optimal_count": config.optimal_hashtags,
                "message": f"Too few hashtags for {config.name}. Minimum: {config.min_hashtags}"
            }
        
        if count > config.max_hashtags:
            return {
                "valid": False,
                "count": count,
                "optimal_count": config.optimal_hashtags,
                "message": f"Too many hashtags for {config.name}. Maximum: {config.max_hashtags}"
            }
        
        if count != config.optimal_hashtags:
            return {
                "valid": True,
                "count": count,
                "optimal_count": config.optimal_hashtags,
                "message": f"Hashtag count is acceptable but {config.optimal_hashtags} is optimal"
            }
        
        return {
            "valid": True,
            "count": count,
            "optimal_count": config.optimal_hashtags,
            "message": "Hashtag count is optimal"
        }
