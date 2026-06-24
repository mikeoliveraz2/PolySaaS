#!/usr/bin/env bash
# Bootstrap Secret Manager secrets required by cloudbuild.yaml / Cloud Run.
# Run once after setup-infrastructure.sh. Prompts are avoided — pass via env or edit.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONFIG="${SCRIPT_DIR}/config.env"
# shellcheck disable=SC1090
source "$CONFIG"

: "${GCP_PROJECT_ID:?}"

gcloud config set project "$GCP_PROJECT_ID"

create_secret() {
  local name="$1" value="$2"
  if gcloud secrets describe "$name" >/dev/null 2>&1; then
    echo "[secrets] $name exists — add new version if rotating"
    echo -n "$value" | gcloud secrets versions add "$name" --data-file=- 2>/dev/null || true
  else
    echo -n "$value" | gcloud secrets create "$name" --data-file=-
    echo "[secrets] created $name"
  fi
}

: "${DJANGO_SECRET_KEY:?Set DJANGO_SECRET_KEY in environment or config.env}"
: "${DOSE_DB_PASSWORD:?Set DOSE_DB_PASSWORD in environment or config.env}"

create_secret "django-secret-key" "$DJANGO_SECRET_KEY"
create_secret "dose-db-password" "$DOSE_DB_PASSWORD"

echo "[secrets] DONE. Cloud Run and Cloud Build can reference these secrets."
