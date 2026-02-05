import os
from pathlib import Path
from dotenv import load_dotenv

# Mimic the loading logic in config.py
BACKEND_DIR = Path(__file__).parent
print(f"Backend Dir: {BACKEND_DIR}")

env_path = BACKEND_DIR / '.env'
print(f"Loading env from: {env_path}, Exists: {env_path.exists()}")
load_dotenv(env_path)

cred_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
print(f"GOOGLE_APPLICATION_CREDENTIALS raw: {cred_path}")

if cred_path:
    # Check if absolute or relative
    p = Path(cred_path)
    print(f"Is absolute: {p.is_absolute()}")
    print(f"Exists: {p.exists()}")
    
    if not p.is_absolute():
        # Try resolving relative to backend dir
        resolved = BACKEND_DIR / cred_path
        print(f"Resolved relative to backend: {resolved}")
        print(f"Resolved Exists: {resolved.exists()}")
        
        # Try resolving relative to CWD
        cwd_resolved = Path.cwd() / cred_path
        print(f"Resolved relative to CWD ({Path.cwd()}): {cwd_resolved}")
        print(f"CWD Resolved Exists: {cwd_resolved.exists()}")
