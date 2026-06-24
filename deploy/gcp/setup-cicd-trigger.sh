#!/usr/bin/env bash
# Phase 4 — Create Cloud Build trigger for main branch → Cloud Run deploy.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONFIG="${SCRIPT_DIR}/config.env"
# shellcheck disable=SC1090
source "$CONFIG"

: "${GCP_PROJECT_ID:?}"
: "${CLOUDSQL_CONNECTION_NAME:?}"
: "${AR_HOST:?}"
: "${CLOUD_RUN_SERVICE:?}"
: "${CLOUD_RUN_IMAGE:?}"

REPO_OWNER="${GITHUB_REPO_OWNER:-mikeoliveraz2}"
REPO_NAME="${GITHUB_REPO_NAME:-PolySaaS}"

gcloud config set project "$GCP_PROJECT_ID"

echo "[setup-cicd] Creating Cloud Build trigger (requires GitHub App connection)..."
gcloud builds triggers create github \
  --name="polysaas-main-deploy" \
  --repo-owner="$REPO_OWNER" \
  --repo-name="$REPO_NAME" \
  --branch-pattern='^main$' \
  --build-config=cloudbuild.yaml \
  --substitutions="_AR_HOST=${AR_HOST},_IMAGE=${CLOUD_RUN_IMAGE},_REGION=${GCP_REGION},_SERVICE=${CLOUD_RUN_SERVICE},_CLOUDSQL=${CLOUDSQL_CONNECTION_NAME}" \
  2>/dev/null || \
  echo "[setup-cicd] Trigger may already exist — update in GCP Console if needed."

echo "[setup-cicd] Grant Cloud Build SA permissions..."
PROJECT_NUMBER="$(gcloud projects describe "$GCP_PROJECT_ID" --format='value(projectNumber)')"
CB_SA="${PROJECT_NUMBER}@cloudbuild.gserviceaccount.com"

for ROLE in roles/run.admin roles/iam.serviceAccountUser roles/secretmanager.secretAccessor roles/cloudsql.client; do
  gcloud projects add-iam-policy-binding "$GCP_PROJECT_ID" \
    --member="serviceAccount:${CB_SA}" \
    --role="$ROLE" \
    --condition=None >/dev/null 2>&1 || true
done

echo "[setup-cicd] DONE. Push to main to trigger deploy, or run:"
echo "  gcloud builds submit --config=cloudbuild.yaml ."
