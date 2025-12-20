"""Readability analysis for SEO content.

This module provides readability scoring using industry-standard metrics:
- Flesch Reading Ease Score
- Flesch-Kincaid Grade Level
- Automated Readability Index (ARI)
- Coleman-Liau Index
- Gunning Fog Index
"""

from typing import Dict
try:
    import textstat
    TEXTSTAT_AVAILABLE = True
except ImportError:
    TEXTSTAT_AVAILABLE = False
    print("Warning: textstat not installed. Readability analysis will be limited.")


class ReadabilityAnalyzer:
    """Analyzes content readability using multiple metrics.
    
    Provides scores and recommendations for improving content readability
    to match target audience reading levels.
    """
    
    # Reading ease score interpretation
    FLESCH_RANGES = [
        (90, 100, "Very Easy", "5th grade", "Very easy to read"),
        (80, 90, "Easy", "6th grade", "Easy to read"),
        (70, 80, "Fairly Easy", "7th grade", "Fairly easy to read"),
        (60, 70, "Standard", "8th-9th grade", "Plain English, easily understood"),
        (50, 60, "Fairly Difficult", "10th-12th grade", "Fairly difficult to read"),
        (30, 50, "Difficult", "College", "Difficult to read"),
        (0, 30, "Very Difficult", "College graduate", "Very difficult to read")
    ]
    
    def __init__(self):
        """Initialize the readability analyzer."""
        self.available = TEXTSTAT_AVAILABLE
    
    def analyze(self, content: str) -> Dict:
        """Comprehensive readability analysis.
        
        Args:
            content: Text content to analyze
        
        Returns:
            Dictionary with readability metrics and recommendations
        """
        if not self.available:
            return self._unavailable_response()
        
        if not content or len(content.strip()) < 10:
            return self._empty_response()
        
        # Calculate various readability metrics
        flesch_score = textstat.flesch_reading_ease(content)
        fk_grade = textstat.flesch_kincaid_grade(content)
        ari = textstat.automated_readability_index(content)
        coleman_liau = textstat.coleman_liau_index(content)
        gunning_fog = textstat.gunning_fog(content)
        
        # Get text statistics
        sentence_count = textstat.sentence_count(content)
        word_count = textstat.lexicon_count(content, removepunct=True)
        syllable_count = textstat.syllable_count(content)
        char_count = textstat.char_count(content, ignore_spaces=True)
        
        # Calculate averages
        avg_sentence_length = word_count / sentence_count if sentence_count > 0 else 0
        avg_syllables_per_word = syllable_count / word_count if word_count > 0 else 0
        avg_word_length = char_count / word_count if word_count > 0 else 0
        
        # Interpret Flesch Reading Ease score
        flesch_interpretation = self._interpret_flesch_score(flesch_score)
        
        # Calculate overall readability score (0-100)
        overall_score = self._calculate_overall_score({
            "flesch": flesch_score,
            "fk_grade": fk_grade,
            "ari": ari,
            "gunning_fog": gunning_fog
        })
        
        # Generate recommendations
        recommendations = self._generate_recommendations({
            "flesch_score": flesch_score,
            "avg_sentence_length": avg_sentence_length,
            "avg_syllables_per_word": avg_syllables_per_word,
            "avg_word_length": avg_word_length
        })
        
        return {
            "readability_score": overall_score,
            "metrics": {
                "flesch_reading_ease": {
                    "score": round(flesch_score, 1),
                    "difficulty": flesch_interpretation["difficulty"],
                    "grade_level": flesch_interpretation["grade_level"],
                    "description": flesch_interpretation["description"]
                },
                "flesch_kincaid_grade": round(fk_grade, 1),
                "automated_readability_index": round(ari, 1),
                "coleman_liau_index": round(coleman_liau, 1),
                "gunning_fog_index": round(gunning_fog, 1)
            },
            "statistics": {
                "sentence_count": sentence_count,
                "word_count": word_count,
                "syllable_count": syllable_count,
                "character_count": char_count,
                "avg_sentence_length": round(avg_sentence_length, 1),
                "avg_syllables_per_word": round(avg_syllables_per_word, 2),
                "avg_word_length": round(avg_word_length, 1)
            },
            "recommendations": recommendations,
            "target_audience": self._suggest_target_audience(flesch_score)
        }
    
    def _interpret_flesch_score(self, score: float) -> Dict:
        """Interpret Flesch Reading Ease score.
        
        Args:
            score: Flesch Reading Ease score (0-100)
        
        Returns:
            Dictionary with interpretation
        """
        for min_score, max_score, difficulty, grade, description in self.FLESCH_RANGES:
            if min_score <= score <= max_score:
                return {
                    "difficulty": difficulty,
                    "grade_level": grade,
                    "description": description
                }
        
        # Fallback for scores outside normal range
        if score > 100:
            return {
                "difficulty": "Very Easy",
                "grade_level": "Below 5th grade",
                "description": "Extremely easy to read"
            }
        else:
            return {
                "difficulty": "Very Difficult",
                "grade_level": "Post-graduate",
                "description": "Extremely difficult to read"
            }
    
    def _calculate_overall_score(self, metrics: Dict) -> float:
        """Calculate overall readability score (0-100).
        
        Higher scores indicate better readability.
        
        Args:
            metrics: Dictionary of readability metrics
        
        Returns:
            Overall score from 0-100
        """
        # Flesch score is already 0-100, higher is better
        flesch_score = max(0, min(100, metrics["flesch"]))
        
        # Convert grade levels to scores (lower grade = higher score)
        # Target: 8th-10th grade (score ~70-80)
        grade_scores = []
        
        for grade_metric in ["fk_grade", "ari", "gunning_fog"]:
            grade = metrics[grade_metric]
            if grade <= 6:
                grade_score = 100  # Very easy
            elif grade <= 8:
                grade_score = 90   # Easy
            elif grade <= 10:
                grade_score = 80   # Ideal
            elif grade <= 12:
                grade_score = 70   # Good
            elif grade <= 14:
                grade_score = 60   # Acceptable
            elif grade <= 16:
                grade_score = 50   # Difficult
            else:
                grade_score = 40   # Very difficult
            
            grade_scores.append(grade_score)
        
        # Weight: Flesch (40%), Average of grade levels (60%)
        overall = (flesch_score * 0.4) + (sum(grade_scores) / len(grade_scores) * 0.6)
        
        return round(overall, 2)
    
    def _generate_recommendations(self, stats: Dict) -> list:
        """Generate recommendations for improving readability.
        
        Args:
            stats: Dictionary of text statistics
        
        Returns:
            List of recommendation strings
        """
        recommendations = []
        
        flesch = stats["flesch_score"]
        avg_sentence_length = stats["avg_sentence_length"]
        avg_syllables = stats["avg_syllables_per_word"]
        avg_word_length = stats["avg_word_length"]
        
        # Sentence length recommendations
        if avg_sentence_length > 25:
            recommendations.append(
                f"🔴 Sentences are too long (avg: {avg_sentence_length:.1f} words). "
                "Break them into shorter sentences (15-20 words ideal)."
            )
        elif avg_sentence_length > 20:
            recommendations.append(
                f"⚠️ Sentences are slightly long (avg: {avg_sentence_length:.1f} words). "
                "Consider shortening some for better flow."
            )
        elif avg_sentence_length < 10:
            recommendations.append(
                f"ℹ️ Sentences are very short (avg: {avg_sentence_length:.1f} words). "
                "Consider varying sentence length for better rhythm."
            )
        
        # Word complexity recommendations
        if avg_syllables > 1.8:
            recommendations.append(
                "🔴 Words are too complex. Use simpler alternatives where possible."
            )
        elif avg_syllables > 1.6:
            recommendations.append(
                "⚠️ Some words are complex. Consider simplifying for broader audience."
            )
        
        if avg_word_length > 5.5:
            recommendations.append(
                "ℹ️ Words are quite long on average. Mix in shorter words for balance."
            )
        
        # Overall Flesch score recommendations
        if flesch < 30:
            recommendations.append(
                "🔴 Content is very difficult to read. Simplify language significantly."
            )
        elif flesch < 50:
            recommendations.append(
                "⚠️ Content is difficult. Consider simpler words and shorter sentences."
            )
        elif flesch < 60:
            recommendations.append(
                "ℹ️ Content is at college level. May be appropriate for educated audience."
            )
        elif flesch > 80:
            recommendations.append(
                "✅ Content is very easy to read. Great for broad audiences!"
            )
        
        # If no issues found
        if not recommendations:
            recommendations.append(
                "✅ Readability is good! Content is clear and accessible."
            )
        
        return recommendations
    
    def _suggest_target_audience(self, flesch_score: float) -> str:
        """Suggest target audience based on Flesch score.
        
        Args:
            flesch_score: Flesch Reading Ease score
        
        Returns:
            Target audience description
        """
        if flesch_score >= 80:
            return "General public, social media, casual readers"
        elif flesch_score >= 70:
            return "General public, blog posts, news articles"
        elif flesch_score >= 60:
            return "Educated adults, business professionals"
        elif flesch_score >= 50:
            return "College students, technical readers"
        elif flesch_score >= 30:
            return "College graduates, industry professionals"
        else:
            return "Academic, scientific, highly specialized audiences"
    
    def _empty_response(self) -> Dict:
        """Return empty response for insufficient content."""
        return {
            "readability_score": 0,
            "metrics": {},
            "statistics": {},
            "recommendations": ["Content too short to analyze"],
            "target_audience": "Unknown"
        }
    
    def _unavailable_response(self) -> Dict:
        """Return response when textstat is not available."""
        return {
            "readability_score": 0,
            "metrics": {},
            "statistics": {},
            "recommendations": ["Install textstat library for readability analysis: pip install textstat"],
            "target_audience": "Unknown",
            "error": "textstat library not installed"
        }
    
    def quick_score(self, content: str) -> float:
        """Get quick Flesch Reading Ease score.
        
        Args:
            content: Text to analyze
        
        Returns:
            Flesch Reading Ease score (0-100), or 0 if unavailable
        """
        if not self.available or not content:
            return 0.0
        
        try:
            return round(textstat.flesch_reading_ease(content), 1)
        except:
            return 0.0
