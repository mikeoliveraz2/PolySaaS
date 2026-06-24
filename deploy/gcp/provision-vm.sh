#!/usr/bin/env bash
# Create Compute Engine VM for Odoo + Mattermost docker-compose stack.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONFIG="${SCRIPT_DIR}/config.env"
# shellcheck disable=SC1090
source "$CONFIG"

: "${GCP_PROJECT_ID:?}"
: "${GCP_ZONE:?}"
: "${GCE_VM_NAME:?}"
: "${GCE_MACHINE_TYPE:?}"

SA_EMAIL="polysaas-bundled-apps@${GCP_PROJECT_ID}.iam.gserviceaccount.com"
STARTUP_SCRIPT="${SCRIPT_DIR}/vm-startup.sh"

gcloud config set project "$GCP_PROJECT_ID"

if gcloud compute instances describe "$GCE_VM_NAME" --zone="$GCP_ZONE" >/dev/null 2>&1; then
  echo "[provision-vm] VM $GCE_VM_NAME already exists in $GCP_ZONE"
  exit 0
fi

gcloud compute instances create "$GCE_VM_NAME" \
  --zone="$GCP_ZONE" \
  --machine-type="$GCE_MACHINE_TYPE" \
  --boot-disk-size="${GCE_DISK_SIZE_GB:-50}GB" \
  --image-family=debian-12 \
  --image-project=debian-cloud \
  --tags=polysaas-bundled-apps \
  --service-account="$SA_EMAIL" \
  --scopes=cloud-platform \
  --metadata-from-file=startup-script="$STARTUP_SCRIPT"

echo "[provision-vm] VM created. Allow HTTP/HTTPS:"
gcloud compute firewall-rules create polysaas-bundled-apps-http \
  --allow=tcp:8065,tcp:8069,tcp:80,tcp:443 \
  --target-tags=polysaas-bundled-apps \
  --description="Odoo and Mattermost" 2>/dev/null || true

echo "[provision-vm] External IP:"
gcloud compute instances describe "$GCE_VM_NAME" \
  --zone="$GCP_ZONE" \
  --format='get(networkInterfaces[0].accessConfigs[0].natIP)'
