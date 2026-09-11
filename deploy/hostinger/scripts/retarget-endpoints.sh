#!/usr/bin/env bash
# Print Django / webhook retarget hints after Hostinger bring-up.
set -euo pipefail

cat <<'EOF'
Retarget PassThroughEndpoint / TenantApp after Hostinger bring-up
=================================================================

Prefer Docker-internal URLs for server-side passthrough fetches:

  Mattermost endpoint_url = http://mattermost:8065
  Odoo endpoint_url       = http://odoo:8069

Public SiteURL / browser URLs:

  Mattermost SiteURL      = https://mm.polysaas.online
  Odoo public             = https://odoo.polysaas.online

External producers (update in vendor consoles):

  Slack Events Request URL =
    https://app.polysaas.online/hooks/slack/events/

  HubSpot FlowLink Target URL =
    https://app.polysaas.online/dose/webhook/hubspot/polysaasonline/

  Mattermost outgoing webhook callback (from MM container) =
    http://django:8000/hooks/mattermost/events/
  Trigger word = newpolysaascontact
  AllowedUntrustedInternalConnections must include: django

Django shell example (on VPS):

  docker compose -f deploy/hostinger/docker-compose.yml --env-file deploy/hostinger/.env \
    run --rm --entrypoint "" django python manage.py shell

  # Then set search_path to tenant and update PassThroughEndpoint.endpoint_url

EOF
