#!/usr/bin/env bash
# Restore dumps into running Hostinger stack volumes (run on VPS).
# Place dumps first:
#   /opt/polysaas/deploy/hostinger/restore/core.sql.gz
#   /opt/polysaas/deploy/hostinger/restore/odoo.sql.gz   (optional)
#   /opt/polysaas/deploy/hostinger/restore/mattermost.sql.gz (optional)
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
HOST_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
ENV_FILE="$HOST_DIR/.env"
RESTORE_DIR="$HOST_DIR/restore"
COMPOSE=(docker compose -f "$HOST_DIR/docker-compose.yml" --env-file "$ENV_FILE")

set -a
# shellcheck disable=SC1090
source "$ENV_FILE"
set +a

mkdir -p "$RESTORE_DIR"

restore_pg() {
  local service="$1"
  local user="$2"
  local db="$3"
  local dump="$4"
  if [[ ! -f "$dump" ]]; then
    echo "Skip $service — missing $dump"
    return 0
  fi
  echo "==> Restoring $dump → $service/$db"
  if [[ "$dump" == *.gz ]]; then
    gunzip -c "$dump" | "${COMPOSE[@]}" exec -T "$service" psql -U "$user" -d "$db"
  else
    cat "$dump" | "${COMPOSE[@]}" exec -T "$service" psql -U "$user" -d "$db"
  fi
}

echo "Stopping consumers that may write during restore"
"${COMPOSE[@]}" stop mailbox-consumer django || true

restore_pg core-postgres "${DB_USER:-dosedbadmin}" "${DB_NAME:-dosedbsaas}" "$RESTORE_DIR/core.sql.gz"
restore_pg odoo-db "${ODOO_DB_USER:-odoo}" "${ODOO_DB_NAME:-polysaas_odoo}" "$RESTORE_DIR/odoo.sql.gz"
restore_pg mattermost-db "${MATTERMOST_DB_USER:-mattermost}" "${MATTERMOST_DB_NAME:-mattermost}" "$RESTORE_DIR/mattermost.sql.gz"

echo "==> Restarting app services"
"${COMPOSE[@]}" start django mailbox-consumer
"${COMPOSE[@]}" up -d

cat <<'EOF'

After restore, retarget PassThroughEndpoint / TenantApp URLs in Django:

  Mattermost endpoint_url → http://mattermost:8065   (server-side) or https://mm.prod-polysaas.cloud
  Odoo endpoint_url       → http://odoo:8069         (server-side) or https://odoo.prod-polysaas.cloud

Update external webhooks:
  HubSpot FlowLink → https://app.prod-polysaas.cloud/dose/webhook/hubspot/polysaasonline/
  Slack Events     → https://app.prod-polysaas.cloud/hooks/slack/events/

Mattermost outgoing webhook callback:
  http://django:8000/hooks/mattermost/events/
  (and AllowedUntrustedInternalConnections includes django)

EOF
