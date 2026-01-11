from typing import Dict, Any
from intelligence.image_collector import ImageCollector
from intelligence.image_prompter import generate_image_prompt

async def generate_image(state: Dict[str, Any]):
    """
    Node that generates an image based on the blog prompt or content.
    """
    try:
        # Check if we already have an image (e.g. from cache or previous run)
        if state.get("image_url"):
            print("[Image Agent] Image already exists in state, skipping.")
            return state
            
        prompt = state.get("prompt", "")
        keywords = state.get("keywords", [])
        tone = state.get("tone", "neutral")
        trends = state.get("trends", [])
        
        # Get blog content if available to use as specific context
        blog_content = state.get("blog", "")
        summary_context = blog_content[:1500] if blog_content else None
        
        # Use AI Art Director to generate specific visual prompt
        print(f"[Image Agent] Consulting Art Director for: {prompt[:30]}... (with {len(trends)} trends)")
        # Default to gemini for image agent unless model is in state
        model = state.get("model", "gemini-2.5-flash")
        query = await generate_image_prompt(prompt, keywords, tone, summary=summary_context, trends=trends, model=model)
        
        print(f"[Image Agent] Generative Query: {query[:50]}...")
        
        collector = ImageCollector()
        image_url = await collector.get_relevant_image(query, model_provider="gpt")
        
        if image_url:
            print("[Image Agent] Image generated successfully.")
            state["image_url"] = image_url
        else:
            print("[Image Agent] Failed to generate image.")
            state["image_url"] = None
            
    except Exception as e:
        print(f"[Image Agent] Error: {e}")
        state["image_url"] = None
        
    return state
