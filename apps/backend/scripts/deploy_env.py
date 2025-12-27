import os
import sys
import subprocess

# No external dependency needed for simple yaml writing
# Actually let's just write simple yaml format manually or import it.
# If pyyaml is not available, we can just write KEY: "VALUE"
# But standard library doesn't have yaml.
# We can use json? gcloud supports --env-vars-file as YAML.
# Let's write a simple manual yaml writer since values might be simple strings.

def escape_yaml_value(value):
    # Simple escaping for double-quoted yaml strings
    return '"' + value.replace('\\', '\\\\').replace('"', '\\"') + '"'

def deploy_env():
    env_file = ".env"
    yaml_file = "env_vars.yaml"
    
    if not os.path.exists(env_file):
        print(f"Error: {env_file} not found")
        sys.exit(1)

    env_dict = {}
    with open(env_file, "r") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" in line:
                key, value = line.split("=", 1)
                key = key.strip()
                value = value.strip()
                # Remove quotes if present
                if (value.startswith('"') and value.endswith('"')) or (value.startswith("'") and value.endswith("'")):
                    value = value[1:-1]
                
                # Filter out local file paths for credentials, Cloud Run uses built-in identity
                if key == "GOOGLE_APPLICATION_CREDENTIALS" and ("\\" in value or "/" in value):
                    print(f"Skipping local file path for {key}")
                    continue
                    
                env_dict[key] = value

    if not env_dict:
        print("No environment variables found.")
        return

    # Write to yaml file
    with open(yaml_file, "w") as f:
        for key, value in env_dict.items():
            f.write(f"{key}: {escape_yaml_value(value)}\n")
    
    cmd = [
        "gcloud", "run", "deploy", "genesis-backend",
        "--source", ".",
        "--env-vars-file", yaml_file,
        "--region", "us-central1",
        "--project", "genecis-481617",
        "--allow-unauthenticated"
    ]
    
    print(f"Deploying to Cloud Run with vars from {yaml_file}...")
    
    try:
        # Use shell=True on Windows
        subprocess.run(cmd, check=True, shell=True)
        print("Successfully deployed and updated environment variables.")
    except subprocess.CalledProcessError as e:
        print(f"Failed to deploy: {e}")
        sys.exit(1)
    finally:
        # Cleanup
        if os.path.exists(yaml_file):
             os.remove(yaml_file)

if __name__ == "__main__":
    deploy_env()
