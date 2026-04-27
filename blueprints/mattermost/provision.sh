#!/usr/bin/env bash
set -euo pipefail

# polysaas_provision_contract=v1

if [ -f .env ]; then
  set -a
  . ./.env
  set +a
fi

: "${TENANT_SLUG:?TENANT_SLUG is required}"

APP_SLUG="mattermost"
actions=()

log() { echo "[provision] $*" 1>&2; }

register_oauth2_app_for_tenant() {
  actions+=("oauth_register_stub")
  return 0
}

register_oauth2_app_for_tenant

log "app=${APP_SLUG} tenant=${TENANT_SLUG}"
log "hook: configure SSO / OIDC in Mattermost (TODO)"

actions_json=""
for a in "${actions[@]}"; do
  if [ -z "$actions_json" ]; then
    actions_json="\"$a\""
  else
    actions_json="$actions_json,\"$a\""
  fi
done

echo "{\"app\":\"${APP_SLUG}\",\"tenant_slug\":\"${TENANT_SLUG}\",\"status\":\"ok\",\"actions\":[${actions_json}]}"
