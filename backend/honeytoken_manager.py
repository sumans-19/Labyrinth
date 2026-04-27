import os
import json
import uuid
import hashlib
import random
from datetime import datetime
from typing import Dict, List, Any, Optional

REGISTRY_FILE = "honeytoken_registry.json"

class HoneytokenManager:
    def __init__(self, registry_path: str = REGISTRY_FILE):
        self.registry_path = registry_path
        self.tokens = self._load_registry()

    def _load_registry(self) -> Dict[str, Any]:
        if os.path.exists(self.registry_path):
            with open(self.registry_path, "r") as f:
                return json.load(f)
        return {}

    def _save_registry(self):
        with open(self.registry_path, "w") as f:
            json.dump(self.tokens, f, indent=4)

    def generate_tokens(self) -> Dict[str, str]:
        """Generates a set of realistic fake credentials."""
        aws_access_key = f"AKIA{uuid.uuid4().hex[:16].upper()}"
        aws_secret_key = base64_secret = uuid.uuid4().hex + uuid.uuid4().hex[:8]
        mongo_uri = f"mongodb+srv://admin:{uuid.uuid4().hex[:12]}@cluster0.mongodb.net/prod-db?retryWrites=true&w=majority"
        internal_api_token = f"internal_auth_{uuid.uuid4().hex}"
        
        creds = {
            "AWS_ACCESS_KEY_ID": aws_access_key,
            "AWS_SECRET_ACCESS_KEY": aws_secret_key,
            "MONGODB_URI": mongo_uri,
            "INTERNAL_API_TOKEN": internal_api_token
        }
        
        # Register them
        timestamp = datetime.now().isoformat()
        for key, value in creds.items():
            token_hash = hashlib.sha256(value.encode()).hexdigest()
            self.tokens[token_hash] = {
                "type": key,
                "value_preview": value[:10] + "...",
                "created_at": timestamp
            }
        
        self._save_registry()
        return creds

    def create_decoy_files(self, output_dir: str = "decoys/honeytokens"):
        os.makedirs(output_dir, exist_ok=True)
        creds = self.generate_tokens()
        
        # Create .env file
        env_content = "\n".join([f"{k}={v}" for k, v in creds.items()])
        with open(os.path.join(output_dir, ".env"), "w") as f:
            f.write(env_content)
            
        # Create config.json file
        with open(os.path.join(output_dir, "config.json"), "w") as f:
            json.dump(creds, f, indent=4)
            
        print(f"[*] Honeytoken decoy files created in {output_dir}")
        return creds

    def verify_token(self, token_value: str) -> Optional[Dict[str, Any]]:
        token_hash = hashlib.sha256(token_value.encode()).hexdigest()
        return self.tokens.get(token_hash)

if __name__ == "__main__":
    manager = HoneytokenManager()
    manager.create_decoy_files()
