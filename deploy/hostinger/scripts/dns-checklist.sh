#!/usr/bin/env bash
# Print DNS A records for Dokploy / Hostinger (prod-polysaas.cloud).
set -euo pipefail

VPS_IP="${1:-${VPS_IP:-187.53.138.235}}"

cat <<EOF
Add these DNS A records (TTL 300) for prod-polysaas.cloud → Hostinger VPS:

  app.prod-polysaas.cloud    A    $VPS_IP
  mm.prod-polysaas.cloud     A    $VPS_IP
  odoo.prod-polysaas.cloud   A    $VPS_IP

(Optional) apex / www for Dokploy panel if you use them separately.

Leave polysaas.online WordPress apex unchanged (phase 1).

After propagation:
  dig +short app.prod-polysaas.cloud
  dig +short mm.prod-polysaas.cloud
  dig +short odoo.prod-polysaas.cloud

Expect each to return: $VPS_IP

Dokploy Traefik issues Let's Encrypt certs once DNS points here (ports 80/443 open).
EOF
