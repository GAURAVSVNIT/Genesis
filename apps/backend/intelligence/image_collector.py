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
    
    async def get_relevant_image(self, query: str, model_provider: str = "vertex") -> Optional[str]:
        """
        Generate a relevant image for the given query using the selected provider.
        
        Args:
            query: Image generation prompt
            model_provider: 'vertex' (Imagen - Default) or 'gpt' (DALL-E 3)
            
        Returns:
             Base64 Data URI string or URL
        """
        
        # Helper function for DALL-E generation
        async def generate_with_dalle(prompt):
            try:
                print(f"[MODEL INFO] ImageCollector - Using OpenAI DALL-E 3 for: {prompt[:50]}...")
                
                if not settings.OPENAI_API_KEY:
                     print("[ImageCollector] ❌ ERROR: OPENAI_API_KEY not found in .env file!")
                     return None
                
                try:
                    from openai import OpenAI
                    client = OpenAI(api_key=settings.OPENAI_API_KEY)
                    response = client.images.generate(
                        model="dall-e-3",
                        prompt=prompt,
                        size="1024x1024",
                        quality="standard",
                        n=1,
                        response_format="b64_json"
                    )
                    b64_data = response.data[0].b64_json
                    print(f"[ImageCollector] ✅ OpenAI image generated successfully")
                    return f"data:image/png;base64,{b64_data}"
                except ImportError:
                    print("[ImageCollector] ❌ ERROR: openai package not installed!")
                    return None
            except Exception as e:
                print(f"[ImageCollector] ❌ OpenAI DALL-E Error: {e}")
                return None

        # Helper function for Vertex Imagen generation
        async def generate_with_vertex(prompt):
            if not self.model:
                print("[ImageCollector] Vertex AI Model not initialized.")
                return None
                
            try:
                print(f"[MODEL INFO] ImageCollector - Using Vertex AI Imagen for: {prompt}")
                response = self.model.generate_images(
                    prompt=prompt,
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
                return None
            return None

        # === EXECUTION LOGIC ===
        
        if model_provider == "gpt":
            # Explicitly requested GPT
            return await generate_with_dalle(query)
            
        else:
            # Default to Vertex, Fallback to GPT
            image = await generate_with_vertex(query)
            if image:
                return image
            
            print("[ImageCollector] ⚠️ Vertex AI failed, falling back to DALL-E 3...")
            return await generate_with_dalle(query)
        
        return None

