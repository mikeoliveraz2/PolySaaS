#!/usr/bin/env bash
# Phase 3 — Manual first deploy of PolySaaS Django to Cloud Run.
# After this works, use cloudbuild.yaml for CI/CD.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONFIG="${SCRIPT_DIR}/config.env"
# shellcheck disable=SC1090
source "$CONFIG"

: "${GCP_PROJECT_ID:?}"
: "${GCP_REGION:?}"
: "${CLOUDSQL_CONNECTION_NAME:?}"
: "${AR_HOST:?}"
: "${CLOUD_RUN_SERVICE:?}"
: "${CLOUD_RUN_IMAGE:?}"

REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
IMAGE="${AR_HOST}/${CLOUD_RUN_IMAGE}:latest"

gcloud config set project "$GCP_PROJECT_ID"

echo "[deploy-cloud-run] Building image..."
gcloud builds submit "$REPO_ROOT" \
  --config="$REPO_ROOT/cloudbuild.yaml" \
  --substitutions="_AR_HOST=${AR_HOST},_IMAGE=${CLOUD_RUN_IMAGE},_TAG=manual,_REGION=${GCP_REGION},_SERVICE=${CLOUD_RUN_SERVICE},_CLOUDSQL=${CLOUDSQL_CONNECTION_NAME}"

echo "[deploy-cloud-run] Service URL:"
gcloud run services describe "$CLOUD_RUN_SERVICE" \
  --region="$GCP_REGION" \
  --format='value(status.url)'
