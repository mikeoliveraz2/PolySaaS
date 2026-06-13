"""System prompt assembly for staff PolySaaS AI admin chat (Phase 1)."""
# THIS CODE IS FROZEN — NO CHANGES TO THIS CODE ARE ALLOWED WITHOUT THE OWNER'S PERMISSION
# BINGO: PolySaaS AI Context-Aware Chat — commit PENDING

from __future__ import annotations

from django.conf import settings

from llm_router.integrations import platform_context_for_system_prompt
from llm_router.page_context import format_page_context_for_system_prompt


def build_staff_admin_system_prompt(
    request,
    *,
    ml_studio_instruction_appendix: str = "",
    page_context: str = "",
) -> str:
    """
    Merge: platform links, optional settings base prompt, ML Studio appendix,
    live page context, Geronimo persona.
    """
    parts: list[str] = [platform_context_for_system_prompt(request)]

    ctx_block = format_page_context_for_system_prompt(page_context)
    if ctx_block:
        parts.append(ctx_block)

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
        "You are Geronimo, the PolySaaS AI co-pilot — a context-aware assistant embedded "
        "in the PolySaaS orchestration shell. Use the current page context above to tailor "
        "answers (tenant, passthrough service, Mattermost channel, Odoo screen, orchestration bar). "
        "Be helpful and concise. When relevant, suggest orchestration instructions or point at "
        "platform URLs from the reference list. Do not invent tenant data not present in context."
    )
    return "\n\n".join(parts)
