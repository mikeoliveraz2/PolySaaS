#!/usr/bin/env bash
# Smoke checks against production hostnames (run from laptop or VPS).
set -euo pipefail

APP_HOST="${APP_HOST:-https://app.polysaas.online}"
MM_HOST="${MM_HOST:-https://mm.polysaas.online}"
ODOO_HOST="${ODOO_HOST:-https://odoo.polysaas.online}"

fail=0
check() {
  local name="$1" url="$2"
  echo -n "CHECK $name ... "
  if curl -fsS -o /dev/null --max-time 30 "$url"; then
    echo OK
  else
    echo FAIL
    fail=1
  fi
}

check "django /health/" "$APP_HOST/health/"
check "mattermost ping" "$MM_HOST/api/v4/system/ping"
check "odoo login page" "$ODOO_HOST/web/login"

echo ""
echo "Manual checks (browser):"
echo "  1. Login $APP_HOST/accounts/login/ → /dose/home/"
echo "  2. Passthrough Odoo  $APP_HOST/pt/admin/odoo/web?ps_fullscreen=1"
echo "  3. Passthrough MM    $APP_HOST/pt/admin/mattermost/?plugin_booted=1"
echo "  4. MM post: newpolysaascontact Smoke Hostinger, smoke.host@acme.com, Acme"
echo "  5. HubSpot create contact → Odoo Contacts"

exit $fail
