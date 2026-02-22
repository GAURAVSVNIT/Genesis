import sys
import os

# Assume running from apps/backend (where pyproject.toml is)
# Add current directory to path just in case
sys.path.append(os.getcwd())

print(f"Working directory: {os.getcwd()}")
print(f"Python path: {sys.path[:3]}")

try:
    print("Checking intelligence.image_prompter...")
    from intelligence import image_prompter
    print("intelligence.image_prompter imported successfully.")
except ImportError as e:
    print(f" Error importing intelligence.image_prompter: {e}")
except Exception as e:
    print(f" Unexpected error checking image_prompter: {e}")

try:
    print("Checking api.v1.content...")
    from api.v1 import content
    print(" api.v1.content imported successfully.")
except ImportError as e:
    print(f" Error importing api.v1.content: {e}")
except Exception as e:
    print(f" Unexpected error checking content: {e}")
