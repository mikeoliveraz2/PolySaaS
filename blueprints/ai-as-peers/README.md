# PolySaaS Blueprint: AI as Peers

## What this is
A minimal FastAPI-based placeholder blueprint representing your internal "AI as Peers" service.

## Quick start
1. `copy .env.example .env`
2. Edit `.env`
3. `docker compose --env-file .env up -d --build`
4. `./provision.sh`

## PolySaaS integration hooks
The provisioning script is where PolySaaS should:
- register OAuth2 apps per tenant
- seed service configuration
- publish routing metadata to Traefik (if managed externally)
