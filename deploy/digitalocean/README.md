# PolySaaS on DigitalOcean (phase 1)

See the full runbook: [DIGITALOCEAN_DEPLOY_RUNBOOK.md](../../documentation/deployment/DIGITALOCEAN_DEPLOY_RUNBOOK.md)

Quick start:

1. `scripts/provision-droplet.ps1` (laptop, needs doctl + token)
2. `scripts/bootstrap-droplet.sh` (on droplet)
3. Fill `.env` from `.env.example`
4. `scripts/dns-checklist.sh <floating-ip>` then create DNS A records
5. `scripts/bringup.sh`
6. Optional: `scripts/dump-local-for-restore.sh` → `scripts/migrate-data.sh`
7. `scripts/smoke-test.sh`
