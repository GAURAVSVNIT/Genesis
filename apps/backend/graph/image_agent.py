from typing import Dict, Any
from intelligence.image_collector import ImageCollector

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
        
        # Decide query: use first keyword or prompt excerpt
        query = keywords[0] if keywords else prompt[:50]
        
        print(f"[Image Agent] Generating image for query: {query}")
        
        collector = ImageCollector()
        image_url = await collector.get_relevant_image(query)
        
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
