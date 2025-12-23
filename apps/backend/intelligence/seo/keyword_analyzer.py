"""Keyword analysis and optimization for SEO content.

This module provides advanced keyword analysis including:
- Keyword density calculation
- Keyword stuffing detection
- LSI (Latent Semantic Indexing) keyword suggestions
- Natural placement validation
- Keyword distribution analysis
"""

from typing import Dict, List, Tuple, Optional
import re
from collections import Counter
from langchain_google_genai import ChatGoogleGenerativeAI


class KeywordAnalyzer:
    """Advanced keyword analysis for SEO optimization.
    
    Analyzes content for keyword usage patterns, density, and natural integration.
    Provides suggestions for improvement and detects potential issues.
    """
    
    # Optimal keyword density thresholds
    MIN_KEYWORD_DENSITY = 0.5  # Minimum % for keyword presence
    OPTIMAL_KEYWORD_DENSITY_MIN = 1.0  # Optimal minimum %
    OPTIMAL_KEYWORD_DENSITY_MAX = 2.5  # Optimal maximum %
    MAX_KEYWORD_DENSITY = 4.0  # Maximum before considered stuffing
    
    def __init__(self, use_ai_for_lsi: bool = True):
        """Initialize the keyword analyzer.
        
        Args:
            use_ai_for_lsi: Whether to use AI for LSI keyword suggestions
        """
        self.use_ai_for_lsi = use_ai_for_lsi
        if use_ai_for_lsi:
            self.model = ChatGoogleGenerativeAI(
                model="gemini-1.5-pro",
                temperature=0.3  # Lower temperature for more focused suggestions
            )
    
    def analyze(
        self,
        content: str,
        keywords: List[str],
        include_lsi: bool = False
    ) -> Dict:
        """Comprehensive keyword analysis of content.
        
        Args:
            content: Content to analyze
            keywords: Target keywords to check
            include_lsi: Whether to generate LSI keyword suggestions
        
        Returns:
            Dictionary with analysis results including:
                - density: Keyword density metrics
                - stuffing_detected: Whether keyword stuffing is detected
                - placement: How keywords are distributed
                - suggestions: Improvement recommendations
                - lsi_keywords: Related keyword suggestions (if include_lsi=True)
        """
        if not content or not keywords:
            return self._empty_analysis()
        
        # Calculate keyword density
        density_results = self.calculate_density(content, keywords)
        
        # Check for keyword stuffing
        stuffing_check = self.detect_stuffing(content, keywords)
        
        # Analyze placement
        placement_analysis = self.analyze_placement(content, keywords)
        
        # Generate suggestions
        suggestions = self._generate_suggestions(
            density_results,
            stuffing_check,
            placement_analysis
        )
        
        # Compile results
        analysis = {
            "density": density_results,
            "stuffing_detected": stuffing_check["is_stuffing"],
            "stuffing_details": stuffing_check,
            "placement": placement_analysis,
            "suggestions": suggestions,
            "overall_score": self._calculate_keyword_score(
                density_results,
                stuffing_check,
                placement_analysis
            )
        }
        
        # Add LSI suggestions if requested
        if include_lsi and self.use_ai_for_lsi:
            try:
                lsi_keywords = self.suggest_lsi_keywords(content, keywords)
                analysis["lsi_keywords"] = lsi_keywords
            except:
                analysis["lsi_keywords"] = []
        
        return analysis
    
    def calculate_density(self, content: str, keywords: List[str]) -> Dict:
        """Calculate keyword density for each target keyword.
        
        Args:
            content: Content to analyze
            keywords: List of target keywords
        
        Returns:
            Dictionary with density metrics for each keyword
        """
        # Clean and normalize content
        content_lower = content.lower()
        words = re.findall(r'\b\w+\b', content_lower)
        total_words = len(words)
        
        if total_words == 0:
            return {"total_words": 0, "keywords": {}, "average_density": 0.0}
        
        density_results = {}
        
        for keyword in keywords:
            keyword_lower = keyword.lower()
            
            # Count exact phrase occurrences
            phrase_count = content_lower.count(keyword_lower)
            
            # Count individual word occurrences
            keyword_words = re.findall(r'\b\w+\b', keyword_lower)
            word_counts = sum(words.count(word) for word in keyword_words)
            
            # Calculate density
            phrase_density = (phrase_count / total_words) * 100
            word_density = (word_counts / total_words) * 100
            
            # Determine status
            if phrase_density >= self.OPTIMAL_KEYWORD_DENSITY_MIN and \
               phrase_density <= self.OPTIMAL_KEYWORD_DENSITY_MAX:
                status = "optimal"
            elif phrase_density >= self.MIN_KEYWORD_DENSITY:
                if phrase_density > self.MAX_KEYWORD_DENSITY:
                    status = "too_high"
                else:
                    status = "acceptable"
            else:
                status = "too_low"
            
            density_results[keyword] = {
                "phrase_count": phrase_count,
                "word_count": word_counts,
                "phrase_density": round(phrase_density, 2),
                "word_density": round(word_density, 2),
                "status": status
            }
        
        # Calculate average density
        if density_results:
            avg_density = sum(
                d["phrase_density"] for d in density_results.values()
            ) / len(density_results)
        else:
            avg_density = 0.0
        
        return {
            "total_words": total_words,
            "keywords": density_results,
            "average_density": round(avg_density, 2)
        }
    
    def detect_stuffing(self, content: str, keywords: List[str]) -> Dict:
        """Detect keyword stuffing patterns.
        
        Args:
            content: Content to analyze
            keywords: List of target keywords
        
        Returns:
            Dictionary with stuffing detection results
        """
        content_lower = content.lower()
        sentences = re.split(r'[.!?]+', content)
        
        stuffing_indicators = {
            "is_stuffing": False,
            "severity": "none",  # none, low, medium, high
            "issues": [],
            "problematic_keywords": []
        }
        
        # Check 1: Overall density too high
        density = self.calculate_density(content, keywords)
        high_density_keywords = [
            kw for kw, data in density["keywords"].items()
            if data["phrase_density"] > self.MAX_KEYWORD_DENSITY
        ]
        
        if high_density_keywords:
            stuffing_indicators["issues"].append(
                f"High keyword density detected: {', '.join(high_density_keywords)}"
            )
            stuffing_indicators["problematic_keywords"].extend(high_density_keywords)
        
        # Check 2: Unnatural repetition in sentences
        for keyword in keywords:
            keyword_lower = keyword.lower()
            for sentence in sentences:
                sentence_lower = sentence.lower()
                count = sentence_lower.count(keyword_lower)
                if count > 2:  # Keyword appears more than twice in one sentence
                    stuffing_indicators["issues"].append(
                        f"Keyword '{keyword}' appears {count} times in one sentence"
                    )
                    if keyword not in stuffing_indicators["problematic_keywords"]:
                        stuffing_indicators["problematic_keywords"].append(keyword)
        
        # Check 3: Keyword proximity (keywords too close together)
        words = re.findall(r'\b\w+\b', content_lower)
        for keyword in keywords:
            keyword_words = keyword.lower().split()
            if len(keyword_words) == 1:
                positions = [i for i, word in enumerate(words) if word == keyword_words[0]]
                # Check if keyword appears within 10 words of itself multiple times
                for i in range(len(positions) - 1):
                    if positions[i + 1] - positions[i] < 10:
                        stuffing_indicators["issues"].append(
                            f"Keyword '{keyword}' appears too frequently in close proximity"
                        )
                        if keyword not in stuffing_indicators["problematic_keywords"]:
                            stuffing_indicators["problematic_keywords"].append(keyword)
                        break
        
        # Determine severity
        issue_count = len(stuffing_indicators["issues"])
        if issue_count == 0:
            stuffing_indicators["severity"] = "none"
        elif issue_count == 1:
            stuffing_indicators["severity"] = "low"
        elif issue_count <= 3:
            stuffing_indicators["severity"] = "medium"
        else:
            stuffing_indicators["severity"] = "high"
        
        stuffing_indicators["is_stuffing"] = issue_count > 0
        
        return stuffing_indicators
    
    def analyze_placement(self, content: str, keywords: List[str]) -> Dict:
        """Analyze how keywords are distributed throughout content.
        
        Args:
            content: Content to analyze
            keywords: List of target keywords
        
        Returns:
            Dictionary with placement analysis
        """
        content_lower = content.lower()
        content_length = len(content)
        
        # Divide content into sections
        section_size = content_length // 3 if content_length > 100 else content_length
        beginning = content_lower[:section_size]
        middle = content_lower[section_size:section_size * 2] if content_length > 100 else ""
        end = content_lower[section_size * 2:] if content_length > 100 else ""
        
        placement_results = {}
        
        for keyword in keywords:
            keyword_lower = keyword.lower()
            
            in_beginning = keyword_lower in beginning
            in_middle = keyword_lower in middle if middle else False
            in_end = keyword_lower in end if end else False
            
            # Count occurrences in each section
            beginning_count = beginning.count(keyword_lower)
            middle_count = middle.count(keyword_lower) if middle else 0
            end_count = end.count(keyword_lower) if end else 0
            
            # Check first 100 characters (important for SEO)
            in_first_100 = keyword_lower in content_lower[:100]
            
            # Determine distribution quality
            sections_present = sum([in_beginning, in_middle, in_end])
            if sections_present == 3:
                distribution = "excellent"
            elif sections_present == 2:
                distribution = "good"
            elif sections_present == 1:
                distribution = "poor"
            else:
                distribution = "missing"
            
            placement_results[keyword] = {
                "in_beginning": in_beginning,
                "in_middle": in_middle,
                "in_end": in_end,
                "in_first_100_chars": in_first_100,
                "beginning_count": beginning_count,
                "middle_count": middle_count,
                "end_count": end_count,
                "distribution": distribution
            }
        
        return placement_results
    
    async def suggest_lsi_keywords(
        self,
        content: str,
        keywords: List[str],
        max_suggestions: int = 10
    ) -> List[str]:
        """Suggest LSI (Latent Semantic Indexing) keywords using AI.
        
        Args:
            content: Content to analyze
            keywords: Primary keywords
            max_suggestions: Maximum number of suggestions to return
        
        Returns:
            List of related keyword suggestions
        """
        if not self.use_ai_for_lsi:
            return []
        
        prompt = f"""Analyze this content and suggest related keywords (LSI keywords) that would naturally fit and improve SEO.

Content:
{content[:1000]}  

Primary Keywords: {', '.join(keywords)}

Generate {max_suggestions} semantically related keywords or phrases that:
1. Are contextually relevant to the content
2. Would naturally fit in the topic
3. Help search engines understand the content better
4. Are commonly searched alongside the primary keywords

Return ONLY a comma-separated list of keywords, no explanations or numbering.
Example format: keyword1, keyword2, keyword3"""
        
        try:
            response = await self.model.ainvoke(prompt)
            suggestions_text = response.content.strip()
            
            # Parse the response
            lsi_keywords = [
                kw.strip() 
                for kw in suggestions_text.split(',')
                if kw.strip() and len(kw.strip()) > 2
            ]
            
            return lsi_keywords[:max_suggestions]
            
        except Exception as e:
            # Fallback to simple related terms if AI fails
            return []
    
    def _generate_suggestions(
        self,
        density_results: Dict,
        stuffing_check: Dict,
        placement_analysis: Dict
    ) -> List[str]:
        """Generate improvement suggestions based on analysis.
        
        Args:
            density_results: Keyword density analysis
            stuffing_check: Stuffing detection results
            placement_analysis: Placement analysis results
        
        Returns:
            List of actionable suggestions
        """
        suggestions = []
        
        # Density suggestions
        for keyword, data in density_results.get("keywords", {}).items():
            if data["status"] == "too_low":
                suggestions.append(
                    f"Increase usage of '{keyword}' (current: {data['phrase_density']}%, "
                    f"optimal: {self.OPTIMAL_KEYWORD_DENSITY_MIN}-{self.OPTIMAL_KEYWORD_DENSITY_MAX}%)"
                )
            elif data["status"] == "too_high":
                suggestions.append(
                    f"Reduce usage of '{keyword}' to avoid keyword stuffing "
                    f"(current: {data['phrase_density']}%, max: {self.MAX_KEYWORD_DENSITY}%)"
                )
        
        # Stuffing suggestions
        if stuffing_check["is_stuffing"]:
            if stuffing_check["severity"] in ["medium", "high"]:
                suggestions.append(
                    "⚠️ Keyword stuffing detected. Make keyword usage more natural and varied"
                )
            for issue in stuffing_check["issues"][:3]:  # Limit to top 3 issues
                suggestions.append(f"• {issue}")
        
        # Placement suggestions
        for keyword, data in placement_analysis.items():
            if not data["in_first_100_chars"]:
                suggestions.append(
                    f"Consider placing '{keyword}' in the first 100 characters for better SEO"
                )
            if data["distribution"] == "poor":
                suggestions.append(
                    f"Improve distribution of '{keyword}' throughout the content"
                )
            elif data["distribution"] == "missing":
                suggestions.append(
                    f"⚠️ '{keyword}' is not present in the content"
                )
        
        return suggestions
    
    def _calculate_keyword_score(
        self,
        density_results: Dict,
        stuffing_check: Dict,
        placement_analysis: Dict
    ) -> float:
        """Calculate overall keyword optimization score (0-100).
        
        Args:
            density_results: Keyword density analysis
            stuffing_check: Stuffing detection results
            placement_analysis: Placement analysis results
        
        Returns:
            Score from 0-100
        """
        score = 0.0
        
        # Density score (40 points)
        if density_results.get("keywords"):
            optimal_count = sum(
                1 for data in density_results["keywords"].values()
                if data["status"] == "optimal"
            )
            acceptable_count = sum(
                1 for data in density_results["keywords"].values()
                if data["status"] in ["optimal", "acceptable"]
            )
            total_keywords = len(density_results["keywords"])
            
            density_score = (optimal_count / total_keywords) * 40
            if density_score < 20:
                density_score = (acceptable_count / total_keywords) * 30
            
            score += density_score
        
        # Stuffing penalty (up to -30 points)
        if stuffing_check["is_stuffing"]:
            severity_penalties = {
                "low": 10,
                "medium": 20,
                "high": 30
            }
            score -= severity_penalties.get(stuffing_check["severity"], 0)
        else:
            score += 20  # Bonus for no stuffing
        
        # Placement score (40 points)
        if placement_analysis:
            excellent_count = sum(
                1 for data in placement_analysis.values()
                if data["distribution"] == "excellent"
            )
            good_count = sum(
                1 for data in placement_analysis.values()
                if data["distribution"] in ["excellent", "good"]
            )
            total_keywords = len(placement_analysis)
            
            placement_score = (excellent_count / total_keywords) * 40
            if placement_score < 20:
                placement_score = (good_count / total_keywords) * 30
            
            score += placement_score
        
        return min(100.0, max(0.0, round(score, 2)))
    
    def _empty_analysis(self) -> Dict:
        """Return empty analysis structure."""
        return {
            "density": {
                "total_words": 0,
                "keywords": {},
                "average_density": 0.0
            },
            "stuffing_detected": False,
            "stuffing_details": {
                "is_stuffing": False,
                "severity": "none",
                "issues": [],
                "problematic_keywords": []
            },
            "placement": {},
            "suggestions": ["No content or keywords provided"],
            "overall_score": 0.0
        }
