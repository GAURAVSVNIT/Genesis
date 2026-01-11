import dotenv
import os

# Load environment variables first
dotenv.load_dotenv()

from core.vertex_ai import get_vertex_ai_service

# Initialize Vertex AI service
llm = get_vertex_ai_service(project_id=os.getenv("GCP_PROJECT_ID"), model="gemini-2.5-flash")

async def write_blog(state):
    # Base prompt
    prompt = f"""
    Write a {state.get('length', 'medium')} blog post.
    Topic: {state.get('prompt', '')}
    Tone: {state.get('tone', 'informative')}
    """
    
    # Add Trend Context if available
    trend_context = state.get("trend_context", "")
    if trend_context:
        prompt += f"\n\nMARKET/TREND CONTEXT (Use this to potentially guide the angle):\n{trend_context}"
        
    # Add Uniqueness Feedback if available
    uniqueness_feedback = state.get("uniqueness_feedback", "")
    if uniqueness_feedback:
        prompt += f"\n\nCRITICAL INSTRUCTION - UNIQUENESS CHECK FAILED:\n{uniqueness_feedback}\nensure the new draft takes a different angle or perspective."
        
    # Add SEO Feedback if available
    seo_feedback = state.get("seo_feedback", "")
    if seo_feedback:
        prompt += f"\n\nSEO IMPROVEMENT REQUEST:\nThe previous draft needs improvement. Please revise based on these SEO suggestions:\n{seo_feedback}"
        
    # Add structure
    prompt += """
    \nStructure:
    - Engaging Title
    - Introduction (Hook)
    - Structured Body with Clear Headings
    - Practical Takeaways
    - Conclusion
    """

    res = await llm.ainvoke(prompt)
    state["blog"] = res.content
    return state