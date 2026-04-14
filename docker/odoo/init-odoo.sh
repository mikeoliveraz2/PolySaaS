#!/usr/bin/env bash
set -euo pipefail

# ---------------------------------------------------------------------------
# init-odoo.sh
# Entrypoint wrapper that initialises the Odoo database on first startup
# only.  On subsequent starts the -i base flag is omitted so that Odoo does
# not attempt to reinitialise an already-populated database.
#
# Requires: psql (bundled in the odoo:18.0 image via postgresql-client)
# ---------------------------------------------------------------------------

# Fix volume ownership so Odoo can write its filestore.
mkdir -p /var/lib/odoo/filestore
chown -R odoo:odoo /var/lib/odoo

# ---------------------------------------------------------------------------
# Determine whether the database has already been initialised by checking
# for the presence of the ir_module_module table, which Odoo creates during
# its first-run base module installation.
# ---------------------------------------------------------------------------

# Read connection details from odoo.conf so we stay in sync with it.
CONF=/etc/odoo/odoo.conf

get_conf() {
    grep -E "^${1}\s*=" "${CONF}" | head -1 | sed 's/^[^=]*=\s*//' | tr -d '[:space:]'
}

DB_HOST="${DB_HOST:-$(get_conf db_host)}"
DB_PORT="${DB_PORT:-$(get_conf db_port)}"
DB_USER="${DB_USER:-$(get_conf db_user)}"
DB_NAME="${DB_NAME:-$(get_conf db_name)}"

# PGPASSWORD / DB_PASSWORD should be injected as Railway environment variables.
export PGPASSWORD="${PGPASSWORD:-${DB_PASSWORD:-}}"

echo "[init-odoo] Checking database '${DB_NAME}' on ${DB_HOST}:${DB_PORT} ..."

TABLE_EXISTS=$(
    psql \
        --host="${DB_HOST}" \
        --port="${DB_PORT}" \
        --username="${DB_USER}" \
        --dbname="${DB_NAME}" \
        --tuples-only \
        --no-align \
        --command="SELECT to_regclass('public.ir_module_module');" \
    2>/dev/null || echo ""
)

if [ -z "${TABLE_EXISTS}" ] || [ "${TABLE_EXISTS}" = "" ] || echo "${TABLE_EXISTS}" | grep -q "^$"; then
    # psql itself may have failed (db doesn't exist yet) — treat as uninitialised.
    INITIALISED=false
elif echo "${TABLE_EXISTS}" | grep -qi "ir_module_module"; then
    INITIALISED=true
else
    # to_regclass returns NULL when the table is absent.
    INITIALISED=false
fi

if [ "${INITIALISED}" = "true" ]; then
    echo "[init-odoo] Database already initialised — starting Odoo without -i base."
    exec su -s /bin/bash odoo -c \
        "odoo -c /etc/odoo/odoo.conf -d ${DB_NAME}"
else
    echo "[init-odoo] Database not yet initialised — running first-time setup with -i base."
    exec su -s /bin/bash odoo -c \
        "odoo -c /etc/odoo/odoo.conf -d ${DB_NAME} -i base"
fi
