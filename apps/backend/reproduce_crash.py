
import os
import sys

# Clear sensitive environment variables to simulate "missing config" scenarios
# causing startup crashes if code assumes they exist at import time.
keys_to_clear = ["GCP_PROJECT_ID", "UPSTASH_REDIS_REST_URL", "UPSTASH_REDIS_REST_TOKEN", "GOOGLE_API_KEY", "OPENAI_API_KEY"]
for key in keys_to_clear:
    if key in os.environ:
        del os.environ[key]

print("Starting import test...")
try:
    import main
    print("✅ Successfully imported main.py")
except Exception as e:
    print(f"❌ Crash during import: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
