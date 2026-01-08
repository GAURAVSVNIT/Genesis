"""
Service for generating enhanced image descriptions/prompts using Vertex AI LLM.
Acts as an "Art Director" to convert simple topics into rich visual descriptions.
"""
from typing import List, Optional
import vertexai
from vertexai.preview.generative_models import GenerativeModel, GenerationConfig
from core.config import settings

# Initialize Vertex AI
if settings.GCP_PROJECT_ID:
    try:
        vertexai.init(project=settings.GCP_PROJECT_ID, location="us-central1")
    except Exception as e:
        print(f"[ImagePrompter] Failed to init Vertex AI: {e}")

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

async def generate_image_prompt(topic: str, keywords: List[str], tone: str = "neutral", summary: Optional[str] = None, trends: Optional[List[str]] = None) -> str:
    """
    Generate a detailed image prompt based on the blog topic, tone, optional summary, and trends.
    """
    try:
        model = GenerativeModel("gemini-2.0-flash")
        
        temperature = get_temperature_for_tone(tone)
        config = GenerationConfig(
            temperature=temperature,
            max_output_tokens=150, # Keep descriptions concise enough for Imagen
            top_p=0.9,
            top_k=40
        )
        
        system_context = (
            "You are an expert AI Art Director. Your goal is to write ONE paragraph "
            "describing a high-quality, visually striking feature image for a blog post. "
            "Do NOT include introductory text like 'Here is a prompt'. Just write the visual description. "
            "Focus on lighting, composition, style, and mood. "
            "Avoid text in the image. "
            "Compatible styles: Photorealistic, 3D Render, Minimalist Vector, Cinematic."
        )
        
        user_prompt = (
            f"Blog Topic: {topic}\n"
            f"Keywords: {', '.join(keywords)}\n"
            f"Content Tone: {tone}\n"
        )

        if trends:
             user_prompt += f"Trending Elements to Include: {', '.join(trends)}\n"
        
        if summary:
            # Use the summary to provide specific context
            user_prompt += f"\nBlog Context/Summary: {summary[:1500]}\n" # Limit summary length
            
        user_prompt += "\nCreate a visual description for the header image:"
        
        # Combine manually if using a model that doesn't support system instruction in init
        # Gemini 1.5 Pro supports system instructions but keeping it simple for compatibility
        full_prompt = f"{system_context}\n\n{user_prompt}"
        
        response = await model.generate_content_async(
            full_prompt,
            generation_config=config
        )
        
        if response.text:
            cleaned_prompt = response.text.strip().replace('"', '')
            print(f"[ImagePrompter] Generated Prompt (T={temperature}): {cleaned_prompt[:50]}...")
            return cleaned_prompt
            
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"[ImagePrompter] FAILED to generate prompt. Error: {e}")
        print(f"[ImagePrompter] Traceback: {error_details}")
        
        # Fallback to simple keyword join
        return f"{topic}, {', '.join(keywords)}, high quality, professional, 4k"

    return topic
