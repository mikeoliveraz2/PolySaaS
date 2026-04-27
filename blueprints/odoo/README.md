# PolySaaS Blueprint: Odoo

## What this is
This blueprint is a tenant-scoped, production-oriented Docker Compose stack for Odoo.

## Tenant variables
- `TENANT_SLUG`
- `DOMAIN`
- `SUBDOMAIN`

## Quick start
1. Copy env file:
   - `copy .env.example .env`
2. Edit secrets in `.env`.
3. Deploy:
   - `docker compose --env-file .env up -d --build`

## Reverse proxy (Traefik)
This stack ships with Traefik labels. Ensure an external network exists matching `TRAEFIK_NETWORK` (default: `proxy`).

## PolySaaS provisioning hook
Run the provisioning script after deploy:
- `./provision.sh`

## Data persistence
All volumes are namespaced by `TENANT_SLUG`.
