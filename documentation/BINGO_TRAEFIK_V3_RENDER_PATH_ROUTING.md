# BINGO: Traefik v3 Path-Based Routing for Render

Date: 2026-04-28
Branch: main
Status: COMPLETE (BINGO)

## Summary
Created a complete Traefik v3 deployment strategy for Render to achieve single-domain path-based routing (`production.polysaas.online`) across multiple services. This works around Render's 2 custom domain limit per workspace by using Traefik as a reverse proxy on Render itself.

## Architecture
- Single domain: `production.polysaas.online`
- Path-based routing:
  - `/` → PolySaaS Core (Render Web Service)
  - `/mattermost` → Mattermost (Render Docker Service)
  - `/odoo` → Odoo (Render Docker Service)
  - `/nextcloud` → Nextcloud (Render Docker Service)
- Traefik deployed as Render Docker Service
- Traefik proxies to Render service URLs (not Docker containers, since Render doesn't support Docker labels)

## Key Design Decision
User's local Windows laptop has no fixed IP and no outside access, so local Traefik deployment is not feasible. Traefik must run on Render itself.

## Files Created
- `traefik-stack/traefik.Dockerfile` — Render-specific Dockerfile for Traefik v3
- `traefik-stack/render.yaml` — Render blueprint for deploying Traefik + backend services
- `traefik-stack/traefik.render.yml` — Traefik configuration (proxies to Render service URLs)
- `traefik-stack/dynamic.yml` — Dynamic config for WebSocket support (Mattermost)
- `traefik-stack/RENDER_DEPLOYMENT.md` — Complete deployment guide
- `traefik-stack/docker-compose.yml` — Local Docker Compose (for reference)
- `traefik-stack/docker-compose.windows.yml` — Windows-specific Docker Compose (for reference)
- `traefik-stack/traefik.yml` — Original Traefik config (for reference)
- `traefik-stack/.env.example` — Environment variables template
- `traefik-stack/README.md` — General documentation

## Follow-ups
- Deploy Traefik service on Render using `traefik.Dockerfile`
- Deploy backend services (Mattermost, Odoo, Nextcloud) as separate Render services
- Configure Traefik environment variables with service URLs
- Copy `traefik.render.yml` → `traefik.yml` and redeploy Traefik
- Verify routing works for all paths
