#!/usr/bin/env bash
# Deploy Odoo + Mattermost docker-compose stack to the GCE VM.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONFIG="${SCRIPT_DIR}/config.env"
# shellcheck disable=SC1090
source "$CONFIG"

: "${GCP_PROJECT_ID:?}"
: "${GCP_ZONE:?}"
: "${GCE_VM_NAME:?}"

REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
COMPOSE_FILE="$SCRIPT_DIR/docker-compose.gcp.yml"

echo "[deploy-bundled] Syncing deploy/gcp to VM..."
gcloud compute scp --recurse \
  "$SCRIPT_DIR" \
  "$GCE_VM_NAME:/opt/polysaas/deploy-gcp" \
  --zone="$GCP_ZONE"

gcloud compute scp --recurse \
  "$REPO_ROOT/deploy/odoo" \
  "$REPO_ROOT/deploy/mattermost" \
  "$GCE_VM_NAME:/opt/polysaas/" \
  --zone="$GCP_ZONE"

echo "[deploy-bundled] Building and starting containers..."
gcloud compute ssh "$GCE_VM_NAME" --zone="$GCP_ZONE" --command="
  set -e
  sudo mkdir -p /opt/polysaas /mnt/gcs/odoo-filestore
  sudo cp -f /opt/polysaas/deploy-gcp/config.env /opt/polysaas/config.env 2>/dev/null || true
  cd /opt/polysaas
  sudo docker compose -f deploy-gcp/docker-compose.gcp.yml --env-file config.env build
  sudo docker compose -f deploy-gcp/docker-compose.gcp.yml --env-file config.env up -d
  sudo docker compose -f deploy-gcp/docker-compose.gcp.yml ps
"

echo "[deploy-bundled] External IP (point DNS or test locally):"
gcloud compute instances describe "$GCE_VM_NAME" \
  --zone="$GCP_ZONE" \
  --format='get(networkInterfaces[0].accessConfigs[0].natIP)'
