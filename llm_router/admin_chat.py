"""Staff-only PolySaaS AI chat (admin shell) + JSON API for the in-process LLM router."""
# THIS CODE IS FROZEN — NO CHANGES TO THIS CODE ARE ALLOWED WITHOUT THE OWNER'S PERMISSION
# BINGO: PolySaaS AI Context-Aware Chat — commit fd9febb8

from __future__ import annotations

import json
import logging
from typing import Any

from django.conf import settings
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_POST

from llm_router.admin_prompts import build_staff_admin_system_prompt
from llm_router.ml_studio_chat import (
    ml_studio_template_for_system_appendix,
    resolve_effective_user_message,
)
from llm_router.providers import complete_chat
from llm_router.router import RoutePlan, route

log = logging.getLogger(__name__)

_MAX_MESSAGE = 16000
_MAX_HISTORY_TURNS = 24
_MAX_CONTENT_PER_MSG = 32000
_MAX_PAGE_CONTEXT = 2000


def _admin_chat_route_plan(prompt: str) -> RoutePlan:
    """Admin PolySaaS AI chat — default Gemini for demo / Google for Startups signal."""
    provider = (getattr(settings, "LLM_ROUTER_ADMIN_CHAT_PROVIDER", "") or "gemini").strip().lower()
    model = (getattr(settings, "LLM_ROUTER_ADMIN_CHAT_MODEL", "") or "gemini-2.5-flash").strip()
    if provider:
        return RoutePlan(
            provider=provider,
            model=model,
            task_bucket="standard",
            user_tier="staff",
            reason="admin_chat_configured_provider",
        )
    return route(prompt=prompt, user_tier="staff")


def _normalize_history(raw: Any) -> list[dict[str, str]]:
    if not isinstance(raw, list):
        return []
    out: list[dict[str, str]] = []
    for item in raw[-_MAX_HISTORY_TURNS:]:
        if not isinstance(item, dict):
            continue
        role = item.get("role")
        if role not in ("user", "assistant"):
            continue
        content = str(item.get("content", ""))[:_MAX_CONTENT_PER_MSG]
        out.append({"role": role, "content": content})
    return out


@never_cache
@staff_member_required
def polysaas_ai_chat_page(request):
    """Full admin ``base_site`` page with chat in the main content column (same shell as passthrough)."""
    from dose.models import MLPrompt
    from dose.utils import get_current_tenant

    key = getattr(settings, "LLM_ROUTER_ML_STUDIO_REFINE_KEY", "polysaas_admin_chat_refine")
    tenant = get_current_tenant(request)
    ml_registered = False
    if tenant:
        try:
            ml_registered = MLPrompt.objects.filter(tenant=tenant, key=key).exists()
        except Exception:
            ml_registered = False

    return render(
        request,
        "admin/polysaas_ai_chat.html",
        {
            "title": "PolySaaS AI",
            "page_context_initial": (request.GET.get("context") or "")[:500],
            "ml_studio_refine_key": key,
            "ml_studio_prompt_registered": ml_registered,
            "llm_standard_provider": getattr(settings, "LLM_ROUTER_STANDARD_PROVIDER", ""),
            "llm_standard_model": getattr(settings, "LLM_ROUTER_STANDARD_MODEL", ""),
            "ml_studio_use_llm": getattr(settings, "LLM_ROUTER_ML_STUDIO_REFINE_USE_LLM", True),
        },
    )


@staff_member_required
@require_POST
def admin_llm_router_chat_api(request):
    """
    JSON API for the PolySaaS AI admin chat page.

    Body: ``message``, ``history``, optional ``mode`` (``standard`` | ``ml_studio``),
    optional ``page_context`` (short string, e.g. from ``?context=``).
    """
    try:
        body = json.loads(request.body.decode() or "{}")
    except json.JSONDecodeError:
        return JsonResponse({"error": "invalid_json"}, status=400)

    message = (body.get("message") or "").strip()
    if not message:
        return JsonResponse({"error": "message_required"}, status=400)
    if len(message) > _MAX_MESSAGE:
        return JsonResponse({"error": "message_too_long"}, status=400)

    mode = (body.get("mode") or "standard").strip().lower()
    if mode not in ("standard", "ml_studio"):
        mode = "standard"
    page_context = str(body.get("page_context") or "")[:_MAX_PAGE_CONTEXT]

    history = _normalize_history(body.get("history"))
    ml_appendix = ""
    response_meta: dict[str, Any] = {"mode": mode}

    if mode == "ml_studio" and getattr(settings, "LLM_ROUTER_ML_STUDIO_REFINE_USE_LLM", True):
        effective, sub = resolve_effective_user_message(
            request,
            mode=mode,
            raw_message=message,
            page_context=page_context,
        )
        response_meta["ml_studio"] = sub.get("ml_studio")
    elif mode == "ml_studio":
        effective = message
        tmpl, sub = ml_studio_template_for_system_appendix(request)
        ml_appendix = tmpl or ""
        response_meta["ml_studio"] = sub.get("ml_studio")
    else:
        effective = message
        response_meta["ml_studio"] = None

    messages = list(history)
    messages.append({"role": "user", "content": effective})

    system = build_staff_admin_system_prompt(
        request,
        ml_studio_instruction_appendix=ml_appendix,
        page_context=page_context,
    )

    plan = _admin_chat_route_plan(effective)
    try:
        reply = complete_chat(
            plan,
            messages=messages,
            system_prompt=system,
            max_tokens=2048,
        )
    except Exception as exc:
        log.exception("admin_llm_router_chat_api failed")
        return JsonResponse(
            {"error": "upstream_error", "detail": str(exc)[:500]},
            status=502,
        )

    payload = {
        "reply": reply,
        "provider": plan.provider,
        "model": plan.model,
        "task_bucket": plan.task_bucket,
        "meta": response_meta,
    }
    return JsonResponse(payload)
@login_required
@require_POST
def tenant_llm_router_chat_api(request):
    """
    Tenant-accessible JSON API for LLM chat (no staff required).
    Body: ``message``, ``history``.
    Always returns JSON, even on error.
    """
    try:
        # Parse request body
        try:
            body = json.loads(request.body.decode() or "{}")
        except json.JSONDecodeError as e:
            log.warning("Invalid JSON in tenant chat request: %s", e)
            return JsonResponse({"error": "invalid_json", "detail": str(e)[:200]}, status=400)

        message = (body.get("message") or "").strip()
        if not message:
            return JsonResponse({"error": "message_required"}, status=400)
        if len(message) > _MAX_MESSAGE:
            return JsonResponse({"error": "message_too_long"}, status=400)

        history = _normalize_history(body.get("history"))
        page_context = str(body.get("page_context") or "")[:_MAX_PAGE_CONTEXT]
        messages = list(history)
        messages.append({"role": "user", "content": message})

        # Build system prompt
        try:
            system = build_staff_admin_system_prompt(
                request,
                ml_studio_instruction_appendix="",
                page_context=page_context,
            )
        except Exception as e:
            log.warning("Failed to build system prompt: %s", e)
            system = (
                "You are Geronimo, the PolySaaS AI co-pilot. "
                "Answer questions about workspace features and how-tos."
            )

        # Route and complete — Gemini for tenant passthrough embed chat
        try:
            plan = _admin_chat_route_plan(message)
        except Exception as e:
            log.warning("LLM routing failed: %s", e)
            plan = None

        if not plan:
            return JsonResponse(
                {"error": "routing_failed", "detail": "Could not determine LLM provider"},
                status=502,
            )

        try:
            reply = complete_chat(
                plan,
                messages=messages,
                system_prompt=system,
                max_tokens=2048,
            )
        except Exception as exc:
            log.exception("LLM complete_chat failed in tenant API")
            return JsonResponse(
                {"error": "upstream_error", "detail": str(exc)[:500]},
                status=502,
            )

        payload = {
            "reply": reply,
            "provider": plan.provider,
            "model": plan.model,
            "task_bucket": plan.task_bucket,
        }
        return JsonResponse(payload)

    except Exception as outer_exc:
        # Catch-all for any unforeseen errors
        log.exception("Unexpected error in tenant_llm_router_chat_api")
        return JsonResponse(
            {"error": "internal_error", "detail": str(outer_exc)[:500]},
            status=500,
        )
