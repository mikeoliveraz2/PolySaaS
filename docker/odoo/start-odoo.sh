#!/usr/bin/env bash
set -euo pipefail

# Railway volume is often mounted as root-owned; fix ownership for Odoo filestore writes.
mkdir -p /var/lib/odoo/filestore
chown -R odoo:odoo /var/lib/odoo

DB_NAME="${DB_NAME:-${PGDATABASE:-odoo}}"
DB_HOST="${DB_HOST:-${PGHOST:-postgres.railway.internal}}"
DB_PORT="${DB_PORT:-${PGPORT:-5432}}"
DB_USER="${DB_USER:-${PGUSER:-odoo}}"
DB_PASSWORD="${DB_PASSWORD:-${PGPASSWORD:-}}"

export DB_NAME
export DB_HOST
export DB_PORT
export DB_USER
export DB_PASSWORD
export PGHOST="$DB_HOST"
export PGPORT="$DB_PORT"
export PGUSER="$DB_USER"
export PGPASSWORD="$DB_PASSWORD"

db_exists() {
	python3 - <<'PY'
import os
import sys

import psycopg2

params = {
	"dbname": os.environ.get("DB_NAME", "odoo"),
	"user": os.environ.get("DB_USER", "odoo"),
	"password": os.environ.get("DB_PASSWORD", ""),
	"host": os.environ.get("DB_HOST", "postgres.railway.internal"),
	"port": int(os.environ.get("DB_PORT", "5432")),
	"connect_timeout": 5,
}

try:
	conn = psycopg2.connect(**params)
	conn.close()
except psycopg2.OperationalError as exc:
	# 3D000 = invalid_catalog_name (database does not exist)
	if getattr(exc, "pgcode", None) == "3D000" or "does not exist" in str(exc).lower():
		sys.exit(10)
	print(f"Database connectivity check failed: {exc}", file=sys.stderr)
	sys.exit(20)

sys.exit(0)
PY
}

if db_exists; then
	echo "Database '$DB_NAME' exists; starting Odoo normally."
else
	rc=$?
	if [ "$rc" -eq 10 ]; then
		echo "Database '$DB_NAME' not found; running one-time base initialization."
		su -s /bin/bash odoo -c "/entrypoint.sh odoo -c /etc/odoo/odoo.conf -d '$DB_NAME' -i base --without-demo=all --stop-after-init"
	else
		echo "Database check failed with code $rc; refusing to continue." >&2
		exit "$rc"
	fi
fi

exec su -s /bin/bash odoo -c "/entrypoint.sh odoo -c /etc/odoo/odoo.conf -d '$DB_NAME'"
