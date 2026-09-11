#!/usr/bin/env bash
# Print DNS A records required for Traefik Let's Encrypt (Hostinger VPS).
set -euo pipefail

VPS_IP="${1:-${VPS_IP:-}}"
if [[ -z "$VPS_IP" ]]; then
  echo "Usage: $0 <vps-ip>"
  echo "Or set VPS_IP=..."
  exit 1
fi

cat <<EOF
Add these DNS A records (TTL 300) at your DNS provider for polysaas.online:

  app.polysaas.online    A    $VPS_IP
  mm.polysaas.online     A    $VPS_IP
  odoo.polysaas.online   A    $VPS_IP

Leave apex polysaas.online on the current WordPress host (phase 1).

After propagation:
  dig +short app.polysaas.online
  dig +short mm.polysaas.online
  dig +short odoo.polysaas.online

Expect each to return: $VPS_IP

Then Traefik will obtain certs via TLS-ALPN-01 (port 443) on first HTTPS request.
Ensure Hostinger / UFW firewall allows 22, 80, and 443.
EOF
