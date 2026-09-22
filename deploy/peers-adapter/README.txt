PolySaaS Peers Adapter (phase 1)
================================

Purpose
-------
Thin HTTP service for Mattermost outgoing webhooks (AI as Peers / Apps as Peers).
Phase 1 proxies POST bodies to the existing Django endpoint:

  {PEERS_UPSTREAM_DJANGO_URL}/dose/webhook/ai-peers/

So you can point Mattermost at the adapter URL on Render while LLM + peer logic
still runs in PolySaaS-Core. Later phases can move logic into this image or an
internal API without changing the Mattermost trigger path again.

Endpoints
---------
  GET  /health                      — Render health check
  POST /v1/mattermost/outgoing      — Mattermost outgoing webhook (JSON body)

Environment
-------------
  PEERS_UPSTREAM_DJANGO_URL   Required. Base URL only, no path. Example:
                              https://app.prod-polysaas.cloud

  AI_PEERS_WEBHOOK_TOKEN      Optional. If set, JSON body must include the same
                              token field as Mattermost/Django expect (defense
                              in depth). If unset, proxy only (Django validates).

  LOG_LEVEL                   Optional. Default INFO.

Mattermost
----------
Outgoing webhook callback URL:

  https://<your-adapter-host>/v1/mattermost/outgoing

Use the same Content-Type and JSON payload Mattermost sends today; token must
match Django setup (and adapter if AI_PEERS_WEBHOOK_TOKEN is set here).

Local
-----
  docker build -t peers-adapter .
  docker run -e PEERS_UPSTREAM_DJANGO_URL=http://host.docker.internal:8000 -p 8001:8000 peers-adapter

Render Blueprint
----------------
See render.yaml service PolySaaS-Peers-Adapter: dockerfilePath deploy/peers-adapter/Dockerfile,
dockerContext deploy/peers-adapter.
