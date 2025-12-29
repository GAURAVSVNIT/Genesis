import asyncio
from typing import Dict, Any
from intelligence.seo.optimizer import SEOOptimizer

async def evaluate_seo(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Evaluate SEO of the blog content.
    Returns status 'accept' or 'revise' based on score and iterations.
    """
    blog_content = state.get("blog", "")
    keywords = state.get("keywords", [])
    iteration_count = state.get("iteration_count", 0)
    
    if not blog_content:
        return {"seo_status": "revise", "seo_result": {}}

    try:
        optimizer = SEOOptimizer()
        
        # Optimize/Analyze content
        result = await optimizer.optimize(
            content=blog_content,
            keywords=keywords,
            generate_metadata=True
        )
        
        seo_score = result.get("seo_score", 0)
        suggestions = result.get("suggestions", [])
        
        # logic for acceptance
        # Accept if score > 80 OR we have iterated 3 times
        status = "accept"
        if seo_score < 80 and iteration_count < 3:
            status = "revise"
            
        print(f"DEBUG: SEO Score: {seo_score}, Iteration: {iteration_count}, Status: {status}")
            
        return {
            "seo_result": result,
            "seo_score": seo_score,
            "seo_status": status,
            "iteration_count": iteration_count + 1,
            "seo_feedback": "\n".join(suggestions[:5]) if status == "revise" else ""
        }
        
    except Exception as e:
        print(f"Error in SEO evaluation: {e}")
        return {
            "seo_status": "accept", # Pass through on error
            "seo_result": {},
            "iteration_count": iteration_count + 1
        }
