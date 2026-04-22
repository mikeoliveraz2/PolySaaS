"""
OpenAI-compatible HTTP surface for internal PolySaaS workloads (Option 2).

POST /v1/chat/completions — body shaped like OpenAI; ``model`` in the body is
ignored for routing unless ``OPENCLAW_ROUTER_TRUST_CLIENT_MODEL=1``.

GET /healthz — liveness.

Run locally::

  pip install -r requirements.txt
  export ANTHROPIC_API_KEY=...
  uvicorn main:app --host 0.0.0.0 --port 8765 --app-dir /path/to/openclaw_router
"""

from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Any, List

import httpx
import yaml
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, ConfigDict, Field

from classifier import bucket_for_openai_messages

log = logging.getLogger("openclaw_router")
logging.basicConfig(level=os.environ.get("LOG_LEVEL", "INFO"))

_CONFIG_PATH = Path(os.environ.get("OPENCLAW_ROUTER_CONFIG", "")).expanduser()
if _CONFIG_PATH.is_file():
    with open(_CONFIG_PATH, encoding="utf-8") as fh:
        CONFIG = yaml.safe_load(fh) or {}
else:
    here = Path(__file__).resolve().parent
    with open(here / "config.yaml", encoding="utf-8") as fh:
        CONFIG = yaml.safe_load(fh) or {}

THRESHOLDS = CONFIG.get("thresholds") or {}
ROUTES = CONFIG.get("routes") or {}
TRUST_CLIENT = os.environ.get("OPENCLAW_ROUTER_TRUST_CLIENT_MODEL", "").strip() == "1"

app = FastAPI(title="PolySaaS OpenClaw Router", version="0.1.0")


@app.get("/healthz")
def healthz():
    return {"status": "ok"}


class ChatMessage(BaseModel):
    model_config = ConfigDict(extra="ignore")
    role: str = "user"
    content: str = ""


class ChatCompletionRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")
    model: str | None = None
    messages: List[ChatMessage] = Field(default_factory=list)
    max_tokens: int = 1024
    temperature: float | None = None


@app.post("/v1/chat/completions")
def chat_completions(body: ChatCompletionRequest):
    msgs = [m.model_dump() for m in body.messages]
    if not msgs:
        raise HTTPException(400, "messages required")

    bucket = bucket_for_openai_messages(msgs, None, THRESHOLDS)
    if TRUST_CLIENT and body.model:
        # passthrough mode — not recommended for cost control
        model_id = body.model
        provider = os.environ.get("OPENCLAW_ROUTER_DEFAULT_PROVIDER", "anthropic")
    else:
        route = ROUTES.get(bucket.value) or ROUTES.get("standard") or {}
        provider = str(route.get("provider", "anthropic")).lower()
        model_id = str(route.get("model", "claude-3-5-haiku-20241022"))

    log.info(
        "route bucket=%s provider=%s model=%s trust_client=%s",
        bucket.value,
        provider,
        model_id,
        TRUST_CLIENT,
    )

    if provider != "anthropic":
        raise HTTPException(501, f"provider {provider!r} not implemented in this skeleton")

    api_key = os.environ.get("ANTHROPIC_API_KEY", "").strip()
    if not api_key:
        raise HTTPException(503, "ANTHROPIC_API_KEY not set")

    system = ""
    anth_msgs: list[dict[str, str]] = []
    for m in msgs:
        role = (m.get("role") or "user").lower()
        if role == "system":
            system = str(m.get("content", ""))
            continue
        if role not in ("user", "assistant"):
            role = "user"
        anth_msgs.append({"role": role, "content": str(m.get("content", ""))})

    payload: dict[str, Any] = {
        "model": model_id,
        "max_tokens": body.max_tokens,
        "messages": anth_msgs,
    }
    if system:
        payload["system"] = system

    try:
        with httpx.Client(timeout=120.0) as client:
            r = client.post(
                "https://api.anthropic.com/v1/messages",
                headers={
                    "x-api-key": api_key,
                    "anthropic-version": "2023-06-01",
                    "content-type": "application/json",
                },
                json=payload,
            )
    except httpx.HTTPError as exc:
        log.exception("upstream error")
        raise HTTPException(502, str(exc)) from exc

    if r.status_code != 200:
        log.error("anthropic status=%s body=%s", r.status_code, r.text[:800])
        raise HTTPException(r.status_code, r.text[:2000])

    data = r.json()
    text = data["content"][0]["text"]
    # OpenAI-shaped response (minimal)
    return {
        "id": "openclaw-router-1",
        "object": "chat.completion",
        "model": model_id,
        "choices": [
            {
                "index": 0,
                "message": {"role": "assistant", "content": text},
                "finish_reason": "stop",
            }
        ],
        "usage": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
    }
