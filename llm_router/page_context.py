"""Format browser-collected page context for LLM system prompts."""
# THIS CODE IS FROZEN — NO CHANGES TO THIS CODE ARE ALLOWED WITHOUT THE OWNER'S PERMISSION
# BINGO: PolySaaS AI Context-Aware Chat — commit fd9febb8

from __future__ import annotations

import json
from typing import Any


def _parse_page_context(raw: str) -> dict[str, Any]:
    text = (raw or "").strip()
    if not text:
        return {}
    if text.startswith("{"):
        try:
            data = json.loads(text)
            return data if isinstance(data, dict) else {"raw": text}
        except json.JSONDecodeError:
            pass
    return {"url": text[:500]}


def format_page_context_for_system_prompt(page_context: str, *, max_chars: int = 1600) -> str:
    """
    Turn frontend ``page_context`` (JSON or legacy URL string) into prompt text.
    """
    data = _parse_page_context(page_context)
    if not data:
        return ""

    lines = ["Current page context (auto-collected when the user sent this message):"]

    mapping = (
        ("tenant_name", "Tenant"),
        ("tenant_slug", "Tenant slug"),
        ("page_title", "Page title"),
        ("section", "Section"),
        ("url", "URL"),
        ("pathname", "Path"),
        ("action_path", "Action path (passthrough / orchestration)"),
        ("active_service", "Active bundled service"),
        ("mattermost_team", "Mattermost team"),
        ("mattermost_channel", "Mattermost channel"),
        ("passthrough_embed", "Passthrough embed"),
    )
    for key, label in mapping:
        val = data.get(key)
        if val is None or val == "":
            continue
        lines.append(f"- {label}: {val}")

    orch = data.get("orchestration")
    if isinstance(orch, dict):
        for ok, ol in (("status", "Orchestration status"), ("menu_id", "Menu ID"), ("event", "Orch event")):
            ov = orch.get(ok)
            if ov:
                lines.append(f"- {ol}: {ov}")

    block = "\n".join(lines).strip()
    if len(block) > max_chars:
        block = block[: max_chars - 3] + "..."
    return block
