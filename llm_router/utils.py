"""Small helpers for the LLM router (logging safety, size hints)."""

from __future__ import annotations


def prompt_char_len(prompt: str | None) -> int:
    if not prompt:
        return 0
    return len(prompt)


def safe_prompt_fragment(prompt: str | None, max_chars: int) -> str:
    if not prompt:
        return ""
    s = prompt.replace("\r\n", "\n").strip()
    if len(s) <= max_chars:
        return s
    return s[: max_chars - 3] + "..."
