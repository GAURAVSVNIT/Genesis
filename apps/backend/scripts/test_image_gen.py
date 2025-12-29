import asyncio
import os
import sys

# Add parent directory to path to import backend modules
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from intelligence.image_collector import ImageCollector

async def test_generation():
    print("Initializing ImageCollector...")
    collector = ImageCollector()
    
    query = "A futuristic cyberpunk city with neon lights, high quality, digital art"
    print(f"Testing generation with query: '{query}'")
    
    try:
        result = await collector.get_relevant_image(query)
        
        if result:
            print("✅ Success! Image generated.")
            print(f"Result starts with: {result[:50]}...")
            
            # Save to file to verify
            if result.startswith("data:image/"):
                header, encoded = result.split(",", 1)
                import base64
                data = base64.b64decode(encoded)
                with open("test_gen_image.png", "wb") as f:
                    f.write(data)
                print("Saved to test_gen_image.png")
            else:
                print("Result format unexpected (not base64 data URI)")
        else:
            print("❌ Failed to generate image (returned None)")
            
    except Exception as e:
        print(f"❌ Exception during test: {e}")

if __name__ == "__main__":
    asyncio.run(test_generation())
