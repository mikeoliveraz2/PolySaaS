"""
Rule-based task classification for routing (Option 1).

No ML model here — length + keyword heuristics. Extend with embeddings or
a classifier model later without changing the public ``classify()`` signature.
"""

from __future__ import annotations

import enum
import re


class TaskBucket(enum.Enum):
    """Coarse buckets mapped to (provider, model) tiers in config."""

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


def classify(*, prompt: str, task_hint: str | None = None) -> TaskBucket:
    """
    Classify user prompt (+ optional caller hint) into lite / standard / heavy.

    ``task_hint`` may be values like ``code``, ``analysis``, ``chat`` from
    orchestration or Peers — treated as soft signals only.
    """
    text = (prompt or "").strip()
    hint = (task_hint or "").strip().lower()

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

    if n < 1_500:
        return TaskBucket.LITE
    if n < 12_000:
        return TaskBucket.STANDARD
    return TaskBucket.HEAVY
