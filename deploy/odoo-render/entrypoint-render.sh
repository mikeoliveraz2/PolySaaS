#!/usr/bin/env bash
# First stderr line: if deploy logs never show this, the kernel did not run this script (shebang/CRLF,
# wrong entrypoint, or Render start command bypassing the image ENTRYPOINT). See README.txt.
echo "[entrypoint-render] boot line1 pid=$$ 0=$0" >&2
# This file must use LF line endings only (CRLF breaks the shebang on Linux / Render).
# Render sets PORT to the HTTP listener (e.g. 10000). Odoo's /entrypoint.sh reuses the name PORT
# for Postgres — unreliable on Render. We skip /entrypoint.sh for DB checks and run odoo with
# explicit --http-port / --db_* / -d.
#
# Naming (PolySaaS convention): prefer ODOO_DB_* from Render / polysaas-odoo. Legacy HOST, PASSWORD,
# DB_NAME, USER still accepted for one-off migration — see deploy/odoo-render/README.txt.
set -euo pipefail

# --- Postgres host (internal DNS only, never postgresql://) ---
HOST_VAL="${ODOO_DB_HOST:-${PGHOST:-${HOST:-}}}"
if [ -z "${HOST_VAL}" ]; then
  _eodb="${ODOO_DB_HOST:-}"
  _pgh="${PGHOST:-}"
  _hst="${HOST:-}"
  echo "[entrypoint-render] debug: ODOO_DB_HOST_empty=$([ -z "${_eodb}" ] && echo yes || echo no) PGHOST_empty=$([ -z "${_pgh}" ] && echo yes || echo no) HOST_empty=$([ -z "${_hst}" ] && echo yes || echo no)" >&2
  echo "FATAL: Set ODOO_DB_HOST (required) to the Postgres internal hostname. Legacy: PGHOST or HOST. Not a postgresql:// URL." >&2
  exit 1
fi
export HOST="$HOST_VAL"

RENDER_HTTP_PORT="${PORT:-8069}"

RUNTIME_LOGIN="$(id -un)"
USER_VAL="${ODOO_DB_USER:-${DB_USER:-${PGUSER:-${POSTGRES_USER:-}}}}"
if [ -z "${USER_VAL}" ] && [ -n "${USER:-}" ]; then
  if [ "${USER}" != "${RUNTIME_LOGIN}" ] || [ -n "${USE_ENV_USER_FOR_POSTGRES:-}" ]; then
    USER_VAL="${USER}"
  fi
fi
if [ -z "${USER_VAL}" ]; then
  echo "FATAL: Set ODOO_DB_USER (required). Legacy: DB_USER / PGUSER, or USER if not POSIX login '${RUNTIME_LOGIN}'." >&2
  exit 1
fi

# Prefer ODOO_DB_PASSWORD (canonical); legacy PGPASSWORD, PASSWORD
DB_PASS="${ODOO_DB_PASSWORD:-${PGPASSWORD:-${PASSWORD:-${ODOO_PASSWORD:-}}}}"
if [ -z "${DB_PASS}" ]; then
  echo "FATAL: Set ODOO_DB_PASSWORD (required) to the Postgres role password. Legacy: PGPASSWORD or PASSWORD." >&2
  exit 1
fi

DBN_VAL="${ODOO_DB_NAME:-${DB_NAME:-postgres}}"
DB_PORT="${ODOO_DB_PORT:-5432}"

export HOST USER="${USER_VAL}" PASSWORD="${DB_PASS}"
export PGHOST="${HOST}" PGPORT="${DB_PORT}" PGUSER="${USER_VAL}" PGPASSWORD="${DB_PASS}" PGDATABASE="${DBN_VAL}"

if [ -z "${PGSSLMODE:-}" ]; then
  case "$HOST" in
    dpg-*)
      export PGSSLMODE=require
      ;;
    *)
      export PGSSLMODE=prefer
      ;;
  esac
fi

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

echo "[entrypoint-render] waiting for Postgres ${HOST}:${DB_PORT} dbname=${DBN_VAL} PGSSLMODE=${PGSSLMODE}..." >&2
n=0
while [ "$n" -lt 60 ]; do
  if PGPASSWORD="$DB_PASS" PGSSLMODE="${PGSSLMODE}" \
    psql -h "$HOST" -p "$DB_PORT" -U "$USER_VAL" -d "$DBN_VAL" -c 'select 1' >/dev/null 2>&1; then
    echo "[entrypoint-render] Postgres is reachable." >&2
    break
  fi
  n=$((n + 1))
  if [ "$n" -eq 60 ]; then
    echo "[entrypoint-render] diagnostic (last psql attempt):" >&2
    PGPASSWORD="$DB_PASS" PGSSLMODE="${PGSSLMODE}" \
      psql -h "$HOST" -p "$DB_PORT" -U "$USER_VAL" -d "$DBN_VAL" -c 'select 1' 2>&1 | tail -n 8 >&2 || true
    echo "[entrypoint-render] FATAL: could not connect after 60 attempts. Check ODOO_DB_HOST, ODOO_DB_USER, ODOO_DB_PASSWORD, ODOO_DB_NAME=${DBN_VAL}, ODOO_DB_PORT=${DB_PORT}, PGSSLMODE." >&2
    exit 1
  fi
  sleep 2
done

echo "[entrypoint-render] starting odoo http_port=${RENDER_HTTP_PORT} db=${HOST}:${DB_PORT} dbname=${DBN_VAL}" >&2

unset PORT 2>/dev/null || true

# Optional bootstrap when Render Shell is unavailable: if ODOO_AUTO_INIT is set and the DB has no
# Odoo core table yet, run one install pass then continue to normal exec. Remove ODOO_AUTO_INIT from
# the service after the first good deploy (avoids an extra psql probe every boot).
_invoke_odoo() {
  odoo \
    --http-port="${RENDER_HTTP_PORT}" \
    --proxy-mode \
    --db_host="$HOST" \
    --db_port="${DB_PORT}" \
    --db_user="$USER_VAL" \
    --db_password="$DB_PASS" \
    -d "$DBN_VAL" \
    "$@"
}

if [ "${ODOO_AUTO_INIT:-0}" = "1" ] || [ "${ODOO_AUTO_INIT:-}" = "true" ] || [ "${ODOO_AUTO_INIT:-}" = "yes" ]; then
  # Check if web module is actually installed (not just if table exists)
  WEB_INSTALLED="$(
    PGPASSWORD="$DB_PASS" PGSSLMODE="${PGSSLMODE}" \
      psql -h "$HOST" -p "$DB_PORT" -U "$USER_VAL" -d "$DBN_VAL" -tAc \
      "SELECT state FROM ir_module_module WHERE name = 'web' LIMIT 1;" 2>/dev/null || echo ""
  )"
  WEB_INSTALLED="$(printf '%s' "${WEB_INSTALLED}" | tr -d '[:space:]')"
  if [ "${WEB_INSTALLED}" = "installed" ]; then
    echo "[entrypoint-render] ODOO_AUTO_INIT: web module already installed; skipping -i." >&2
  else
    echo "[entrypoint-render] ODOO_AUTO_INIT: web module not installed (state='${WEB_INSTALLED}'); installing base,web --stop-after-init..." >&2
    _invoke_odoo -i base,web --stop-after-init
    echo "[entrypoint-render] ODOO_AUTO_INIT: install step finished." >&2
  fi
fi

if [ "${1:-}" = "odoo" ]; then
  shift
fi

exec odoo \
  --http-port="${RENDER_HTTP_PORT}" \
  --proxy-mode \
  --db_host="$HOST" \
  --db_port="${DB_PORT}" \
  --db_user="$USER_VAL" \
  --db_password="$DB_PASS" \
  -d "$DBN_VAL" \
  "$@"
