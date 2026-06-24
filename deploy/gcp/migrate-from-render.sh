#!/usr/bin/env bash
# Phase 1.3 — Migrate Odoo and Mattermost data from Render to GCP Cloud SQL + GCS.
#
# Prerequisites:
#   - pg_dump / pg_restore installed locally
#   - gsutil installed and authenticated
#   - Render DB credentials in config.env or environment
#
# Usage:
#   bash deploy/gcp/migrate-from-render.sh [--odoo-only|--mattermost-only]
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONFIG="${SCRIPT_DIR}/config.env"
# shellcheck disable=SC1090
source "$CONFIG"

MIGRATE_ODOO=1
MIGRATE_MM=1
for arg in "$@"; do
  case "$arg" in
    --odoo-only) MIGRATE_MM=0 ;;
    --mattermost-only) MIGRATE_ODOO=0 ;;
  esac
done

WORKDIR="${TMPDIR:-/tmp}/polysaas-gcp-migrate"
mkdir -p "$WORKDIR"

migrate_db() {
  local label="$1" src_host="$2" src_port="$3" src_user="$4" src_pass="$5" src_db="$6"
  local dst_host="$7" dst_port="$8" dst_user="$9" dst_pass="${10}" dst_db="${11}"
  local dump_file="$WORKDIR/${label}.dump"

  echo "[migrate] $label: dumping $src_db from Render..."
  PGPASSWORD="$src_pass" pg_dump \
    -h "$src_host" -p "$src_port" -U "$src_user" -d "$src_db" \
    -Fc -f "$dump_file"

  echo "[migrate] $label: restoring to Cloud SQL $dst_db..."
  PGPASSWORD="$dst_pass" pg_restore \
    -h "$dst_host" -p "$dst_port" -U "$dst_user" -d "$dst_db" \
    --no-owner --no-acl --clean --if-exists \
    "$dump_file" || true

  echo "[migrate] $label: done ($dump_file)"
}

if [[ "$MIGRATE_ODOO" -eq 1 ]]; then
  : "${RENDER_ODOO_DB_HOST:?RENDER_ODOO_DB_HOST required for Odoo migration}"
  : "${RENDER_ODOO_DB_USER:?}"
  : "${RENDER_ODOO_DB_PASSWORD:?}"
  : "${ODOO_DB_PASSWORD:?}"
  migrate_db "odoo" \
    "$RENDER_ODOO_DB_HOST" "${RENDER_ODOO_DB_PORT:-5432}" \
    "$RENDER_ODOO_DB_USER" "$RENDER_ODOO_DB_PASSWORD" "$RENDER_ODOO_DB_NAME" \
    "$CLOUDSQL_HOST" "$CLOUDSQL_PORT" \
    "$ODOO_DB_USER" "$ODOO_DB_PASSWORD" "$ODOO_DB_NAME"
fi

if [[ "$MIGRATE_MM" -eq 1 ]]; then
  : "${RENDER_MM_DB_HOST:?RENDER_MM_DB_HOST required for Mattermost migration}"
  : "${RENDER_MM_DB_USER:?}"
  : "${RENDER_MM_DB_PASSWORD:?}"
  : "${MATTERMOST_DB_PASSWORD:?}"
  migrate_db "mattermost" \
    "$RENDER_MM_DB_HOST" "${RENDER_MM_DB_PORT:-5432}" \
    "$RENDER_MM_DB_USER" "$RENDER_MM_DB_PASSWORD" "$RENDER_MM_DB_NAME" \
    "$CLOUDSQL_HOST" "$CLOUDSQL_PORT" \
    "$MATTERMOST_DB_USER" "$MATTERMOST_DB_PASSWORD" "$MATTERMOST_DB_NAME"
fi

echo "[migrate] File migration (optional — run manually if you have Render disk exports):"
echo "  gsutil -m rsync -r ./odoo-filestore-export gs://${GCS_ODOO_FILESTORE_BUCKET}/"
echo "  gsutil -m rsync -r ./mattermost-data-export gs://${GCS_MATTERMOST_FILES_BUCKET}/"
echo "[migrate] DONE."
