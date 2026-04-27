# PolySaaS Blueprint: Nextcloud

## What this is
Tenant-scoped Nextcloud stack with Redis + PostgreSQL, plus an OnlyOffice DocumentServer container for integration readiness.

## Quick start
1. `copy .env.example .env`
2. Edit `.env`
3. `docker compose --env-file .env up -d --build`
4. Run provisioning hook:
   - `./provision.sh`

## Reverse proxy
Traefik labels are included; set `TRAEFIK_NETWORK` and ensure that external network exists.

## Data persistence
Volumes are namespaced by `TENANT_SLUG`.
