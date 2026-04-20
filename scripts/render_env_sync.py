#!/usr/bin/env python3
"""
Generate Render env checklists and paste-friendly blocks from scripts/env-master.json.

Sensitive values stay as placeholders in the committed template; use env-master.local.json
(optional, gitignored) to hold real values locally without committing them.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


SCRIPT_DIR = Path(__file__).resolve().parent
DEFAULT_MASTER = SCRIPT_DIR / "env-master.json"
LOCAL_OVERLAY = SCRIPT_DIR / "env-master.local.json"


def deep_merge(base: dict[str, Any], overlay: dict[str, Any]) -> dict[str, Any]:
    out = dict(base)
    for k, v in overlay.items():
        if k in out and isinstance(out[k], dict) and isinstance(v, dict):
            out[k] = deep_merge(out[k], v)
        else:
            out[k] = v
    return out


def load_master(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if LOCAL_OVERLAY.exists():
        local = json.loads(LOCAL_OVERLAY.read_text(encoding="utf-8"))
        data = deep_merge(data, local)
    return data


def merge_group_vars(master: dict[str, Any], group_names: list[str]) -> dict[str, str]:
    groups = master.get("envVarGroups", {})
    merged: dict[str, str] = {}
    for name in group_names:
        block = groups.get(name)
        if not isinstance(block, dict):
            continue
        for key, val in block.items():
            if key.startswith("_"):
                continue
            merged[key] = "" if val is None else str(val)
    return merged


def service_effective_env(master: dict[str, Any], service_name: str) -> dict[str, str]:
    svc = master.get("services", {}).get(service_name)
    if not isinstance(svc, dict):
        raise KeyError(f"Unknown service: {service_name}")
    from_groups = svc.get("fromGroups") or []
    env = merge_group_vars(master, list(from_groups))
    overrides = svc.get("overrides") or {}
    for k, v in overrides.items():
        env[k] = "" if v is None else str(v)
    return env


def is_sensitive_placeholder(value: str) -> bool:
    v = value.upper()
    return "FILL" in v or "SECRET" in v or "PASSWORD" in v or "TOKEN" in v or "KEY" in v


def md_escape(s: str) -> str:
    return s.replace("|", "\\|").replace("\n", " ")


def render_group_section(master: dict[str, Any]) -> str:
    lines: list[str] = []
    lines.append("## Environment groups (Render: Environment Groups)\n")
    lines.append(
        "Set these once per **group**, then link groups to services (`fromGroup` in `render.yaml`).\n"
    )
    for group_name, vars_dict in master.get("envVarGroups", {}).items():
        if not isinstance(vars_dict, dict):
            continue
        lines.append(f"### `{group_name}`\n")
        for key in sorted(vars_dict.keys()):
            if key.startswith("_"):
                continue
            val = str(vars_dict[key])
            pending = "[ ]" if is_sensitive_placeholder(val) or val == "" else "[x]"
            lines.append(f"- {pending} `{key}` - `{md_escape(val)}`\n")
        lines.append("\n**Paste block (Key = one line; paste into notes or split for Render UI):**\n")
        lines.append("```\n")
        for key in sorted(vars_dict.keys()):
            if key.startswith("_"):
                continue
            lines.append(f"{key}={vars_dict[key]}\n")
        lines.append("```\n\n")
    return "".join(lines)


def render_service_section(master: dict[str, Any], name: str) -> str:
    svc = master["services"][name]
    lines: list[str] = []
    lines.append(f"## Service: `{name}`\n")
    fg = svc.get("fromGroups") or []
    if fg:
        lines.append(f"- **fromGroup:** {', '.join(f'`{g}`' for g in fg)}\n")
    notes = svc.get("notes")
    if notes:
        lines.append(f"- **Notes:** {notes}\n")
    injected = svc.get("renderInjectedFromDatabase") or []
    if injected:
        lines.append(
            f"- **Render / Blueprint managed (do not paste manually):** "
            f"{', '.join(f'`{k}`' for k in injected)}\n"
        )
    lines.append("\n### Checklist (effective env after groups + overrides)\n")
    eff = service_effective_env(master, name)
    for key in sorted(eff.keys()):
        val = eff[key]
        pending = "[ ]" if is_sensitive_placeholder(val) or val == "" else "[x]"
        lines.append(f"- {pending} `{key}`\n")
    lines.append("\n### Paste block (.env style; prefer env groups in production)\n")
    lines.append("```\n")
    for key in sorted(eff.keys()):
        lines.append(f"{key}={eff[key]}\n")
    lines.append("```\n\n")
    return "".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--master",
        type=Path,
        default=DEFAULT_MASTER,
        help=f"Path to env-master.json (default: {DEFAULT_MASTER})",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        default=None,
        help="Write markdown to this file instead of stdout",
    )
    parser.add_argument(
        "--service",
        action="append",
        default=None,
        help="Only emit sections for this service (repeatable). Default: all services in master.",
    )
    args = parser.parse_args()

    if not args.master.exists():
        print(f"Missing master file: {args.master}", file=sys.stderr)
        return 1

    master = load_master(args.master)
    chunks: list[str] = []
    chunks.append("# Render environment checklist\n\n")
    chunks.append(
        "_Generated by `scripts/render_env_sync.py`. Do not commit files containing real secrets._\n\n"
    )
    if LOCAL_OVERLAY.exists():
        chunks.append(f"_Merged overlay: `{LOCAL_OVERLAY.name}`_\n\n")

    chunks.append(render_group_section(master))

    service_names = list(master.get("services", {}).keys())
    if args.service:
        service_names = [s for s in args.service if s in master.get("services", {})]
        missing = set(args.service) - set(service_names)
        if missing:
            print(f"Unknown --service: {missing}", file=sys.stderr)
            return 1

    for name in service_names:
        chunks.append(render_service_section(master, name))

    text = "".join(chunks)
    if args.output:
        args.output.write_text(text, encoding="utf-8")
        print(f"Wrote {args.output}", file=sys.stderr)
    else:
        sys.stdout.write(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
