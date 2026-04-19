"""
PolySaaS Peers Adapter — phase 1: validate optional edge token, proxy Mattermost
outgoing webhook POST to Django (existing ai_peers_webhook). LLM + peer logic
stays in Django until ported here or behind an internal API.
"""
from __future__ import annotations

import json
import logging
import os

import httpx
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import JSONResponse, Response
from starlette.routing import Route

logger = logging.getLogger("peers_adapter")
logging.basicConfig(level=os.environ.get("LOG_LEVEL", "INFO"))


def _upstream_url() -> str:
    return os.environ.get("PEERS_UPSTREAM_DJANGO_URL", "").strip().rstrip("/")


def _edge_token() -> str:
    return os.environ.get("AI_PEERS_WEBHOOK_TOKEN", "").strip()


async def health(_: Request) -> JSONResponse:
    return JSONResponse({"status": "ok", "service": "peers-adapter"})


async def mattermost_outgoing(request: Request) -> Response:
    upstream = _upstream_url()
    if not upstream:
        logger.error("PEERS_UPSTREAM_DJANGO_URL is not set")
        return JSONResponse(
            {"error": "adapter_misconfigured", "detail": "PEERS_UPSTREAM_DJANGO_URL unset"},
            status_code=503,
        )

    body = await request.body()
    ct = request.headers.get("content-type", "application/json")

    # Optional defense-in-depth: Mattermost includes `token` in JSON body; Django
    # already validates. If AI_PEERS_WEBHOOK_TOKEN is set on the adapter, require
    # JSON body to parse and match (light check without full JSON parse if empty).
    edge = _edge_token()
    if edge:
        try:
            payload = json.loads(body.decode("utf-8") if body else "{}")
        except (json.JSONDecodeError, UnicodeDecodeError):
            return JSONResponse({"error": "invalid_json"}, status_code=400)
        if payload.get("token", "") != edge:
            logger.warning("mattermost_outgoing: edge token mismatch")
            return JSONResponse({"error": "Forbidden"}, status_code=403)

    target = f"{upstream}/dose/webhook/ai-peers/"
    headers = {"Content-Type": ct}
    fwd = request.headers.get("X-Forwarded-For")
    if fwd:
        headers["X-Forwarded-For"] = fwd

    try:
        async with httpx.AsyncClient(timeout=httpx.Timeout(60.0)) as client:
            r = await client.post(target, content=body, headers=headers)
    except httpx.RequestError as exc:
        logger.exception("upstream request failed: %s", exc)
        return JSONResponse(
            {"error": "upstream_unreachable", "detail": str(exc)},
            status_code=502,
        )

    out_headers = {}
    rct = r.headers.get("content-type")
    if rct:
        out_headers["content-type"] = rct
    return Response(r.content, status_code=r.status_code, headers=out_headers)


routes = [
    Route("/health", health, methods=["GET"]),
    Route("/v1/mattermost/outgoing", mattermost_outgoing, methods=["POST"]),
]

app = Starlette(debug=False, routes=routes)
