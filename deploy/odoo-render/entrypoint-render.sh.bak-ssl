#!/usr/bin/env bash
# Render sets PORT to the HTTP listener (e.g. 10000). Odoo's /entrypoint.sh reuses the name PORT
# for Postgres — unreliable on Render. We skip /entrypoint.sh for DB checks and run odoo with
# explicit --http-port / --db_* / -d.
#
# IMPORTANT: Do not read plain "USER" first — POSIX shells set USER to the login name (often
# "odoo" in this image), which is wrong for Postgres unless you explicitly meant that role.
set -euo pipefail

HOST_VAL="${HOST:-${ODOO_DB_HOST:-${PGHOST:-}}}"
if [ -z "${HOST_VAL}" ]; then
  echo "FATAL: Set HOST or ODOO_DB_HOST (Postgres hostname only from Connections / internal DNS), not a postgresql:// URL." >&2
  exit 1
fi
export HOST="$HOST_VAL"

RENDER_HTTP_PORT="${PORT:-8069}"

RUNTIME_LOGIN="$(id -un)"
# Prefer explicit DB role names (Render / polysaas-odoo env group uses ODOO_DB_USER).
USER_VAL="${ODOO_DB_USER:-${DB_USER:-${PGUSER:-${POSTGRES_USER:-}}}}"
if [ -z "${USER_VAL}" ] && [ -n "${USER:-}" ]; then
  if [ "${USER}" != "${RUNTIME_LOGIN}" ] || [ -n "${USE_ENV_USER_FOR_POSTGRES:-}" ]; then
    USER_VAL="${USER}"
  fi
fi
if [ -z "${USER_VAL}" ]; then
  echo "FATAL: Set ODOO_DB_USER or DB_USER (recommended). Plain USER is ignored when it equals login '${RUNTIME_LOGIN}' (POSIX collision). Set USE_ENV_USER_FOR_POSTGRES=1 if your Postgres role is literally that name." >&2
  exit 1
fi

DB_PASS="${PGPASSWORD:-${PASSWORD:-${ODOO_DB_PASSWORD:-${ODOO_PASSWORD:-}}}}"
if [ -z "${DB_PASS}" ]; then
  echo "FATAL: Set PASSWORD or ODOO_DB_PASSWORD (or PGPASSWORD) to that role's password." >&2
  exit 1
fi

DBN_VAL="${DB_NAME:-${ODOO_DB_NAME:-postgres}}"

export HOST USER="${USER_VAL}" PASSWORD="${DB_PASS}"
export PGHOST="${HOST}" PGPORT=5432 PGUSER="${USER_VAL}" PGPASSWORD="${DB_PASS}" PGDATABASE="${DBN_VAL}"

# Sanitized config for Odoo runtime (no db_* lines so nothing can override CLI DB settings).
ODOO_BASE="${ODOO_RC:-/etc/odoo/odoo.conf}"
TMP_RC="/tmp/odoo-render-odoorc.conf"
if [ -r "$ODOO_BASE" ]; then
  umask 077
  grep -Ev '^[[:space:]]*(db_port|db_host|db_user|db_password)[[:space:]]*=' "$ODOO_BASE" >"$TMP_RC" || true
  if [ ! -s "$TMP_RC" ]; then
    echo "[entrypoint-render] WARNING: stripped odoo.conf empty; using minimal [options] only." >&2
    printf '%s\n' '[options]' >"$TMP_RC"
  fi
  chmod 600 "$TMP_RC" 2>/dev/null || true
  export ODOO_RC="$TMP_RC"
else
  echo "[entrypoint-render] WARNING: cannot read ODOO_RC base at $ODOO_BASE; using defaults." >&2
fi

echo "[entrypoint-render] waiting for Postgres ${HOST}:5432 dbname=${DBN_VAL} (PGSSLMODE=${PGSSLMODE:-prefer})..." >&2
n=0
while [ "$n" -lt 60 ]; do
  if PGPASSWORD="$DB_PASS" PGSSLMODE="${PGSSLMODE:-prefer}" \
    psql -h "$HOST" -p 5432 -U "$USER_VAL" -d "$DBN_VAL" -c 'select 1' >/dev/null 2>&1; then
    echo "[entrypoint-render] Postgres is reachable." >&2
    break
  fi
  n=$((n + 1))
  if [ "$n" -eq 60 ]; then
    echo "[entrypoint-render] FATAL: could not connect after 60 attempts. Check HOST, ODOO_DB_USER, PASSWORD, DB_NAME, and PGSSLMODE (try PGSSLMODE=require for Render external Postgres)." >&2
    exit 1
  fi
  sleep 2
done

echo "[entrypoint-render] starting odoo http_port=${RENDER_HTTP_PORT} db=${HOST}:5432 dbname=${DBN_VAL}" >&2

# Drop inherited Render PORT before starting Odoo so nothing in the stack misreads it as DB.
unset PORT 2>/dev/null || true

if [ "${1:-}" = "odoo" ]; then
  shift
fi

exec odoo \
  --http-port="${RENDER_HTTP_PORT}" \
  --proxy-mode \
  --db_host="$HOST" \
  --db_port=5432 \
  --db_user="$USER_VAL" \
  --db_password="$DB_PASS" \
  -d "$DBN_VAL" \
  "$@"
