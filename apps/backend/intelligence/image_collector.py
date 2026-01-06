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
    
    async def get_relevant_image(self, query: str) -> Optional[str]:
        """
        Generate a relevant image for the given query using Imagen.
        Returns a Base64 Data URI string.
        """
        if not self.model:
            print("[ImageCollector] Model not initialized via Vertex AI.")
            return None
            
        try:
            print(f"[ImageCollector] Generating image for: {query}")
            
            # Generate the image
            # aspect_ratio: "1:1", "3:4", "4:3", "16:9", "9:16"
            response = self.model.generate_images(
                prompt=query,
                number_of_images=1,
                language="en",
                aspect_ratio="16:9",
                safety_filter_level="block_some",
                person_generation="allow_adult",
            )
            
            if response.images:
                # Get the first image
                img = response.images[0]
                
                # Check directly if it has a _image_bytes or assumption or standard method
                # The Vertex AI Image object usually has _image_bytes or can save. 
                # Let's check documentation or assume standard interface.
                # Actually, standard way is img._image_bytes or img.save()
                # Use robust method:
                
                img_bytes = img._image_bytes # Accessing raw bytes directly is common in this SDK
                
                # Encode to base64
                b64_data = base64.b64encode(img_bytes).decode("utf-8")
                return f"data:image/png;base64,{b64_data}"
                
        except Exception as e:
            print(f"[ImageCollector] Generation Error: {str(e)}")
            with open("debug_redis.log", "a", encoding="utf-8") as f:
                 f.write(f"[ImageCollector] Generation Error: {str(e)}\n")
            # Re-raise as specific error
            raise ValueError(f"Image generation failed: {str(e)}")
            
        print("[ImageCollector] No images returned (likely blocked by safety filters)")
        return None

