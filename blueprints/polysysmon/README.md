# PolySaaS Blueprint: PolySysMon

## What this is
A tenant-scoped monitoring dashboard baseline using Grafana.

## Quick start
1. `copy .env.example .env`
2. Edit `.env`
3. `docker compose --env-file .env up -d --build`
4. `./provision.sh`

## Data persistence
Grafana volume is namespaced by `TENANT_SLUG`.
