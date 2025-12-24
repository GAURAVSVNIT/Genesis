"""
Service for collecting images from Unsplash.
"""
import os
import httpx
from typing import Optional
import random

class ImageCollector:
    """Collects high-quality images from Unsplash based on keywords."""
    
    BASE_URL = "https://api.unsplash.com"
    
    def __init__(self):
        self.access_key = os.getenv("UNSPLASH_ACCESS_KEY")
    
    async def get_relevant_image(self, query: str) -> Optional[str]:
        """
        Fetch a relevant image URL for the given query.
        Returns the 'regular' size image URL or None if failed.
        """
        if not self.access_key:
            print("[ImageCollector] No Unsplash Access Key configured.")
            return None
            
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.BASE_URL}/search/photos",
                    params={
                        "query": query,
                        "per_page": 5,
                        "orientation": "landscape",
                        "content_filter": "high"
                    },
                    headers={"Authorization": f"Client-ID {self.access_key}"},
                    timeout=5.0
                )
                
                if response.status_code == 200:
                    data = response.json()
                    results = data.get("results", [])
                    if results:
                        # Pick a random one from top 5 to vary it slightly if query is same
                        selected = random.choice(results)
                        # Prefer regular, fallback to small/full
                        urls = selected.get("urls", {})
                        return urls.get("regular", urls.get("small"))
                else:
                    print(f"[ImageCollector] API Error: {response.status_code} - {response.text}")
                    
        except Exception as e:
            print(f"[ImageCollector] Exception: {str(e)}")
            
        return None
