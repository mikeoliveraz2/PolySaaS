"""
Router configuration from Django settings (environment on Render).

Model IDs are strings passed through to provider APIs; override per deployment.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from django.conf import settings


@dataclass(frozen=True)
class RouterConfig:
    enabled: bool
    default_user_tier: str
    log_full_prompt: bool
    log_prompt_max_chars: int
    # (tier, task_bucket) -> (provider, model_id) — task_bucket: lite | standard | heavy
    routes: dict[tuple[str, str], tuple[str, str]]


def _routes_from_settings() -> dict[tuple[str, str], tuple[str, str]]:
    """Build routing table; keys are (user_tier, task_bucket)."""
    # Defaults: lite tasks -> fast/cheap where possible; heavy -> capable models
    r: dict[tuple[str, str], tuple[str, str]] = {}
    tiers = ("free", "standard", "premium", "staff")
    for tier in tiers:
        r[(tier, "lite")] = (
            getattr(settings, "LLM_ROUTER_LITE_PROVIDER", "anthropic"),
            getattr(settings, "LLM_ROUTER_LITE_MODEL", "claude-3-5-haiku-20241022"),
        )
        r[(tier, "standard")] = (
            getattr(settings, "LLM_ROUTER_STANDARD_PROVIDER", "anthropic"),
            getattr(settings, "LLM_ROUTER_STANDARD_MODEL", "claude-sonnet-4-20250514"),
        )
        r[(tier, "heavy")] = (
            getattr(settings, "LLM_ROUTER_HEAVY_PROVIDER", "anthropic"),
            getattr(settings, "LLM_ROUTER_HEAVY_MODEL", "claude-sonnet-4-20250514"),
        )
    # Premium / staff can use configured heavy default (e.g. opus) via env overrides only
    return r


def get_router_config() -> RouterConfig:
    return RouterConfig(
        enabled=getattr(settings, "LLM_ROUTER_ENABLED", True),
        default_user_tier=getattr(settings, "LLM_ROUTER_DEFAULT_USER_TIER", "standard"),
        log_full_prompt=getattr(settings, "LLM_ROUTER_LOG_FULL_PROMPT", False),
        log_prompt_max_chars=int(getattr(settings, "LLM_ROUTER_LOG_PROMPT_MAX_CHARS", 200)),
        routes=_routes_from_settings(),
    )


def rough_cost_per_1k_tokens_usd(provider: str, model: str) -> float | None:
    """Opaque estimates for logging only; not billing."""
    key = f"{provider}:{model}".lower()
    table: dict[str, float] = getattr(settings, "LLM_ROUTER_COST_HINTS_USD_PER_1K", {}) or {}
    if isinstance(table, dict) and key in table:
        return float(table[key])
    return None
