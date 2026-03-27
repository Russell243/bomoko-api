import os
from google.cloud import secretmanager
import environ

# Configuration
PROJECT_ID = "cleveland-467300-d1"
ENV_FILE = ".env"

def create_secret(secret_id, payload):
    client = secretmanager.SecretManagerServiceClient()
    parent = f"projects/{PROJECT_ID}"
    
    # Check if secret already exists
    try:
        client.get_secret(request={"name": f"{parent}/secrets/{secret_id}"})
        print(f"Secret {secret_id} already exists, adding new version...")
    except:
        # Create the secret
        client.create_secret(request={
            "parent": parent,
            "secret_id": secret_id,
            "secret": {"replication": {"automatic": {}}}
        })
        print(f"Created secret {secret_id}")

    # Add the secret version
    client.add_secret_version(request={
        "parent": f"{parent}/secrets/{secret_id}",
        "payload": {"data": payload.encode("UTF-8")}
    })
    print(f"Added version to {secret_id}")

def sync_env_to_gcp():
    env = environ.Env()
    if not os.path.exists(ENV_FILE):
        print(f"Error: {ENV_FILE} not found.")
        return

    # Load env file manually as a dictionary to get all keys
    with open(ENV_FILE, 'r') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            if '=' in line:
                key, val = line.split('=', 1)
                key = key.strip()
                val = val.strip()
                if val:
                    print(f"Syncing {key}...")
                    create_secret(f"bomoko_{key.lower()}", val)

if __name__ == "__main__":
    # Note: Requires google-cloud-secret-manager
    # pip install google-cloud-secret-manager
    sync_env_to_gcp()
