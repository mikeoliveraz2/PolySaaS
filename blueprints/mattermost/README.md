# PolySaaS Blueprint: Mattermost (Team Edition)

## Quick start
1. `copy .env.example .env`
2. Edit `.env`
3. `docker compose --env-file .env up -d --build`
4. `./provision.sh`

## Reverse proxy
Traefik labels are included.

## Data persistence
Volumes are namespaced by `TENANT_SLUG`.
