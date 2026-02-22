"""
Service for generating enhanced image descriptions/prompts.
Acts as an "Art Director" to convert simple topics into rich visual descriptions.
Supports both Gemini and OpenAI models.
"""
from typing import List, Optional

def get_temperature_for_tone(tone: str) -> float:
    """
    Map content tone to LLM temperature (creativity level).
    """
    tone_lower = tone.lower()
    
    # High Creativity
    if any(t in tone_lower for t in ['creative', 'humorous', 'witty', 'fictional', 'story']):
        return 0.9
        
    # Low Creativity (Strict/Professional)
    if any(t in tone_lower for t in ['professional', 'technical', 'academic', 'formal', 'business']):
        return 0.2
        
    # Medium Creativity (Default)
    return 0.5

async def generate_image_prompt(
    topic: str, 
    keywords: List[str], 
    tone: str = "neutral", 
    summary: Optional[str] = None, 
    trends: Optional[List[str]] = None, 
    model: str = "gemini-2.5-flash", # Use 2.5-flash as default for better instruction following than 1.5-flash for this task
    style_preference: Optional[str] = None,
    specific_focus: Optional[str] = None,
    exclude_elements: Optional[List[str]] = None,
    variation_level: Optional[str] = "medium"
) -> str:
    """
    Generate a detailed image prompt based on the blog topic, context, and style preferences.
    """
    try:
        # Base temperature - lean towards creativity
        temperature = 0.7 
        
        # Adjust temperature based on variation level
        if variation_level == "high":
            temperature = 0.9
        elif variation_level == "low":
            temperature = 0.4
        
        # Determine which model to use
        use_openai = model.startswith("gpt") or model.startswith("o1")
        
        if use_openai:
            # Use OpenAI
            from openai import AsyncOpenAI
            from core.config import settings
            
            if not settings.OPENAI_API_KEY:
                print("[ImagePrompter] Missing OpenAI API Key, using simple fallback")
                fallback_keywords = ", ".join(keywords[:3])
                return f"A professional {tone} photograph depicting {topic}. Featured elements: {fallback_keywords}. High-quality, detailed composition."
            
            client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        
        system_context = (
            "You are an expert Editorial Illustrator and Concept Artist. "
            "Your goal is to visualize a specific scene or concept described in the 'Content Context' into a highly detailed, award-winning image prompt for DALL-E 3/Imagen. "
            "\n\nRULES:\n"
            "- **VISUALIZE THE SCENE**: Do not just list keywords. Describe *what is happening*.\n"
            "- **BE BOLD**: Avoid generic, safe, or stock-photo style descriptions. Go for dramatic lighting, interesting angles, and dynamic compositions.\n"
            "- **SHOW, DON'T TELL**: Instead of saying 'inspirational', describe 'warm golden hour lighting illuminating a mountaintop'.\n"
            "- **CONTEXT IS KING**: Use the provided Content Context to find a specific metaphor or scene to depict.\n"
            "- Start directly with the visual description.\n"
            "- NO text, logos, or words in the image.\n"
        )
        
        user_prompt = (
            f"Main Topic: {topic}\n"
            f"Keywords: {', '.join(keywords[:5])}\n"
            f"Content Tone: {tone}\n"
        )

        if style_preference:
            user_prompt += f"Visual Style: {style_preference} (Strictly adhere to this style)\n"
            
        if specific_focus:
            user_prompt += f"Primary Focus/Subject: {specific_focus}\n"
            
        if exclude_elements:
             user_prompt += f"Avoid Including: {', '.join(exclude_elements)}\n"

        if trends:
             user_prompt += f"Trending Visual Elements to Incorporate: {', '.join(trends[:3])}\n"
        
        if summary:
            # High priority on context
            user_prompt += f"\nCONTENT CONTEXT (Visualize a specific scene from this): \n{summary[:2000]}\n"
            
        user_prompt += (
            "\nTask: Write a cohesive, descriptive visual prompt. "
            "Combine the style, tone, and context into a single, vivid scene description. "
            "Focus on lighting (e.g., volumetric, cinematic), texture, and composition."
        )
        
        if use_openai:
            # Use OpenAI GPT to generate the prompt
            response = await client.chat.completions.create(
                model="gpt-4o-mini",  # Fast and cost-effective
                messages=[
                    {"role": "system", "content": system_context},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=temperature,
                max_tokens=250
            )
            
            if response.choices and response.choices[0].message.content:
                cleaned_prompt = response.choices[0].message.content.strip().replace('"', '')
                print(f"[ImagePrompter] Generated Prompt (OpenAI, T={temperature}): {cleaned_prompt[:100]}...")
                return cleaned_prompt
        else:
            # Use Gemini
            import vertexai
            from vertexai.preview.generative_models import GenerativeModel, GenerationConfig
            from core.config import settings
            
            if not settings.GCP_PROJECT_ID:
                print("[ImagePrompter] Missing GCP_PROJECT_ID for Gemini, using fallback")
                raise Exception("GCP not configured")
            
            vertexai.init(project=settings.GCP_PROJECT_ID, location="us-central1")
            gemini_model = GenerativeModel(model)
            
            full_prompt = f"{system_context}\n\n{user_prompt}"
            config = GenerationConfig(
                temperature=temperature,
                max_output_tokens=250,
                top_p=0.9,
                top_k=40
            )
            
            response = await gemini_model.generate_content_async(full_prompt, generation_config=config)
            
            if response.text:
                cleaned_prompt = response.text.strip().replace('"', '')
                print(f"[ImagePrompter] Generated Prompt (Gemini, T={temperature}): {cleaned_prompt[:100]}...")
                return cleaned_prompt
            
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"[ImagePrompter] FAILED to generate prompt. Error: {e}")
        print(f"[ImagePrompter] Traceback: {error_details}")
        
        # Enhanced fallback with more specific description
        fallback_keywords = ", ".join(keywords[:3])
        fallback_prompt = (
            f"A professional {tone} photograph depicting {topic}. "
            f"Featured elements: {fallback_keywords}. "
            f"High-quality, detailed composition with dramatic lighting, "
            f"photorealistic style, 4K resolution, sharp focus."
        )
        print(f"[ImagePrompter] Using enhanced fallback: {fallback_prompt}")
        return fallback_prompt

    return topic
