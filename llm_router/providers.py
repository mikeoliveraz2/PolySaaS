"""
Provider HTTP calls after routing (Anthropic, xAI, Gemini).

Uses the same API keys as ``mysite.settings`` / AI Peers. Does not log raw
request bodies beyond what ``llm_router.router`` already records.
"""

from __future__ import annotations

import logging
from typing import Any, List

import requests
from django.conf import settings

from llm_router.router import RoutePlan

log = logging.getLogger(__name__)


def complete_chat(
    plan: RoutePlan,
    *,
    messages: List[dict[str, Any]],
    system_prompt: str = "",
    max_tokens: int = 1024,
    timeout: int = 90,
) -> str:
    """
    Run one chat completion using the routed provider and model.

    ``messages`` are OpenAI-shaped: ``[{"role": "user"|"assistant", "content": "..."}, ...]``.
    """
    provider = plan.provider.lower()
    if provider == "anthropic":
        return _anthropic(plan.model, messages, system_prompt, max_tokens, timeout)
    if provider in ("xai", "grok"):
        return _xai(plan.model, messages, system_prompt, max_tokens, timeout)
    if provider == "gemini":
        return _gemini(plan.model, messages, system_prompt, max_tokens, timeout)
    raise ValueError(f"Unsupported LLM router provider: {plan.provider}")


def _to_anthropic_messages(messages: List[dict[str, Any]]) -> list[dict[str, str]]:
    out: list[dict[str, str]] = []
    for m in messages:
        role = m.get("role") or "user"
        if role not in ("user", "assistant"):
            role = "user"
        out.append({"role": role, "content": str(m.get("content", ""))})
    return out


def _anthropic(
    model: str,
    messages: List[dict[str, Any]],
    system_prompt: str,
    max_tokens: int,
    timeout: int,
) -> str:
    api_key = getattr(settings, "ANTHROPIC_API_KEY", "") or ""
    if not api_key:
        return "[llm_router] ANTHROPIC_API_KEY not configured."
    payload = {
        "model": model,
        "max_tokens": max_tokens,
        "messages": _to_anthropic_messages(messages),
    }
    if system_prompt:
        payload["system"] = system_prompt
    resp = requests.post(
        "https://api.anthropic.com/v1/messages",
        headers={
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        },
        json=payload,
        timeout=timeout,
    )
    if resp.status_code != 200:
        log.error("Anthropic error status=%s body=%s", resp.status_code, resp.text[:500])
        resp.raise_for_status()
    data = resp.json()
    return data["content"][0]["text"]


def _xai(
    model: str,
    messages: List[dict[str, Any]],
    system_prompt: str,
    max_tokens: int,
    timeout: int,
) -> str:
    api_key = getattr(settings, "XAI_API_KEY", "") or ""
    if not api_key:
        return "[llm_router] XAI_API_KEY not configured."
    chat_messages: list[dict[str, str]] = []
    if system_prompt:
        chat_messages.append({"role": "system", "content": system_prompt})
    for m in messages:
        role = m.get("role") or "user"
        if role not in ("user", "assistant", "system"):
            role = "user"
        chat_messages.append({"role": role, "content": str(m.get("content", ""))})
    resp = requests.post(
        "https://api.x.ai/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        json={
            "model": model,
            "messages": chat_messages,
            "max_tokens": max_tokens,
        },
        timeout=timeout,
    )
    if resp.status_code != 200:
        log.error("xAI error status=%s body=%s", resp.status_code, resp.text[:500])
        resp.raise_for_status()
    data = resp.json()
    return data["choices"][0]["message"]["content"]


def _gemini(
    model: str,
    messages: List[dict[str, Any]],
    system_prompt: str,
    max_tokens: int,
    timeout: int,
) -> str:
    api_key = getattr(settings, "GEMINI_API_KEY", "") or ""
    if not api_key:
        return "[llm_router] GEMINI_API_KEY not configured."
    contents = []
    for m in messages:
        role = "model" if (m.get("role") == "assistant") else "user"
        contents.append(
            {"role": role, "parts": [{"text": str(m.get("content", ""))}]}
        )
    mid = model or "gemini-flash-latest"
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{mid}:generateContent"
    body: dict[str, Any] = {
        "contents": contents,
        "generationConfig": {"maxOutputTokens": max_tokens},
    }
    if system_prompt:
        body["system_instruction"] = {"parts": [{"text": system_prompt}]}
    resp = requests.post(url, params={"key": api_key}, json=body, timeout=timeout)
    if resp.status_code != 200:
        log.error("Gemini error status=%s body=%s", resp.status_code, resp.text[:500])
        resp.raise_for_status()
    data = resp.json()
    return data["candidates"][0]["content"]["parts"][0]["text"]
