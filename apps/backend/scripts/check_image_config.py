
import sys
import os
# Add backend to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.config import settings
from intelligence.image_collector import ImageCollector

print(f"Checking Configuration:")
print(f"GCP_PROJECT_ID: {settings.GCP_PROJECT_ID}")
print(f"GOOGLE_APPLICATION_CREDENTIALS: {os.environ.get('GOOGLE_APPLICATION_CREDENTIALS')}")

print("\nInitializing ImageCollector...")
try:
    collector = ImageCollector()
    print(f"Project ID in Collector: {collector.project_id}")
    print(f"Model Property Access Attempt:")
    model = collector.model
    if model:
        print("Successfully initialized ImageGenerationModel")
    else:
        print("Failed to initialize ImageGenerationModel (returned None)")
except Exception as e:
    print(f"Exception during initialization: {e}")
