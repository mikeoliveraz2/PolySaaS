# PolySaaS on Hostinger VPS (phase 1)

See the full runbook: [HOSTINGER_DEPLOY_RUNBOOK.md](../../documentation/deployment/HOSTINGER_DEPLOY_RUNBOOK.md)

Quick start:

1. `scripts/provision-vps.ps1` (hPanel checklist — order KVM 4 + Docker template)
2. `scripts/bootstrap-vps.sh` (on VPS as root)
3. Fill `.env` from `.env.example`
4. `scripts/dns-checklist.sh <VPS_IP>` then create DNS A records
5. `scripts/bringup.sh`
6. Optional: `scripts/dump-local-for-restore.sh` → `scripts/migrate-data.sh`
7. `scripts/smoke-test.sh` + `scripts/retarget-endpoints.sh`
