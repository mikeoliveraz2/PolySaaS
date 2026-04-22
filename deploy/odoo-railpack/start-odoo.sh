#!/usr/bin/env bash
set -euo pipefail

DB_HOST="${ODOO_DB_HOST:-${DB_HOST:-${PGHOST:-postgres}}}"
DB_PORT="${ODOO_DB_PORT:-${DB_PORT:-${PGPORT:-5432}}}"
DB_USER="${ODOO_DB_USER:-${DB_USER:-${PGUSER:-odoo}}}"
DB_PASSWORD="${ODOO_DB_PASSWORD:-${DB_PASSWORD:-${PGPASSWORD:-odoo}}}"
DB_NAME="${ODOO_DB_NAME:-${DB_NAME:-${PGDATABASE:-database1}}}"
HTTP_PORT="${PORT:-8069}"
MASTER_PASSWORD="${ODOO_MASTER_PASSWORD:-admin}"

echo "Starting Odoo with db=${DB_NAME} host=${DB_HOST} port=${DB_PORT} user=${DB_USER}"

exec /opt/venv/bin/odoo \
  -c ./odoo.conf \
  --db_host "${DB_HOST}" \
  --db_port "${DB_PORT}" \
  --db_user "${DB_USER}" \
  --db_password "${DB_PASSWORD}" \
  -d "${DB_NAME}" \
  --admin-passwd "${MASTER_PASSWORD}" \
  --http-port "${HTTP_PORT}"
