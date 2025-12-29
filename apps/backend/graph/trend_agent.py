import asyncio
from typing import Dict, List, Any
from intelligence.trend_collector import TrendCollector
from intelligence.trend_analyzer import TrendAnalyzer

async def analyze_trends(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Fetch and analyze trends based on the prompt keywords.
    Updates state with trend data and context.
    """
    prompt = state.get("prompt", "")
    if not prompt:
        return {"trend_context": ""}
        
    # Initialize services
    collector = TrendCollector(use_cache=True)
    analyzer = TrendAnalyzer()
    
    # Extract keywords
    keywords, tone = analyzer.extract_keywords_and_tone(prompt)
    
    # Store keywords in state for future use (SEO)
    state_updates = {"keywords": keywords, "tone": tone}
    
    try:
        # Fetch trends
        # Note: In a real run, we might want to be selective about sources based on config
        trend_data = await collector.collect_all_trends(keywords)
        
        # Analyze trends for generation
        analysis = await analyzer.analyze_for_generation(prompt, keywords, trend_data)
        
        # Build context string for the writer
        insights = analysis.get("insights", [])
        recommendations = analysis.get("recommendations", [])
        top_topics = analysis.get("trending_topics", [])[:3]
        
        # Format trend context
        trend_context = "TREND ANALYSIS INSIGHTS:\n"
        if insights:
            trend_context += "Insights:\n- " + "\n- ".join(insights[:3]) + "\n\n"
            
        if recommendations:
            trend_context += "Recommendations:\n- " + "\n- ".join(recommendations[:3]) + "\n\n"
            
        if top_topics:
            trend_context += "Trending Topics to Reference:\n"
            for topic in top_topics:
                trend_context += f"- {topic.get('title')} ({topic.get('source')})\n"
        
        state_updates["trend_data"] = analysis
        state_updates["trend_context"] = trend_context
        
        return state_updates
        
    except Exception as e:
        print(f"Error in trend analysis: {e}")
        # Fallback to empty context on error so workflow doesn't break
        return {"trend_context": "", "keywords": keywords or []}
