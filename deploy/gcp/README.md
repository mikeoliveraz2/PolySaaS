# PolySaaS GCP Deployment

Operator scripts and configs for migrating from Render to GCP.

**Full runbook:** [`documentation/deployment/gcp/GCP_MIGRATION_RUNBOOK.md`](../../documentation/deployment/gcp/GCP_MIGRATION_RUNBOOK.md)

## Quick start

```powershell
Copy-Item deploy\gcp\config.env.example deploy\gcp\config.env
# Edit config.env

# Phase 1 — infra
.\deploy\gcp\setup-infrastructure.ps1

# Phase 2 — Odoo + Mattermost (bash / Git Bash)
bash deploy/gcp/provision-vm.sh
bash deploy/gcp/deploy-bundled-apps.sh

# Phase 3 — migrate from Render
bash deploy/gcp/migrate-from-render.sh

# Phase 4 — local test
# Merge deploy/gcp/.env.local-gcp.example into .env
.\deploy\gcp\verify-integration.ps1
.\runall.ps1

# Phase 5 — Django Cloud Run
bash deploy/gcp/deploy-cloud-run.sh

# Phase 6 — CI/CD trigger
bash deploy/gcp/setup-cicd-trigger.sh
```

## Key files

| File | Purpose |
|------|---------|
| `config.env.example` | GCP variables template |
| `docker-compose.gcp.yml` | Odoo + Mattermost on Compute Engine |
| `setup-infrastructure.sh` | Buckets, DBs, service accounts |
| `migrate-from-render.sh` | Database cutover |
| `../../Dockerfile.gcp` | Django Cloud Run image |
| `../../cloudbuild.yaml` | CI/CD pipeline |
