"""System prompt assembly for staff PolySaaS AI admin chat (Phase 1)."""

from __future__ import annotations

from django.conf import settings

from llm_router.integrations import platform_context_for_system_prompt


def build_staff_admin_system_prompt(
    request,
    *,
    ml_studio_instruction_appendix: str = "",
) -> str:
    """
    Merge, in order: platform link context, optional persistent base prompt from settings,
    optional ML Studio template appendix (single-call mode), then the fixed staff line.
    """
    parts: list[str] = [platform_context_for_system_prompt(request)]

    base = (getattr(settings, "LLM_ROUTER_ADMIN_BASE_SYSTEM_PROMPT", None) or "").strip()
    if base:
        parts.append(base)

    extra = (ml_studio_instruction_appendix or "").strip()
    if extra:
        parts.append(
            "--- ML Studio prompt template (apply when interpreting the user) ---\n"
            + extra
        )

    parts.append(
        "You are PolySaaS staff assistant connected via the in-app LLM router. "
        "Answer concisely; when relevant, point at the URLs above (admin, Swagger, REST logs, passthrough)."
    )
    return "\n\n".join(parts)
