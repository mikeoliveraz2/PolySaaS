"""
One-time utility: parse .env and upload each key as a separate secret to GCP Secret Manager.
Usage:
    pip install google-cloud-secret-manager
    python upload_env_to_secret_manager.py [--dry-run]
"""
import sys
import os
from google.cloud import secretmanager

PROJECT_ID = "application-integration-4524"
ENV_FILE = ".env"


def upload_env_to_secret_manager(project_id: str, env_file: str, dry_run: bool = False):
    client = None if dry_run else secretmanager.SecretManagerServiceClient()

    skipped = []
    uploaded = []
    errors = []

    with open(env_file) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            if '=' not in line:
                continue

            key, value = line.split('=', 1)
            key = key.strip()
            value = value.strip().strip('"\'')

            if not value:
                skipped.append(key)
                continue

            secret_id = key.lower().replace('_', '-')

            if dry_run:
                print(f"  [DRY RUN] Would upload: {key} → {secret_id}")
                uploaded.append(key)
                continue

            try:
                client.create_secret(
                    request={
                        "parent": f"projects/{project_id}",
                        "secret_id": secret_id,
                        "secret": {"replication": {"automatic": {}}},
                    }
                )
            except Exception:
                pass  # Already exists — will just add a new version

            try:
                client.add_secret_version(
                    request={
                        "parent": f"projects/{project_id}/secrets/{secret_id}",
                        "payload": {"data": value.encode("UTF-8")},
                    }
                )
                print(f"  ✅ {key} → {secret_id}")
                uploaded.append(key)
            except Exception as e:
                print(f"  ❌ {key}: {e}")
                errors.append(key)

    print(f"\nDone — {len(uploaded)} uploaded, {len(skipped)} skipped (empty), {len(errors)} errors.")
    if skipped:
        print(f"Skipped (empty): {', '.join(skipped)}")
    if errors:
        print(f"Errors: {', '.join(errors)}")


if __name__ == "__main__":
    dry_run = "--dry-run" in sys.argv
    if dry_run:
        print(f"DRY RUN — no secrets will be created (project={PROJECT_ID})\n")
    else:
        print(f"Uploading .env to Secret Manager (project={PROJECT_ID})\n")
    upload_env_to_secret_manager(PROJECT_ID, ENV_FILE, dry_run=dry_run)
