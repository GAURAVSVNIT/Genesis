"""
Service for generating images using Vertex AI Imagen.
"""
import os
import base64
from typing import Optional
from vertexai.preview.vision_models import ImageGenerationModel
import vertexai
from core.config import settings

class ImageCollector:
    """Generates high-quality images using Vertex AI Imagen."""
    
    def __init__(self):
        self.project_id = settings.GCP_PROJECT_ID
        self.location = "us-central1" # Image generation often requires specific regions
        self._model = None
        
        if self.project_id:
            try:
                vertexai.init(project=self.project_id, location=self.location)
                # Load the model only when needed or lazy load
            except Exception as e:
                print(f"[ImageCollector] Failed to init Vertex AI: {e}")
                with open("debug_redis.log", "a", encoding="utf-8") as f:
                     f.write(f"[ImageCollector] Init Error: {e}\n")

    @property
    def model(self):
        if not self._model and self.project_id:
            try:
                self._model = ImageGenerationModel.from_pretrained("imagegeneration@006")
            except Exception as e:
                print(f"[ImageCollector] Failed to load Imagen model: {e}")
        return self._model
    
    async def get_relevant_image(self, query: str, model_provider: str = "gpt") -> Optional[str]:
        """
        Generate a relevant image for the given query using the selected provider.
        
        Args:
            query: Image generation prompt
            model_provider: 'gemini' (uses Vertex AI Imagen) or 'gpt' (uses DALL-E 3)
            
        Returns:
             Base64 Data URI string or URL
        """
        
        # === OPTION 1: OpenAI DALL-E 3 ===
        if model_provider.startswith("gpt"):
            try:
                print(f"[MODEL INFO] ImageCollector - Using OpenAI DALL-E 3 for: {query[:50]}...")
                
                if not settings.OPENAI_API_KEY:
                     print("[ImageCollector] ❌ ERROR: OPENAI_API_KEY not found in .env file!")
                     print("[ImageCollector] Please add OPENAI_API_KEY=sk-... to your .env file")
                     return None
                
                try:
                    from openai import OpenAI
                except ImportError:
                    print("[ImageCollector] ❌ ERROR: openai package not installed!")
                    print("[ImageCollector] Run: pip install openai")
                    return None
                     
                client = OpenAI(api_key=settings.OPENAI_API_KEY)
                
                response = client.images.generate(
                    model="dall-e-3",
                    prompt=query,
                    size="1024x1024",
                    quality="standard",
                    n=1,
                    response_format="b64_json" # Get base64 directly
                )
                
                b64_data = response.data[0].b64_json
                print(f"[ImageCollector] ✅ OpenAI image generated successfully")
                return f"data:image/png;base64,{b64_data}"
                
            except Exception as e:
                print(f"[ImageCollector] ❌ OpenAI DALL-E Error: {e}")
                import traceback
                traceback.print_exc()
                # Fallback to Vertex AI if OpenAI fails? Or just return None
                # For now, let's allow fallback to Vertex AI below
                print("[ImageCollector] Falling back to Vertex AI...")

        # === OPTION 2: Vertex AI Imagen (Default) ===
        if not self.model:
            print("[ImageCollector] Vertex AI Model not initialized.")
            return None
            
        try:
            print(f"[MODEL INFO] ImageCollector - Using Vertex AI Imagen for: {query}")
            
            # Generate the image
            response = self.model.generate_images(
                prompt=query,
                number_of_images=1,
                language="en",
                aspect_ratio="16:9",
                safety_filter_level="block_some",
                person_generation="allow_adult",
            )
            
            if response.images:
                img = response.images[0]
                img_bytes = img._image_bytes
                b64_data = base64.b64encode(img_bytes).decode("utf-8")
                return f"data:image/png;base64,{b64_data}"
                
        except Exception as e:
            print(f"[ImageCollector] Vertex AI Generation Error: {str(e)}")
            with open("debug_redis.log", "a", encoding="utf-8") as f:
                 f.write(f"[ImageCollector] Generation Error: {str(e)}\n")
            return None
            
        return None

