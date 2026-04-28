import os
import requests
import time
import sys

# Define base URL for the backend
BASE_URL = "http://localhost:8000"

# Path to the decoy environment file
DECOY_ENV_PATH = os.path.join(os.path.dirname(__file__), "..", "backend", "decoys", "honeytokens", ".env")

def print_step(msg):
    print(f"[*] {msg}")
    time.sleep(1)

def print_success(msg):
    print(f"[+] {msg}")
    
def print_error(msg):
    print(f"[!] {msg}")

def read_decoy_credentials():
    if not os.path.exists(DECOY_ENV_PATH):
        print_error(f"Decoy file not found at {DECOY_ENV_PATH}")
        print_error("Please ensure the backend is running so it can generate the honeytokens.")
        sys.exit(1)
        
    creds = {}
    with open(DECOY_ENV_PATH, "r") as f:
        for line in f:
            if "=" in line:
                key, val = line.strip().split("=", 1)
                creds[key] = val
    return creds

def attack_vault(token):
    print_step("Attempting to dump HashiCorp Vault secrets...")
    try:
        res = requests.get(f"{BASE_URL}/api/v1/internal/vault/secrets", params={"token": token}, timeout=5)
        if res.status_code == 200:
            print_success(f"Vault data: {res.json()}")
        else:
            print_error(f"Vault access denied: {res.status_code} - {res.text}")
    except requests.exceptions.RequestException as e:
        print_error(f"Connection failed: {e}")

def attack_s3(api_key):
    print_step("Attempting to access production S3 backups...")
    try:
        res = requests.post(f"{BASE_URL}/api/v1/internal/s3-mock", headers={"X-API-Key": api_key}, timeout=5)
        if res.status_code == 200:
            print_success(f"S3 data: {res.json()}")
        else:
            print_error(f"S3 access denied: {res.status_code} - {res.text}")
    except requests.exceptions.RequestException as e:
        print_error(f"Connection failed: {e}")

def main():
    print("="*50)
    print("   LATERAL MOVEMENT AUTOMATED EXPLOIT SCRIPT   ")
    print("="*50)
    
    print_step("Scanning local filesystem for exposed credentials...")
    creds = read_decoy_credentials()
    
    if "INTERNAL_API_TOKEN" in creds:
        print_success(f"Found internal API token ending in ...{creds['INTERNAL_API_TOKEN'][-6:]}")
        attack_vault(creds["INTERNAL_API_TOKEN"])
        
    print("-" * 30)
    
    if "AWS_ACCESS_KEY_ID" in creds:
        print_success(f"Found AWS credentials ending in ...{creds['AWS_ACCESS_KEY_ID'][-4:]}")
        attack_s3(creds["AWS_ACCESS_KEY_ID"])
        
    print("-" * 30)
    
    # Rapid attempts to trigger blacklisting
    print_step("Running rapid automated scanner to map internal endpoints (should trigger blacklist)...")
    for i in range(5):
        try:
            res = requests.get(f"{BASE_URL}/api/v1/internal/db-sync")
            if res.status_code == 403 and "flagged" in res.text:
                print_error(f"  [!] Blocked by IP blacklist: {res.text}")
                break
            print(f"  [>] Probe {i+1} sent...")
        except:
            pass
            
    print("="*50)
    print_step("Exploit sequence complete.")

if __name__ == "__main__":
    main()
