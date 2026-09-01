<!-- SUPERSEDED — see documentation/BINGO_NEXTCLOUD_JAZZMIN_PANEL_NO_IFRAME_2026-08-13.md -->

> **SUPERSEDED (2026-09-01).** This BINGO certified an iframe passthrough route
> that was **retired on 2026-08-13** by
> `BINGO_NEXTCLOUD_JAZZMIN_PANEL_NO_IFRAME_2026-08-13.md`. Iframes are now
> prohibited by `.cursor/rules/passthrough-no-iframes.mdc`. This document reads
> as current but is not. Retained as history — do not restore this design.

# BINGO — PolySniffer 2.0 Passthrough Workspace Iframe

**Date:** 2026-06-24  
**Declared by:** Michael  
**Commit:** `04e0a381`  
**Builds on:** PolySniffer 2.0 native login workspace (`24ce8dfa`)

---

## What Was Achieved

PolySniffer passthrough mode in the split workspace left iframe loads Mattermost (and production passthrough chain) reliably — same behavior as opening passthrough in a top-level tab.

| Area | Behavior |
|------|----------|
| **Root cause (Windows)** | `pt_admin_generic_passthrough_view` crashed on emoji `print` + `/tmp/odoo_view_debug.log` → 500 blank iframe |
| **Root cause (iframe)** | Mattermost handler redirected to `/pt/admin/{trigger}/` (not iframe-exempt); workspace also stale-loaded `/dose/sniff/…/passthrough/` on active session |
| **New public prefix** | `/pt/polysniff/{endpoint_id}/` — iframe-safe; rewrites redirects + shim `PROXY_PREFIX` away from `/pt/admin/` |
| **Middleware** | `/pt/polysniff/` bypasses `ExternalPassthroughMiddleware` (was treating endpoint id as hostname → 503) |
| **Workspace UI** | Passthrough browse URL + autostart on active session use `/pt/polysniff/{id}/` |

---

## Certified behaviors

| Feature | Status |
|---------|--------|
| Direct tab: `/pt/polysniff/4/` loads Mattermost passthrough (polysaaspp5) | ✓ |
| Workspace passthrough left iframe matches direct tab content | ✓ |
| Redirect stays on `/pt/polysniff/4/?mm_cleared=1` (not `/pt/admin/…`) | ✓ |
| `xframe_options_exempt` on polysniff passthrough responses | ✓ |
| Live capture poll receives passthrough traffic (count > 0 after browse) | ✓ |
| Production sidebar `/pt/admin/{trigger}/` unchanged | ✓ |

---

## Root causes fixed

1. **Windows 500 in passthrough view** — `UnicodeEncodeError` on emoji debug print and `FileNotFoundError` on `/tmp/odoo_view_debug.log`. Replaced with `logger.info()`.

2. **Iframe escape to `/pt/admin/`** — Handler root flow issued redirects with admin prefix; iframe blocked or showed broken page. New `/pt/polysniff/` route rewrites `Location` and HTML/shim paths back to polysniff prefix.

3. **Stale workspace iframe src** — Server rendered `/dose/sniff/{id}/passthrough/` on active session; autostart skipped `setModeUI()` when already recording. Fixed server `proxy_url` and DOMContentLoaded refresh.

---

## Files in this BINGO

| File | Role |
|------|------|
| `dose/polysniffer/sniff_pt_proxy.py` | Dispatch + response rewrite for polysniff prefix |
| `dose/polysniffer/pt_polysniff_urls.py` | URLconf for `/pt/polysniff/{id}/` |
| `mysite/urls.py` | Mount polysniff routes |
| `dose/passthrough/middleware.py` | Delegate `/pt/polysniff/` to URLconf |
| `dose/admin_views.py` | Remove Windows-crashing debug I/O in passthrough view |
| `dose/polysniffer/views/sniff_v2.py` | Shared dispatch via sniff_pt_proxy |
| `dose/polysniffer/views/sniff_v2_workspace.py` | Passthrough `proxy_url` → `/pt/polysniff/` |
| `dose/templates/polysniffer/sniff_workspace.html` | Iframe browse URL + active-session refresh |

---

## Operator checklist

1. Restart: `.\runall.ps1`
2. Log in as provisioned tenant user (e.g. **polysaaspp5**)
3. Admin → PassThrough Endpoints → PolySniffer 2.0 workspace → **Start passthrough**
4. Left pane loads Mattermost; right pane capture count increases
5. Direct sanity: `http://localhost:8000/pt/polysniff/4/`

---

## Known limits

- Static assets still use `/pt/admin/{trigger}/static/` upstream proxy (by design)
- Passthrough sniff legacy path `/dose/sniff/{id}/passthrough/` still works via same rewrite layer
- Native mode unchanged (`/dose/sniff/{id}/native/login/`)
