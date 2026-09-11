# PolySaaS on Hostinger VPS + Dokploy (phase 1)

See the full runbook: [HOSTINGER_DEPLOY_RUNBOOK.md](../../documentation/deployment/HOSTINGER_DEPLOY_RUNBOOK.md)

**Live:** VPS `187.53.138.235` · domain `prod-polysaas.cloud` · orchestrator **Dokploy**

Quick start:

1. DNS: `scripts/dns-checklist.sh 187.53.138.235`
2. Dokploy → New Compose application → repo `deploy/hostinger/docker-compose.yml` + env from `.env.example`
3. Or SSH: fill `.env`, then `scripts/bringup.sh` (requires `dokploy-network`)
4. Optional: `scripts/dump-local-for-restore.sh` → `scripts/migrate-data.sh`
5. `scripts/smoke-test.sh` + `scripts/retarget-endpoints.sh`

Do **not** enable the old standalone Traefik service — Dokploy owns `:80`/`:443`. `traefik.yml` is unused under Dokploy.
