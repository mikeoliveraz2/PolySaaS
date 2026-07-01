"""One-off: regenerate HUBSPOT_PASSTHROUGH_SOURCE_FOR_SHELA.md with full sources."""
from pathlib import Path

root = Path(__file__).resolve().parents[1]
out = root / "documentation" / "HUBSPOT_PASSTHROUGH_SOURCE_FOR_SHELA.md"

files = [
    ("dose/passthrough/handlers/hubspot_handler.py", "python"),
    ("dose/polysniffer/sniff_pt_embed.py", "python"),
    ("dose/polysniffer/sniff_session.py", "python"),
    ("dose/templates/polysniffer/sniff_workspace.html", "html"),
]

intro = """# HubSpot Passthrough — Full Source for Shela

**Date:** 2026-06-27  
**From:** Michael  
**Status:** Uncommitted local changes (weekend review — no repo access needed)

---

## Problem

PolySniffer passthrough for HubSpot (endpoint 4, `app-na2.hubspot.com`) loads login HTML (~46KB, HTTP 200) but HubSpot LoginUI shows:

> **This login URL is invalid.**

That text is **not** in the server HTML — LoginUI injects it client-side. LoginUI bundle maps it to error code `MISSING_FRAGMENTS` (OAuth hash-fragment routing).

## What works now

- **Stop capture** — clears session mode; no auto-restart loop
- **Open in new tab** — opens `/pt/polysniff/4/login/` (raw passthrough, not workspace shell)

## Still broken

- HubSpot login form in workspace embed and in new tab (same error)
- Location spoof runs in **workspace embed only** (not yet in standalone `/pt/polysniff/` pages)

## Script execution order (workspace passthrough)

1. `sniff_pt_embed.build_workspace_shell_guard_script` — `history.replaceState` to `/pt/polysniff/4/login/`
2. `HubspotPassthroughHandler.polysniffer_workspace_location_spoof_script` — patches `location`, `document.URL`
3. HubSpot HTML + `get_client_side_shim` — fetch/XHR rewrite; re-applies spoof if flag set

## Suggested next fix

Inject `_hubspot_location_spoof_iife` at the start of `get_client_side_shim()` so `/pt/polysniff/4/login/` gets the same spoof.

---

"""

parts = [intro]
for i, (rel, lang) in enumerate(files, start=1):
    name = Path(rel).name
    parts.append(f"## File {i} of 4: {name}\n\nRepo path: `{rel}`\n\n")
    text = (root / rel).read_text(encoding="utf-8")
    parts.append(f"```{lang}\n{text}\n```\n\n")

out.write_text("".join(parts), encoding="utf-8")
print(f"Wrote {out} ({round(out.stat().st_size / 1024, 1)} KB)")
