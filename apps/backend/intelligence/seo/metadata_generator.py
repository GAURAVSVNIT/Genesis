"""Metadata generation for SEO optimization.

Generates:
- Multiple meta description variations
- Open Graph (OG) tags
- Twitter Card tags
- Schema.org markup suggestions
- Image alt text
"""

from typing import Dict, List
from langchain_google_genai import ChatGoogleGenerativeAI
import json


class MetadataGenerator:
    """Generates SEO metadata for content."""
    
    def __init__(self, model_name: str = "gemini-1.5-pro"):
        """Initialize metadata generator.
        
        Args:
            model_name: AI model for generation
        """
        self.model = ChatGoogleGenerativeAI(
            model=model_name,
            temperature=0.6,
            max_output_tokens=2048
        )
    
    async def generate(
        self,
        content: str,
        title: str,
        keywords: List[str],
        platform: str = "general",
        image_url: str = None
    ) -> Dict:
        """Generate comprehensive metadata.
        
        Args:
            content: Main content
            title: Content title
            keywords: Target keywords
            platform: Target platform
            image_url: Optional image URL
        
        Returns:
            Dictionary with all metadata
        """
        # Generate multiple meta descriptions
        meta_descriptions = await self._generate_meta_descriptions(content, keywords, count=3)
        
        # Generate OG tags
        og_tags = self._generate_og_tags(title, meta_descriptions[0], image_url)
        
        # Generate Twitter Card tags
        twitter_tags = self._generate_twitter_tags(title, meta_descriptions[0], image_url)
        
        # Generate schema markup suggestions
        schema_markup = self._generate_schema(content, title, platform)
        
        # Generate image alt text if image provided
        image_alt = await self._generate_image_alt(content, title) if image_url else None
        
        return {
            "meta_descriptions": meta_descriptions,
            "og_tags": og_tags,
            "twitter_tags": twitter_tags,
            "schema_markup": schema_markup,
            "image_alt_text": image_alt,
            "canonical_url": None  # To be filled by user
        }
    
    async def _generate_meta_descriptions(
        self,
        content: str,
        keywords: List[str],
        count: int = 3
    ) -> List[str]:
        """Generate multiple meta description variations."""
        prompt = f"""Generate {count} unique meta descriptions for this content.

Content:
{content[:500]}

Keywords: {', '.join(keywords)}

Requirements:
- Each 150-160 characters
- Include primary keywords naturally
- Compelling and click-worthy
- Different angles/approaches

Return as JSON array of strings.
Example: ["Description 1", "Description 2", "Description 3"]"""
        
        try:
            response = await self.model.ainvoke(prompt)
            text = response.content.strip()
            
            # Parse JSON
            if "```json" in text:
                text = text.split("```json")[1].split("```")[0]
            elif "```" in text:
                text = text.split("```")[1].split("```")[0]
            
            descriptions = json.loads(text)
            
            # Validate and truncate to 160 chars
            return [desc[:160] for desc in descriptions if isinstance(desc, str)][:count]
            
        except:
            # Fallback: create simple descriptions
            base_desc = content[:150].strip() + "..."
            return [base_desc] * count
    
    def _generate_og_tags(
        self,
        title: str,
        description: str,
        image_url: str = None
    ) -> Dict:
        """Generate Open Graph tags."""
        og_tags = {
            "og:title": title[:60],
            "og:description": description[:200],
            "og:type": "article",
            "og:locale": "en_US"
        }
        
        if image_url:
            og_tags["og:image"] = image_url
            og_tags["og:image:alt"] = title
        
        return og_tags
    
    def _generate_twitter_tags(
        self,
        title: str,
        description: str,
        image_url: str = None
    ) -> Dict:
        """Generate Twitter Card tags."""
        twitter_tags = {
            "twitter:card": "summary_large_image" if image_url else "summary",
            "twitter:title": title[:70],
            "twitter:description": description[:200]
        }
        
        if image_url:
            twitter_tags["twitter:image"] = image_url
            twitter_tags["twitter:image:alt"] = title
        
        return twitter_tags
    
    def _generate_schema(
        self,
        content: str,
        title: str,
        content_type: str
    ) -> Dict:
        """Generate Schema.org markup suggestion."""
        
        # Determine schema type
        if content_type == "blog":
            schema_type = "Article"
        elif "product" in content.lower():
            schema_type = "Product"
        elif "event" in content.lower():
            schema_type = "Event"
        else:
            schema_type = "WebPage"
        
        schema = {
            "@context": "https://schema.org",
            "@type": schema_type,
            "headline": title,
            "description": content[:200],
        }
        
        if schema_type == "Article":
            schema.update({
                "author": {
                    "@type": "Person",
                    "name": "[Author Name]"
                },
                "datePublished": "[Publication Date]",
                "dateModified": "[Modified Date]"
            })
        
        return schema
    
    async def _generate_image_alt(self, content: str, title: str) -> str:
        """Generate image alt text."""
        prompt = f"""Generate concise, descriptive alt text for an image related to this content.

Title: {title}
Content: {content[:200]}

Requirements:
- 125 characters max
- Descriptive and specific
- Include key context
- Accessibility-focused

Return only the alt text, no explanations."""
        
        try:
            response = await self.model.ainvoke(prompt)
            alt_text = response.content.strip()
            return alt_text[:125]
        except:
            return title[:125]
    
    def generate_meta_tags_html(self, metadata: Dict) -> str:
        """Generate HTML meta tags from metadata dictionary.
        
        Args:
            metadata: Metadata dictionary from generate()
        
        Returns:
            HTML meta tags as string
        """
        html_lines = []
        
        # Basic meta tags
        if metadata.get("meta_descriptions"):
            html_lines.append(f'<meta name="description" content="{metadata["meta_descriptions"][0]}">')
        
        # OG tags
        if og_tags := metadata.get("og_tags"):
            for key, value in og_tags.items():
                html_lines.append(f'<meta property="{key}" content="{value}">')
        
        # Twitter tags
        if twitter_tags := metadata.get("twitter_tags"):
            for key, value in twitter_tags.items():
                html_lines.append(f'<meta name="{key}" content="{value}">')
        
        # Schema markup
        if schema := metadata.get("schema_markup"):
            html_lines.append(f'<script type="application/ld+json">')
            html_lines.append(json.dumps(schema, indent=2))
            html_lines.append('</script>')
        
        return '\n'.join(html_lines)
