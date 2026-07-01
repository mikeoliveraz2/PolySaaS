# HubSpot Passthrough — Code Review Handoff for Shela

**Date:** 2026-06-27  
**From:** Michael (via Cursor session)  
**Status:** Uncommitted local changes — not BINGO, not pushed

---

## What we were trying to fix

PolySniffer workspace **passthrough** for HubSpot (endpoint 4, `app-na2.hubspot.com`) loads login HTML successfully (~46KB, HTTP 200), but HubSpot’s LoginUI SPA shows:

> **This login URL is invalid.**

Server HTML does **not** contain that text — it is injected client-side after LoginUI boots.

---

## What changed (this session)

| File | Change |
|------|--------|
| `dose/passthrough/handlers/hubspot_handler.py` | Location spoof IIFE, workspace hook, shim uses `__PS_REAL_ORIGIN`, session landing helpers |
| `dose/polysniffer/sniff_pt_embed.py` | Guard `replaceState`; inject handler spoof script after guard |
| `dose/polysniffer/sniff_session.py` | `session_stop` also clears `polysniffer_ep{id}_mode` |
| `dose/templates/polysniffer/sniff_workspace.html` | Stop capture UI fix; open-in-new-tab → `/pt/polysniff/4/login/`; click interceptor |
| `dose/polysniffer/handlers/hubspot_bases.py` | Session landing path, global `/login/` entry (supporting) |
| `dose/polysniffer/handler_hooks.py` | Handler hook for browse subpath |
| `dose/polysniffer/views/sniff_v2_workspace.py` | Workspace redirect / login slash |

---

## How to review (no repo access needed)

This folder is self-contained. Email **`shela_review_hubspot_2026-06-27.zip`** from `documentation/` on the office machine.

```
shela_review_hubspot_2026-06-27/
  README.md                          ← this file
  HUBSPOT_PASSTHROUGH_SESSION.patch   ← unified diff (optional)
  source/                            ← current changed files (full text)
    hubspot_handler.py
    sniff_pt_embed.py
    sniff_session.py
    sniff_workspace.html
  before/                            ← backups immediately before edits
    hubspot_handler.py
    sniff_pt_embed.py
    sniff_session.py
    sniff_workspace.html
```

Compare `before/` vs `source/` side by side, or read the `.patch` file in any text editor.

---

## Architecture (execution order)

**Workspace passthrough inline embed:**

1. Page `<head>`: `build_workspace_shell_guard_script` (replaceState → `/pt/polysniff/4/login/`)
2. Page `<head>`: `polysniffer_workspace_location_spoof_script` (patches `location`, `document.URL`)
3. Body: HubSpot HTML + `get_client_side_shim` (fetch/XHR rewrite; re-applies spoof if flag set)

**Standalone `/pt/polysniff/4/login/` (Open in new tab):**

- Gets shim from `process_html_response` only
- Does **not** currently get the location spoof IIFE (workspace hook only)
- Same invalid-login error observed — likely needs spoof in `get_client_side_shim` too

---

## Analysis notes for review

1. **LoginUI bundle** (`LoginUI/.../project.js`): error string maps to `MISSING_FRAGMENTS` — may be OAuth hash-fragment routing, not only pathname.
2. **Location spoof** may be necessary but not sufficient.
3. **Stop capture** fix: clearing session mode prevents auto `startSession('passthrough')` on reload — confirmed working.
4. **Captured: 0** — separate FK issue (`olientAdmin` not in tenant `auth_user`).

**DevTools check:** console should show  
`[PolySaaS HS] location spoof https://app-na2.hubspot.com/login/ real=...`  
If missing, spoof script did not run or server was not restarted.

---

## Suggested next step (not implemented)

Inject `_hubspot_location_spoof_iife` at the **start** of `get_client_side_shim()` so standalone `/pt/polysniff/` pages get the same spoof as the workspace embed.

---

## Related docs

- `documentation/HUBSPOT_POLYSNIFFER_2026-06-26.md`
- `documentation/HUBSPOT_PASSTHROUGH_SNIFF_NOTES.md`
- `.cursor/rules/mattermost-passthrough-no-team.mdc` (HubSpot is separate — no team logic)
