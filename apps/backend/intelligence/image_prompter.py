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

async def generate_image_prompt(topic: str, keywords: List[str], tone: str = "neutral", summary: Optional[str] = None, trends: Optional[List[str]] = None, model: str = "gemini-2.5-flash") -> str:
    """
    Generate a detailed image prompt based on the blog topic, tone, optional summary, and trends.
    Supports both Gemini and OpenAI models based on the model parameter.
    
    Args:
        topic: Main topic for the image
        keywords: Relevant keywords
        tone: Content tone
        summary: Optional content summary
        trends: Optional trending elements
        model: Model to use (gemini-2.5-flash, gpt-4o-mini, etc.)
    """
    try:
        temperature = get_temperature_for_tone(tone)
        
        # Determine which model to use
        use_openai = model.startswith("gpt") or model.startswith("o1")
        
        if use_openai:
            # Use OpenAI
            from openai import AsyncOpenAI
            from core.config import settings
            
            if not settings.OPENAI_API_KEY:
                print("[ImagePrompter] Missing OpenAI API Key, using simple fallback")
                fallback_keywords = ", ".join(keywords[:3])
                return f"A professional {tone} photograph depicting {topic}. Featured elements: {fallback_keywords}. High-quality, detailed composition with dramatic lighting, photorealistic style, 4K resolution, sharp focus."
            
            client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        
        system_context = (
            "You are an expert AI Art Director specializing in creating DALL-E 3 prompts. "
            "Your goal is to write a detailed, specific visual description that will generate a highly relevant feature image. "
            "\n\nRULES:\n"
            "- Be SPECIFIC about the subject matter and context\n"
            "- Include concrete visual elements that directly relate to the topic\n"
            "- Describe lighting, composition, color palette, and atmosphere\n"
            "- Use clear, literal descriptions (DALL-E understands concrete terms better than abstract concepts)\n"
            "- NO text, logos, or words in the image\n"
            "- NO generic phrases like 'professional' or 'high quality'\n"
            "- Start directly with the visual description, no introductory text\n"
            "\nStyles: Photorealistic photography, Digital illustration, 3D render, Minimalist design, Cinematic scene"
        )
        
        user_prompt = (
            f"Blog Topic: {topic}\n"
            f"Keywords: {', '.join(keywords[:5])}\n"  # Limit to top 5 keywords
            f"Content Tone: {tone}\n"
        )

        if trends:
             user_prompt += f"Trending Visual Elements: {', '.join(trends[:3])}\n"  # Top 3 trends
        
        if summary:
            # Use the summary to provide specific context
            user_prompt += f"\nContent Context: {summary[:1500]}\n"
            
        user_prompt += (
            "\nCreate a specific, detailed visual description for DALL-E 3. "
            "Focus on concrete elements, scenes, and objects that directly represent the topic. "
            "Describe what should be in the foreground, background, lighting, and mood:"
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
