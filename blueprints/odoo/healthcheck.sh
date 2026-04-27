#!/usr/bin/env bash
set -euo pipefail

ODOO_PORT="${ODOO_PORT:-${PORT:-8069}}"

curl -fsS "http://127.0.0.1:${ODOO_PORT}/web/login" >/dev/null
