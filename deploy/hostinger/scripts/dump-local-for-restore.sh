#!/usr/bin/env bash
# Dump local DBs for Hostinger restore (run on laptop / office machine).
# Requires: docker (local compose) or pg_dump against localhost ports.
set -euo pipefail

OUT_DIR="${1:-deploy/hostinger/restore}"
mkdir -p "$OUT_DIR"

echo "==> Dumping core Postgres (container polysaas-local-core-postgres if present)"
if docker ps --format '{{.Names}}' | grep -q '^polysaas-local-core-postgres$'; then
  docker exec polysaas-local-core-postgres pg_dump -U "${DB_USER:-dosedbadmin}" -d "${DB_NAME:-dosedbsaas}" \
    | gzip -c > "$OUT_DIR/core.sql.gz"
  echo "Wrote $OUT_DIR/core.sql.gz"
else
  echo "WARN: core postgres container not running — dump manually"
fi

if docker ps --format '{{.Names}}' | grep -q '^polysaas-local-odoo-db$'; then
  docker exec polysaas-local-odoo-db pg_dump -U "${ODOO_DB_USER:-odoo}" -d "${ODOO_SHARED_DB:-polysaas_odoo}" \
    | gzip -c > "$OUT_DIR/odoo.sql.gz"
  echo "Wrote $OUT_DIR/odoo.sql.gz"
else
  echo "WARN: odoo-db container not running — skip or dump manually"
fi

if docker ps --format '{{.Names}}' | grep -q '^polysaas-local-mattermost-db$'; then
  docker exec polysaas-local-mattermost-db pg_dump -U "${MATTERMOST_DB_USER:-mattermost}" -d "${MATTERMOST_DB_NAME:-mattermost}" \
    | gzip -c > "$OUT_DIR/mattermost.sql.gz"
  echo "Wrote $OUT_DIR/mattermost.sql.gz"
else
  echo "WARN: mattermost-db container not running — skip or dump manually"
fi

echo ""
echo "Copy to Hostinger VPS:"
echo "  scp $OUT_DIR/*.sql.gz root@<VPS_IP>:/opt/polysaas/deploy/hostinger/restore/"
echo "Then on VPS: bash deploy/hostinger/scripts/migrate-data.sh"
