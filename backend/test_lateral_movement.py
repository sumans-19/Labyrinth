import json
import requests
import os

# Load the registered tokens to simulate an attacker who found the decoy file
REGISTRY_FILE = "honeytoken_registry.json"

def test_lateral_movement():
    if not os.path.exists(REGISTRY_FILE):
        print("[!] Registry file not found. Run honeytoken_manager.py first.")
        return

    with open(REGISTRY_FILE, "r") as f:
        registry = json.load(f)

    if not registry:
        print("[!] No tokens registered.")
        return

    # Pick a random token from the registry
    token_hash = list(registry.keys())[0]
    token_type = registry[token_hash]["type"]
    
    # We need the actual value, which isn't stored in the registry (only hashes)
    # But wait, my test script won't know the value unless I grab it from the decoy files
    
    # Let's try to grab it from decoys/honeytokens/.env
    env_path = os.path.join("decoys", "honeytokens", ".env")
    token_value = None
    if os.path.exists(env_path):
        with open(env_path, "r") as f:
            for line in f:
                if line.startswith(token_type):
                    token_value = line.split("=")[1].strip()
                    break

    if not token_value:
        print(f"[!] Could not find value for {token_type} in .env file.")
        return

    print(f"[*] Simulating lateral movement with token type: {token_type}")
    print(f"[*] Target: http://localhost:8000/api/v1/internal/db-sync")
    
    headers = {
        "Authorization": f"Bearer {token_value}"
    }
    
    try:
        response = requests.get("http://localhost:8000/api/v1/internal/db-sync", headers=headers)
        print(f"[*] Response: {response.status_code} - {response.json()}")
        print("[*] Check your Labyrinth Forge Dashboard! You should see a LATERAL MOVEMENT alert.")
    except Exception as e:
        print(f"[!] Request failed: {e}")

if __name__ == "__main__":
    test_lateral_movement()
