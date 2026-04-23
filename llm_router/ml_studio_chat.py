"""ML Studio (MLPrompt) integration for admin PolySaaS AI chat — Phase 2."""

from __future__ import annotations

import logging
from typing import Any

from django.conf import settings

log = logging.getLogger(__name__)


def load_ml_studio_refine_template(request: Any) -> tuple[str | None, str | None]:
    """
    Load tenant ``MLPrompt`` row for the configured refine key.

    Returns ``(prompt_text, skip_reason)``. ``skip_reason`` is None when a template exists.
    """
    key = (getattr(settings, "LLM_ROUTER_ML_STUDIO_REFINE_KEY", None) or "polysaas_admin_chat_refine").strip()
    try:
        from dose.models import MLPrompt
        from dose.utils import get_current_tenant
    except Exception as exc:
        log.warning("ml_studio_chat: could not import dose models (%s)", exc)
        return None, "import_error"

    tenant = get_current_tenant(request)
    if not tenant:
        return None, "no_tenant"

    try:
        row = MLPrompt.objects.filter(tenant=tenant, key=key).first()
    except Exception:
        log.exception("ml_studio_chat: MLPrompt query failed")
        return None, "query_error"

    if not row:
        return None, "missing_prompt"

    text = (row.prompt_text or "").strip()
    if not text:
        return None, "empty_prompt"

    return text, None


def refine_user_message_via_lite_llm(
    request: Any,
    *,
    template: str,
    raw_message: str,
    page_context: str = "",
) -> str:
    """
    Second LLM call (lite route): rewrite user text using ML Studio template as system.
    """
    from llm_router.providers import complete_chat
    from llm_router.router import route

    pc = (page_context or "").strip()[:500]
    sys = (
        template.strip()
        + "\n\nRewrite the following user request into a single clear instruction for a "
        "PolySaaS staff assistant. Output only the rewritten instruction; no preamble, no quotes."
    )
    if pc:
        sys += f"\n\nOptional admin page context: {pc}"

    plan = route(prompt=raw_message, user_tier="staff", task_hint="chat")
    out = complete_chat(
        plan,
        messages=[{"role": "user", "content": raw_message}],
        system_prompt=sys,
        max_tokens=1024,
        timeout=60,
    )
    refined = (out or "").strip()
    if len(refined) < 3:
        return raw_message
    return refined


def resolve_effective_user_message(
    request: Any,
    *,
    mode: str,
    raw_message: str,
    page_context: str,
) -> tuple[str, dict[str, Any]]:
    """
    Two-step ML Studio: refine user text with a lite-routed completion.

    Returns ``(effective_message, meta)``. On skip or error, returns ``raw_message``.
    """
    meta: dict[str, Any] = {"mode": mode}
    if mode != "ml_studio":
        meta["ml_studio"] = None
        return raw_message, meta

    tmpl, skip = load_ml_studio_refine_template(request)
    if skip:
        meta["ml_studio"] = {"skipped": skip}
        return raw_message, meta

    try:
        refined = refine_user_message_via_lite_llm(
            request,
            template=tmpl,
            raw_message=raw_message,
            page_context=page_context,
        )
    except Exception as exc:
        log.exception("ml_studio refine LLM step failed")
        meta["ml_studio"] = {"skipped": "refine_llm_error", "detail": str(exc)[:200]}
        return raw_message, meta

    meta["ml_studio"] = {"refined": True, "refine_chars": len(refined)}
    return refined, meta


def ml_studio_template_for_system_appendix(
    request: Any,
) -> tuple[str, dict[str, Any]]:
    """Single-call ML Studio mode: return template text to merge into the main system prompt."""
    tmpl, skip = load_ml_studio_refine_template(request)
    meta: dict[str, Any] = {}
    if skip:
        meta["ml_studio"] = {"skipped": skip}
        return "", meta
    meta["ml_studio"] = {
        "template_injected": True,
        "key": getattr(settings, "LLM_ROUTER_ML_STUDIO_REFINE_KEY", ""),
    }
    return tmpl or "", meta
