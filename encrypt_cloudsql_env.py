#!/usr/bin/env python
"""
Encrypt CloudSQL environment variables to .env.crypt.gcp
Usage: python encrypt_cloudsql_env.py
"""

import os
import json
from pathlib import Path
from cryptography.fernet import Fernet

# CloudSQL variables to extract from .env
CLOUDSQL_VARS = [
    "DB_NAME",
    "DB_USER",
    "DB_HOST",
    "DB_PORT",
    "DOSE_DB_PASSWORD",
    "DATABASE_URL",
    "GCP_PROJECT_ID",
    "CLOUDSQL_CONNECTION_NAME",
]

def get_env_values():
    """Extract CloudSQL variables from .env"""
    env_path = Path(".env")
    if not env_path.exists():
        raise FileNotFoundError(f".env file not found at {env_path}")
    
    values = {}
    with open(env_path) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" in line:
                key, val = line.split("=", 1)
                key = key.strip()
                val = val.strip()
                if key in CLOUDSQL_VARS:
                    values[key] = val
    
    return values

def encrypt_and_save(values):
    """Generate a key, encrypt values, and save to .env.crypt.gcp"""
    # Generate a new Fernet key
    key = Fernet.generate_key()
    cipher = Fernet(key)
    
    # JSON-encode the values
    json_data = json.dumps(values, indent=2)
    
    # Encrypt the JSON
    encrypted_data = cipher.encrypt(json_data.encode())
    
    # Write .env.crypt.gcp with encrypted data and key
    output_path = Path(".env.crypt.gcp")
    with open(output_path, "w") as f:
        f.write("# Encrypted CloudSQL environment variables\n")
        f.write("# ENCRYPTION_KEY (save this securely, share separately):\n")
        f.write(f"# {key.decode()}\n")
        f.write("\n# Encrypted payload (base64):\n")
        f.write(encrypted_data.decode())
    
    print(f"Successfully encrypted CloudSQL variables to {output_path}")
    print(f"\n[ENCRYPTION KEY - save this securely, share separately]:")
    print(f"   {key.decode()}")
    print(f"\n[INSTRUCTIONS FOR SHELA]:")
    print(f"   1. File: {output_path}")
    print(f"   2. Encryption key above (via secure channel)")
    
    return key

def main():
    try:
        print("Encrypting CloudSQL environment variables...\n")
        
        values = get_env_values()
        if not values:
            print("WARNING: No CloudSQL variables found in .env")
            return
        
        print(f"Found {len(values)} CloudSQL variables:")
        for key in values:
            print(f"  - {key}")
        print()
        
        key = encrypt_and_save(values)
        
    except Exception as e:
        print(f"ERROR: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())
