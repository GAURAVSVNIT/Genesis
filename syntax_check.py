import sys
import os

# Add backend to path
sys.path.append(os.path.join(os.getcwd(), 'apps', 'backend'))

try:
    print("Checking intelligence.image_prompter...")
    from apps.backend.intelligence import image_prompter
    print(" image_prompter imported successfully.")
except Exception as e:
    print(f" Error importing image_prompter: {e}")

try:
    print("Checking api.v1.content...")
    # Mocking missing dependencies if necessary, but robust imports should handle it
    # We might need to mock config or database if they are initialized on import
    # But usually fastapi routers are fine.
    # However, content.py imports get_db which imports SessionLocal. 
    # Let's see if it crashes.
    from apps.backend.api.v1 import content
    print(" content imported successfully.")
except Exception as e:
    print(f" Error importing content: {e}")
