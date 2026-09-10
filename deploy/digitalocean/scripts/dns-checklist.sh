#!/usr/bin/env bash
# Print DNS records required for Traefik Let's Encrypt.
set -euo pipefail

FLOATING_IP="${1:-${FLOATING_IP:-}}"
if [[ -z "$FLOATING_IP" ]]; then
  echo "Usage: $0 <floating-ip>"
  echo "Or set FLOATING_IP=..."
  exit 1
fi

cat <<EOF
Add these DNS A records (TTL 300) at your DNS provider for polysaas.online:

  app.polysaas.online    A    $FLOATING_IP
  mm.polysaas.online     A    $FLOATING_IP
  odoo.polysaas.online   A    $FLOATING_IP

Leave apex polysaas.online on the current WordPress host (phase 1).

After propagation:
  dig +short app.polysaas.online
  dig +short mm.polysaas.online
  dig +short odoo.polysaas.online

Expect each to return: $FLOATING_IP

Then Traefik will obtain certs via HTTP-01 on first HTTPS request.
EOF
