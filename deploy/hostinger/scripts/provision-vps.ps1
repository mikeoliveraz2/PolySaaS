# Hostinger VPS provision checklist (hPanel — no API token required).
# Run on laptop after you are ready to order KVM 4.
# Usage: .\deploy\hostinger\scripts\provision-vps.ps1

$ErrorActionPreference = "Stop"

Write-Host @"

=== Hostinger VPS provision checklist (PolySaaS phase 1) ===

1. Sign in to https://hpanel.hostinger.com
2. Order VPS → plan **KVM 4** (4 vCPU / 16 GB RAM / 200 GB NVMe)
   - Prefer Asia / Singapore datacenter if listed; else lowest latency to users
3. OS template: **Ubuntu 24.04 with Docker** (or install Docker template after create)
4. Add your SSH public key in hPanel (disable password SSH after first login)
5. Note the VPS **public IPv4** from the VPS overview page
6. Firewall (hPanel and/or UFW after bootstrap): allow **22, 80, 443** only
7. Take a manual snapshot once the empty OS is up (optional but recommended)

Then SSH and bootstrap:

  ssh root@<VPS_IP>
  curl -fsSL https://raw.githubusercontent.com/mikeoliveraz2/PolySaaS/main/deploy/hostinger/scripts/bootstrap-vps.sh | bash

Or if you prefer clone-first:

  ssh root@<VPS_IP>
  git clone https://github.com/mikeoliveraz2/PolySaaS.git /opt/polysaas
  bash /opt/polysaas/deploy/hostinger/scripts/bootstrap-vps.sh

Record for handoff:
  VPS_IP=
  PLAN=KVM 4
  REGION=
  ORDERED_ON=

Next: DNS A records (app/mm/odoo.polysaas.online → VPS_IP), edit .env, bringup.sh
See: documentation/deployment/HOSTINGER_DEPLOY_RUNBOOK.md

"@
