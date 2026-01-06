# agents/safety.py
async def safety_check(state):
    """
    Checks if the content is safe.
    This can be used both as an initial check and a final check.
    """
    prompt = state.get("prompt", "")
    content = state.get("blog", "")
    
    # Simple keyword-based safety check for demonstration
    unsafe_keywords = ["unsafe_test", "illegal_content_trigger"]
    
    if any(k in prompt.lower() for k in unsafe_keywords) or any(k in content.lower() for k in unsafe_keywords):
        state["status"] = "unsafe"
        state["safety_feedback"] = "Content triggered safety filters."
    else:
        state["status"] = "safe"
        
    return state
