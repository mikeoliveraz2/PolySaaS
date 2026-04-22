"""Rule-based bucket selection (mirrors Django ``llm_router.classifiers`` logic)."""

from __future__ import annotations

import enum
import re
from typing import Any, Mapping


class TaskBucket(enum.Enum):
    LITE = "lite"
    STANDARD = "standard"
    HEAVY = "heavy"


_CODE_HINT = re.compile(
    r"\b(def |class |import |```|SELECT |FROM |await |async def )\b",
    re.IGNORECASE,
)
_ANALYSIS_HINT = re.compile(
    r"\b(analy[sz]e|dataset|metrics|evaluation|report|summari[sz]e|compare trends)\b",
    re.IGNORECASE,
)
_AGENTIC_HINT = re.compile(
    r"\b(tool use|function call|multi-?step|agent|orchestrat|workflow)\b",
    re.IGNORECASE,
)


def classify_prompt(
    prompt: str,
    task_hint: str | None,
    thresholds: Mapping[str, Any],
) -> TaskBucket:
    text = (prompt or "").strip()
    hint = (task_hint or "").strip().lower()
    lite_max = int(thresholds.get("lite_max_chars", 1500))
    std_max = int(thresholds.get("standard_max_chars", 12000))

    if hint in ("code", "coding", "debug", "refactor"):
        return TaskBucket.STANDARD if len(text) < 12_000 else TaskBucket.HEAVY
    if hint in ("analysis", "analytics", "report"):
        return TaskBucket.STANDARD if len(text) < 20_000 else TaskBucket.HEAVY
    if hint in ("agent", "orchestration", "multi_step", "multistep"):
        return TaskBucket.HEAVY

    n = len(text)
    if n == 0:
        return TaskBucket.LITE
    if _AGENTIC_HINT.search(text):
        return TaskBucket.HEAVY
    if _CODE_HINT.search(text):
        return TaskBucket.STANDARD if n < 14_000 else TaskBucket.HEAVY
    if _ANALYSIS_HINT.search(text):
        return TaskBucket.STANDARD if n < 24_000 else TaskBucket.HEAVY
    if n < lite_max:
        return TaskBucket.LITE
    if n < std_max:
        return TaskBucket.STANDARD
    return TaskBucket.HEAVY


def bucket_for_openai_messages(
    messages: list[dict[str, Any]],
    task_hint: str | None,
    thresholds: Mapping[str, Any],
) -> TaskBucket:
    """Use the last user message as the routing surface."""
    prompt = ""
    for m in reversed(messages):
        if (m.get("role") or "").lower() == "user":
            prompt = str(m.get("content", ""))
            break
    return classify_prompt(prompt, task_hint, thresholds)
