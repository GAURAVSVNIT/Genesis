"""Improvement suggestions generator for SEO optimization.

Generates actionable recommendations based on:
- SEO score analysis
- Platform best practices
- Content quality metrics
- Keyword optimization
- Readability issues
"""

from typing import Dict, List


class SuggestionGenerator:
    """Generates improvement suggestions for SEO optimization."""
    
    def generate(
        self,
        seo_score: float,
        keyword_analysis: Dict,
        readability: Dict,
        platform_compliance: Dict,
        platform: str
    ) -> List[str]:
        """Generate comprehensive improvement suggestions.
        
        Args:
            seo_score: Overall SEO score
            keyword_analysis: Keyword analysis results
            readability: Readability analysis results
            platform_compliance: Platform compliance check
            platform: Target platform
        
        Returns:
            List of actionable suggestions
        """
        suggestions = []
        
        # Overall score suggestions
        suggestions.extend(self._score_suggestions(seo_score))
        
        # Keyword suggestions
        if keyword_analysis:
            suggestions.extend(self._keyword_suggestions(keyword_analysis))
        
        # Readability suggestions
        if readability:
            suggestions.extend(self._readability_suggestions(readability))
        
        # Platform compliance suggestions
        if platform_compliance:
            suggestions.extend(self._compliance_suggestions(platform_compliance, platform))
        
        # Platform-specific tips
        suggestions.extend(self._platform_tips(platform))
        
        # Remove duplicates while preserving order
        seen = set()
        unique_suggestions = []
        for suggestion in suggestions:
            if suggestion not in seen:
                seen.add(suggestion)
                unique_suggestions.append(suggestion)
        
        return unique_suggestions
    
    def _score_suggestions(self, score: float) -> List[str]:
        """Suggestions based on overall SEO score."""
        suggestions = []
        
        if score < 40:
            suggestions.append("🔴 SEO score is low. Focus on keyword integration and content structure")
        elif score < 60:
            suggestions.append("⚠️ SEO score needs improvement. Review keyword density and meta descriptions")
        elif score < 75:
            suggestions.append("✓ SEO score is good. Fine-tune for better results")
        elif score < 90:
            suggestions.append("👍 SEO score is very good. Minor optimizations can push to excellent")
        else:
            suggestions.append("🎉 Excellent SEO score! Content is well-optimized")
        
        return suggestions
    
    def _keyword_suggestions(self, analysis: Dict) -> List[str]:
        """Suggestions from keyword analysis."""
        suggestions = []
        
        if not analysis:
            return suggestions
        
        # Check keyword score
        if analysis.get("overall_score", 0) < 60:
            suggestions.append("📊 Keyword optimization score is low. Review keyword placement and density")
        
        # Stuffing issues
        if analysis.get("stuffing_detected"):
            severity = analysis.get("stuffing_details", {}).get("severity", "low")
            if severity == "high":
                suggestions.append("🔴 Critical: Severe keyword stuffing detected. Make keyword usage more natural")
            elif severity == "medium":
                suggestions.append("⚠️ Warning: Keyword stuffing detected. Reduce keyword repetition")
            else:
                suggestions.append("ℹ️ Mild keyword stuffing detected. Vary your language more")
        
        # Density issues
        density = analysis.get("density", {})
        if density.get("average_density", 0) < 1.0:
            suggestions.append("📈 Keyword density is low. Increase keyword usage naturally")
        elif density.get("average_density", 0) > 3.0:
            suggestions.append("📉 Keyword density is high. Reduce keyword repetition")
        
        # Placement issues
        placement = analysis.get("placement", {})
        for keyword, data in placement.items():
            if not data.get("in_first_100_chars"):
                suggestions.append(f"📍 Place '{keyword}' in the first 100 characters for better SEO")
                break  # Only suggest once
        
        # Add top analysis suggestions
        if analysis_suggestions := analysis.get("suggestions", []):
            suggestions.extend(analysis_suggestions[:2])  # Top 2
        
        return suggestions
    
    def _readability_suggestions(self, readability: Dict) -> List[str]:
        """Suggestions from readability analysis."""
        suggestions = []
        
        if not readability:
            return suggestions
        
        score = readability.get("readability_score", 0)
        
        if score < 40:
            suggestions.append("📖 Content is difficult to read. Simplify language and shorten sentences")
        elif score < 60:
            suggestions.append("📖 Improve readability with shorter sentences and simpler words")
        
        # Add readability recommendations
        if recommendations := readability.get("recommendations", []):
            for rec in recommendations[:2]:  # Top 2
                if "🔴" in rec or "⚠️" in rec:
                    suggestions.append(rec)
        
        # Flesch score specific
        if metrics := readability.get("metrics", {}):
            if flesch := metrics.get("flesch_reading_ease", {}):
                if isinstance(flesch, dict) and flesch.get("score", 100) < 50:
                    suggestions.append(f"📚 Target a broader audience by improving readability to {flesch.get('grade_level', '8th-10th')} grade level")
        
        return suggestions
    
    def _compliance_suggestions(self, compliance: Dict, platform: str) -> List[str]:
        """Suggestions from platform compliance check."""
        suggestions = []
        
        if not compliance:
            return suggestions
        
        # Content length
        if content_check := compliance.get("content_length"):
            if not content_check.get("valid"):
                suggestions.append(f"📏 {content_check.get('message', 'Content length issue')}")
        
        # Hashtags
        if hashtag_check := compliance.get("hashtags"):
            if not hashtag_check.get("valid"):
                suggestions.append(f"#️⃣ {hashtag_check.get('message', 'Hashtag count issue')}")
        
        # Titles
        if titles := compliance.get("titles", []):
            for title_check in titles:
                if not title_check.get("valid"):
                    suggestions.append("📝 Some titles exceed maximum length for platform")
                    break
        
        return suggestions
    
    def _platform_tips(self, platform: str) -> List[str]:
        """Platform-specific optimization tips."""
        tips_by_platform = {
            "twitter": [
                "💡 Use relevant trending hashtags for more visibility",
                "💡 Ask questions to increase engagement",
                "💡 Front-load key information in first 100 characters"
            ],
            "linkedin": [
                "💡 Share professional insights and thought leadership",
                "💡 End with a question to drive comments",
                "💡 Use industry-specific hashtags"
            ],
            "instagram": [
                "💡 Use 10-30 hashtags for maximum reach",
                "💡 Front-load first 125 characters before 'more' button",
                "💡 Place hashtags in first comment for cleaner look"
            ],
            "facebook": [
                "💡 Keep posts short (40-80 chars) for higher engagement",
                "💡 Ask questions to drive comments",
                "💡 Use minimal hashtags (0-2)"
            ],
            "blog": [
                "💡 Use H2 and H3 headings for better structure",
                "💡 Add internal links to related content",
                "💡 Include relevant images with alt text",
                "💡 Aim for 1500-2500 words for SEO"
            ]
        }
        
        tips = tips_by_platform.get(platform, [
            "💡 Focus on valuable, engaging content",
            "💡 Use natural keyword integration",
            "💡 Optimize for your target audience"
        ])
        
        # Return 1-2 random tips
        return tips[:2]
    
    def categorize_suggestions(self, suggestions: List[str]) -> Dict[str, List[str]]:
        """Categorize suggestions by priority.
        
        Returns:
            Dict with 'critical', 'important', 'optional' categories
        """
        critical = []
        important = []
        optional = []
        
        for suggestion in suggestions:
            if "🔴" in suggestion or "Critical" in suggestion:
                critical.append(suggestion)
            elif "⚠️" in suggestion or "Warning" in suggestion:
                important.append(suggestion)
            else:
                optional.append(suggestion)
        
        return {
            "critical": critical,
            "important": important,
            "optional": optional
        }
