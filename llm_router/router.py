"""
Public routing API: choose provider + model from prompt and tenant/user tier.

Used by orchestration, ML Studio, DoseAI, and Peers features — call
``route()`` then ``providers.complete_chat()`` (or your own client).
"""

from __future__ import annotations

import logging
from dataclasses import dataclass

from django.conf import settings

from llm_router.classifiers import TaskBucket, classify
from llm_router.config import get_router_config, rough_cost_per_1k_tokens_usd
from llm_router import utils

log = logging.getLogger("llm_router.decisions")


@dataclass(frozen=True)
class RoutePlan:
    provider: str
    model: str
    task_bucket: str
    user_tier: str
    reason: str


def normalize_user_tier(raw: str | None) -> str:
    t = (raw or "").strip().lower()
    if t in ("free", "standard", "premium", "staff"):
        return t
    return get_router_config().default_user_tier


def route(
    *,
    prompt: str,
    task_hint: str | None = None,
    user_tier: str | None = None,
) -> RoutePlan:
    """
    Decide provider + model for this prompt.

    ``user_tier`` should reflect subscription or internal role (``staff`` for
    platform operators). Unknown values fall back to ``LLM_ROUTER_DEFAULT_USER_TIER``.
    """
    cfg = get_router_config()
    if not cfg.enabled:
        bucket = TaskBucket.STANDARD
        reason = "router_disabled_default_standard"
    else:
        bucket = classify(prompt=prompt, task_hint=task_hint)
        reason = f"classifier:{bucket.value}"

    tier = normalize_user_tier(user_tier)
    key = (tier, bucket.value)
    provider, model = cfg.routes.get(
        key,
        (
            getattr(settings, "LLM_ROUTER_STANDARD_PROVIDER", "anthropic"),
            getattr(settings, "LLM_ROUTER_STANDARD_MODEL", "claude-sonnet-4-20250514"),
        ),
    )

    plan = RoutePlan(
        provider=provider,
        model=model,
        task_bucket=bucket.value,
        user_tier=tier,
        reason=reason,
    )
    _log_decision(cfg, plan, prompt)
    return plan


def _log_decision(cfg, plan: RoutePlan, prompt: str) -> None:
    n = utils.prompt_char_len(prompt)
    hint = rough_cost_per_1k_tokens_usd(plan.provider, plan.model)
    if cfg.log_full_prompt:
        body = prompt
    else:
        body = utils.safe_prompt_fragment(prompt, cfg.log_prompt_max_chars)
    log.info(
        "llm_route provider=%s model=%s tier=%s bucket=%s chars=%s cost_hint_1k=%s reason=%s excerpt=%r",
        plan.provider,
        plan.model,
        plan.user_tier,
        plan.task_bucket,
        n,
        hint,
        plan.reason,
        body,
    )
