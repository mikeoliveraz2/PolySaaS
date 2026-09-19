#!/usr/bin/env python3
"""Validate the shared PolySaaS agent sync contract.

This script is intentionally strict: all AI agents (Copilot, Cursor, Windsurf)
should read the same repo-level rules and handoff files before making changes.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent

REQUIRED = {
    "AGENTS.md": [
        "Startup sync: read first",
        "EOD handoff rule",
        "Daily startup rule",
        "shared source of truth",
    ],
    ".github/copilot-instructions.md": [
        "Always read first",
        "EOD requirement",
        "No iframe-based passthrough by default",
    ],
    "documentation/ACTIVE_HANDOFF.md": [
        "Active Handoff",
        "This file is the canonical startup and end-of-day handoff",
        "Every agent",
    ],
    ".cursor/rules/process-rules.mdc": [
        "Rule 0 — Startup Read + Handoff First",
        "Rule 1 — End-of-Day Handoff Requirement",
        "No Unilateral Changes",
    ],
    ".cursor/rules/passthrough-no-iframes.mdc": [
        "Do NOT use iframes for passthrough by default",
        "Never suggest iframes as the easy default",
    ],
    ".windsurf/workflows/push.md": [
        "Startup checks (read before work)",
        "EOD requirement",
        "No iframe-based passthrough by default",
    ],
}


def check_file(path: str, expected: list[str]) -> None:
    file_path = REPO / path
    if not file_path.exists():
        raise FileNotFoundError(f"Missing required file: {path}")
    content = file_path.read_text(encoding="utf-8")
    missing = [text for text in expected if text not in content]
    if missing:
        raise ValueError(
            f"{path} is out of sync; missing required phrases: {', '.join(missing)}"
        )


def main() -> int:
    errors: list[str] = []
    for path, phrases in REQUIRED.items():
        try:
            check_file(path, phrases)
        except Exception as exc:  # noqa: BLE001
            errors.append(str(exc))

    if errors:
        print("Agent sync validation failed:", file=sys.stderr)
        for err in errors:
            print(f"- {err}", file=sys.stderr)
        print("\nFix the shared rule files before continuing.", file=sys.stderr)
        return 1

    print("Agent sync validation passed: repo policy files are aligned.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
