import os

env_path = 'apps/backend/.env'

if not os.path.exists(env_path):
    print(f"❌ File not found: {env_path}")
    exit(1)

print(f"✅ Reading {env_path}...")

with open(env_path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

print(f"Found {len(lines)} lines.")

keys_found = []
for i, line in enumerate(lines):
    line = line.strip()
    if not line or line.startswith('#'):
        continue
    
    if '=' in line:
        key = line.split('=')[0].strip()
        keys_found.append(key)
        # Check for our specific keys
        if key in ['OPENAI_API_KEY', 'GROQ_API_KEY']:
            val = line.split('=')[1].strip()
            masked = val[:5] + "..." + val[-4:] if len(val) > 10 else "SHORT/EMPTY"
            print(f"Line {i+1}: {key} FOUND! Value: {masked}")

print("\nAll Keys Found:", keys_found)
