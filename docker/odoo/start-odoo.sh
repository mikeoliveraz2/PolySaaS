#!/usr/bin/env bash
set -euo pipefail

# Railway volume is often mounted as root-owned; fix ownership for Odoo filestore writes.
mkdir -p /var/lib/odoo/filestore
chown -R odoo:odoo /var/lib/odoo

first_non_empty() {
	for value in "$@"; do
		if [ -n "$value" ]; then
			printf '%s' "$value"
			return 0
		fi
	done
	return 1
}

DB_NAME="$(first_non_empty "${DB_NAME:-}" "${PGDATABASE:-}" "${POSTGRES_DB:-}" "${POSTGRES_DATABASE:-}" "${ODOO_DATABASE_NAME:-}" "odoo")"
DB_HOST="$(first_non_empty "${DB_HOST:-}" "${PGHOST:-}" "${POSTGRES_HOST:-}" "${ODOO_DATABASE_HOST:-}" "postgres.railway.internal")"
DB_PORT="$(first_non_empty "${DB_PORT:-}" "${PGPORT:-}" "${POSTGRES_PORT:-}" "${ODOO_DATABASE_PORT_NUMBER:-}" "5432")"
DB_USER="$(first_non_empty "${DB_USER:-}" "${PGUSER:-}" "${POSTGRES_USER:-}" "${ODOO_DATABASE_USER:-}" "odoo")"
DB_PASSWORD="$(first_non_empty "${DB_PASSWORD:-}" "${PGPASSWORD:-}" "${POSTGRES_PASSWORD:-}" "${ODOO_DATABASE_PASSWORD:-}" "")"

RUNTIME_CONF=/tmp/odoo-runtime.conf

export DB_NAME
export DB_HOST
export DB_PORT
export DB_USER
export DB_PASSWORD
export PGHOST="$DB_HOST"
export PGPORT="$DB_PORT"
export PGUSER="$DB_USER"
export PGPASSWORD="$DB_PASSWORD"

cp /etc/odoo/odoo.conf "$RUNTIME_CONF"
sed -i \
	-e "s#^db_host *=.*#db_host = $DB_HOST#" \
	-e "s#^db_port *=.*#db_port = $DB_PORT#" \
	-e "s#^db_user *=.*#db_user = $DB_USER#" \
	-e "s#^db_name *=.*#db_name = $DB_NAME#" \
	"$RUNTIME_CONF"

if grep -q '^db_password *=.*' "$RUNTIME_CONF"; then
	sed -i -e "s#^db_password *=.*#db_password = $DB_PASSWORD#" "$RUNTIME_CONF"
else
	printf '\ndb_password = %s\n' "$DB_PASSWORD" >> "$RUNTIME_CONF"
fi

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
		su -s /bin/bash odoo -c "/entrypoint.sh odoo -c '$RUNTIME_CONF' -d '$DB_NAME' -i base --without-demo=all --stop-after-init"
	else
		echo "Database check failed with code $rc; refusing to continue." >&2
		exit "$rc"
	fi
fi

exec su -s /bin/bash odoo -c "/entrypoint.sh odoo -c '$RUNTIME_CONF' -d '$DB_NAME'"
