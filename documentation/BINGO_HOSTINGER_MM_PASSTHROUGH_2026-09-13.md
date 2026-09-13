<!-- THIS CODE IS FROZEN — NO CHANGES TO THIS CODE ARE ALLOWED WITHOUT THE OWNER'S PERMISSION -->
# BINGO: Hostinger Mattermost passthrough (Town Square)

**Date:** 2026-09-13 (Sunday)  
**Branch:** main  
**Certification commits (code):** `c3e8cfa6`, `c31479a3`, `7201b356`, `cec81578`  
**Doc / freeze commit:** `c94bd17b`

## What was verified

On Hostinger + Dokploy (`app.prod-polysaas.cloud` / `mm.prod-polysaas.cloud`):

1. Public Mattermost reachable at `https://mm.prod-polysaas.cloud` (healthcheck disabled so Traefik routes the host).
2. PolySaaS passthrough embed at `/pt/admin/mm.prod-polysaas.cloud/` loads the Mattermost SPA inside the admin shell.
3. Authenticated UI paints: team **PolySaaS Online LLC**, channel **Town Square**, composer **Write to Town Square**.
4. Orchestration bar shows passthrough embed active with action path `/polysaas-online-llc/channels/town-square`.

## Root causes fixed

| Issue | Fix |
|-------|-----|
| Traefik 404 on `mm.*` | MM image has no curl → healthcheck left container unhealthy; `healthcheck: disable: true` in compose |
| Mixed Content / bare `/static/` 404 on app host | Rewrite HTML `/static/` → `/pt/admin/<slug>/static/`; shim chunk + webpack path + API via same-origin proxy |
| Double-quote rewrite bug | Closing quote included in regex match |
| Handler never ran for Hostinger slug | `matches_endpoint` only looked for `"mattermost"`; widened to `mm.*` host/slug |

## Screenshot proof

![Hostinger Mattermost passthrough — Town Square in PolySaaS embed](assets/BINGO_HOSTINGER_MM_PASSTHROUGH_2026-09-13_town-square.jpg)

Caption: Oliver Enterprises admin — MatterMost passthrough embed showing Town Square + composer (2026-09-13).

## Frozen files

- `dose/passthrough/handlers/mattermost_handler.py` (+ `.bak`)
- Related infra (prior freeze + MM health FIX): `deploy/hostinger/docker-compose.yml`

## Ops notes

- Django code is image-baked (`Dockerfile.django`) — Dokploy **Rebuild** required after git push (Deploy alone is not enough).
- Endpoint (olient): `endpoint_url=https://mm.prod-polysaas.cloud`, slug `mm.prod-polysaas.cloud`.
- Prefer Dokploy **Git** provider (not unconfigured GitHub App tab).
