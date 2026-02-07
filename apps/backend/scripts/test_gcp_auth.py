
import os
import google.auth
from google.auth.transport.requests import Request

# Path to the credentials file
KEY_PATH = "e:/GENE/Genesis/apps/backend/genecis-481617-4dc0049b7bef.json"
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = KEY_PATH

print("\n--- Testing Google Auth with Scope ---")
try:
    # Explicitly request cloud-platform scope
    scopes = ["https://www.googleapis.com/auth/cloud-platform"]
    credentials, project_id = google.auth.default(scopes=scopes)
    
    print(f"✅ Auth default successful. Project: {project_id}")
    
    # Try to refresh token
    print("Attempting to refresh token...")
    credentials.refresh(Request())
    print("✅ Token refresh successful.")
    # Safe printing of partial token
    token_preview = credentials.token[:10] if credentials.token else "None"
    print(f"Token preview: {token_preview}...")
    
    # Init Vertex AI
    import vertexai
    vertexai.init(project=project_id, location="us-central1")
    print("✅ Vertex AI init successful.")
    
except Exception as e:
    print(f"❌ Auth failed: {e}")
    exit(1)
