# PolySniffer Session — HubSpot native inline workspace

**Date:** 2026-06-25  
**Owner:** Michael  
**Status:** WIP (not BINGO) — inline native left panel landed; full HAR parity triangle still to verify

---

## Goal

HubSpot PolySniffer 2.0 HAR parity triangle for endpoint **4** (`app-na2.hubspot.com`):

| Leg | Route |
|-----|--------|
| Direct | Browser → upstream |
| Native sniff | `/dose/sniff/4/workspace/...` — **inline** left panel (no nested browse iframe) |
| Passthrough | `/pt/polysniff/4/` — full orchestration in left iframe |

Baseline page: `/global-home/246571499`

---

## What shipped this session

### 1. HubSpot native CDN fix

Protocol-relative CDN URLs (`//static.hsappstatic.net/...`) were incorrectly prefixed with the sniff proxy path → 404 on `app-na2.hubspot.com`.

- **`dose/polysniffer/handlers/hubspot_native_sniff.py`** — rewrite CDN to `https://`, proxy app paths; patch upstream resolver for mistaken CDN-via-proxy paths
- Registered from **`hubspot_handler.py`** and **`sniff_forward.py`**

### 2. Native inline workspace (left panel)

Replaced broken left **browse iframe** with **inline** HubSpot HTML in the workspace shell.

| Piece | Role |
|-------|------|
| `sniff_native_embed.py` | `build_inline_native_embed_context()`, `wrap_native_sniff_for_workspace()` |
| `sniff_native_embed.html` | Minimal embed shell (standalone `/workspace/browse/` still supported) |
| `sniff_v2_workspace.py` | `workspace_dispatch` — HTML → shell; API/assets → transparent proxy |
| `sniff_workspace.html` | Native = `#native-inline`; passthrough = left iframe; capture = right iframe |
| `sniff_native_rewrite.py` | `sniff_native_proxy_prefix()` recognizes `/workspace` and `/workspace/browse` |

**URLs**

- Shell (page nav, inline): `/dose/sniff/<id>/workspace/<path>`
- Proxy (API/assets): `/dose/sniff/<id>/workspace/browse/<path>` or `/workspace/api/...` via dispatch
- Start native → redirect to `/workspace/global-home/246571499`

Template marker: HTML comment `native-inline-v2` in `sniff_workspace.html`.

### 3. Client-side capture ingest

- **`workspace_client_capture.py`** — fetch/XHR shim → `POST /workspace/ingest/`
- Injected into native HTML (HubSpot processor) and passthrough (`sniff_pt_proxy.py`)
- **`workspace_ingest`** uses session mode for `capture_source` (not hardcoded passthrough)
- Capture panel: newest-at-top backfill + dedupe in `sniff_workspace_capture.html`

### 4. Dual mode picker restored

Native vs passthrough on workspace; passthrough keeps production chain for orchestration HAR leg.

---

## Operator notes

1. Restart after pull: `.\runall.ps1`
2. Hard refresh workspace (Ctrl+Shift+R)
3. **Stop capture** → **Start native** → should land on `/workspace/global-home/246571499` with **Browse — native inline** header
4. Right panel: green capture iframe (unchanged)
5. Passthrough: left iframe to `/pt/polysniff/4/`

---

## Still open

- [ ] Confirm HubSpot SPA boots inline (POST `/api/crm/...` in capture, not just repeated GETs)
- [ ] Run `scripts/compare_hubspot_har_parity.py` with direct + native + passthrough HARs
- [ ] BINGO when Michael certifies all three legs

---

## Files touched (this commit)

| File | Notes |
|------|--------|
| `handlers/hubspot_native_sniff.py` | New — HubSpot native rewrites |
| `sniff_native_embed.py` | New — inline + iframe embed helpers |
| `workspace_client_capture.py` | New — client ingest shim |
| `sniff_v2_workspace.py` | Inline shell, dispatch, redirect |
| `sniff_urls.py` | `workspace_dispatch` route |
| `sniff_workspace.html` | Inline native UI |
| `sniff_native_embed.html` | Standalone embed document |
| `sniff_workspace_capture.html` | Poll/dedupe/mode hints |
| `sniff_native_rewrite.py` | Workspace proxy prefix |
| `sniff_forward.py` | HubSpot module import |
| `sniff_pt_proxy.py` | Passthrough client capture inject |
| `hubspot_handler.py` | Register native processor |
| `scripts/compare_hubspot_har_parity.py` | HAR triangle helper |

All `.bak` copies alongside edited sources are included per project backup rule.
