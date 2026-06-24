#!/usr/bin/env bash
# Phase 1 — Create GCP resources for PolySaaS migration (Odoo, Mattermost, Django).
# Usage:
#   cp deploy/gcp/config.env.example deploy/gcp/config.env
#   # edit config.env with real values
#   bash deploy/gcp/setup-infrastructure.sh
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONFIG="${SCRIPT_DIR}/config.env"

if [[ ! -f "$CONFIG" ]]; then
  echo "FATAL: Missing $CONFIG — copy config.env.example first." >&2
  exit 1
fi
# shellcheck disable=SC1090
source "$CONFIG"

: "${GCP_PROJECT_ID:?GCP_PROJECT_ID required}"
: "${GCP_REGION:?GCP_REGION required}"
: "${CLOUDSQL_INSTANCE_NAME:?CLOUDSQL_INSTANCE_NAME required}"

echo "[gcp-setup] project=$GCP_PROJECT_ID region=$GCP_REGION"

gcloud config set project "$GCP_PROJECT_ID"

echo "[gcp-setup] Enabling APIs..."
gcloud services enable \
  run.googleapis.com \
  sqladmin.googleapis.com \
  cloudbuild.googleapis.com \
  artifactregistry.googleapis.com \
  secretmanager.googleapis.com \
  compute.googleapis.com \
  storage.googleapis.com \
  iam.googleapis.com

echo "[gcp-setup] Creating Artifact Registry repository (if missing)..."
gcloud artifacts repositories describe "$AR_REPOSITORY" \
  --location="$GCP_REGION" 2>/dev/null || \
gcloud artifacts repositories create "$AR_REPOSITORY" \
  --repository-format=docker \
  --location="$GCP_REGION" \
  --description="PolySaaS container images"

echo "[gcp-setup] Creating GCS buckets..."
for BUCKET in \
  "$GCS_ODOO_FILESTORE_BUCKET" \
  "$GCS_MATTERMOST_FILES_BUCKET" \
  "$GCS_DJANGO_STATIC_BUCKET" \
  "$GCS_DJANGO_MEDIA_BUCKET"; do
  if gsutil ls -b "gs://${BUCKET}" >/dev/null 2>&1; then
    echo "  bucket gs://${BUCKET} already exists"
  else
    gsutil mb -p "$GCP_PROJECT_ID" -l "$GCP_REGION" "gs://${BUCKET}"
    echo "  created gs://${BUCKET}"
  fi
done

echo "[gcp-setup] Creating bundled-app databases on Cloud SQL..."
gcloud sql databases create "$ODOO_DB_NAME" \
  --instance="$CLOUDSQL_INSTANCE_NAME" 2>/dev/null || \
  echo "  database $ODOO_DB_NAME may already exist"

gcloud sql databases create "$MATTERMOST_DB_NAME" \
  --instance="$CLOUDSQL_INSTANCE_NAME" 2>/dev/null || \
  echo "  database $MATTERMOST_DB_NAME may already exist"

echo "[gcp-setup] Creating DB users (skip if already exist)..."
if [[ -n "${ODOO_DB_PASSWORD:-}" ]]; then
  gcloud sql users create "$ODOO_DB_USER" \
    --instance="$CLOUDSQL_INSTANCE_NAME" \
    --password="$ODOO_DB_PASSWORD" 2>/dev/null || \
    gcloud sql users set-password "$ODOO_DB_USER" \
      --instance="$CLOUDSQL_INSTANCE_NAME" \
      --password="$ODOO_DB_PASSWORD"
fi

if [[ -n "${MATTERMOST_DB_PASSWORD:-}" ]]; then
  gcloud sql users create "$MATTERMOST_DB_USER" \
    --instance="$CLOUDSQL_INSTANCE_NAME" \
    --password="$MATTERMOST_DB_PASSWORD" 2>/dev/null || \
    gcloud sql users set-password "$MATTERMOST_DB_USER" \
      --instance="$CLOUDSQL_INSTANCE_NAME" \
      --password="$MATTERMOST_DB_PASSWORD"
fi

echo "[gcp-setup] Creating service account for bundled apps VM..."
SA_NAME="polysaas-bundled-apps"
SA_EMAIL="${SA_NAME}@${GCP_PROJECT_ID}.iam.gserviceaccount.com"
gcloud iam service-accounts create "$SA_NAME" \
  --display-name="PolySaaS bundled apps (Odoo/Mattermost)" 2>/dev/null || true

for BUCKET in \
  "$GCS_ODOO_FILESTORE_BUCKET" \
  "$GCS_MATTERMOST_FILES_BUCKET"; do
  gsutil iam ch "serviceAccount:${SA_EMAIL}:roles/storage.objectAdmin" "gs://${BUCKET}"
done

gcloud projects add-iam-policy-binding "$GCP_PROJECT_ID" \
  --member="serviceAccount:${SA_EMAIL}" \
  --role="roles/cloudsql.client" \
  --condition=None >/dev/null 2>&1 || true

echo "[gcp-setup] Authorizing your current IP on Cloud SQL (if needed)..."
MY_IP="$(curl -fsS https://ifconfig.me 2>/dev/null || echo "")"
if [[ -n "$MY_IP" ]]; then
  gcloud sql instances patch "$CLOUDSQL_INSTANCE_NAME" \
    --authorized-networks="${MY_IP}/32" \
    --quiet 2>/dev/null || echo "  (authorized networks patch skipped — set manually in console)"
fi

echo "[gcp-setup] Creating Cloud Run runtime service account..."
CR_SA_NAME="polysaas-cloud-run"
CR_SA_EMAIL="${CR_SA_NAME}@${GCP_PROJECT_ID}.iam.gserviceaccount.com"
gcloud iam service-accounts create "$CR_SA_NAME" \
  --display-name="PolySaaS Cloud Run" 2>/dev/null || true

for ROLE in roles/cloudsql.client roles/secretmanager.secretAccessor; do
  gcloud projects add-iam-policy-binding "$GCP_PROJECT_ID" \
    --member="serviceAccount:${CR_SA_EMAIL}" \
    --role="$ROLE" \
    --condition=None >/dev/null 2>&1 || true
done

for BUCKET in "$GCS_DJANGO_STATIC_BUCKET" "$GCS_DJANGO_MEDIA_BUCKET"; do
  gsutil iam ch "serviceAccount:${CR_SA_EMAIL}:roles/storage.objectAdmin" "gs://${BUCKET}"
done

echo ""
echo "[gcp-setup] DONE. Next steps:"
echo "  1. Store passwords in Secret Manager (see deploy/gcp/README.md)"
echo "  2. Provision Compute Engine VM: bash deploy/gcp/provision-vm.sh"
echo "  3. Deploy bundled apps: bash deploy/gcp/deploy-bundled-apps.sh"
