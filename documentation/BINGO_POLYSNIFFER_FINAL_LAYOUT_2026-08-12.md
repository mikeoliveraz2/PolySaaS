# BINGO — PolySniffer Workspace Final Layout

**Date:** 2026-08-12  
**Declared by:** Michael  
**Commit:** `TBD`  
**Replaces:** stacked top-line title, mode-card titles above descriptions, fragmented JS error handling

---

## What Was Achieved

The PolySniffer capture workspace is now a single-pane, demo-ready layout with the Mattermost SPA loading cleanly after login in the embedded `<object>` pane.

| Area | Change |
|------|--------|
| **Top line** | `PolySniffer` title and endpoint meta (`Mattermost - localhost:8065`) are now on one line |
| **Mode cards** | `Native` / `Passthrough` `<h3>` labels removed; each card now shows the action button on the left with its description flowing to the right |
| **Browser pane** | `<object>` embed with placeholder, no auto-load, CSP headers stripped, no iframe use |
| **Token storage** | `store-mm-token` now returns JSON instead of 500 HTML; uses `bind_request_tenant` and `@csrf_exempt` |
| **Ingest** | Client-capture shim POSTs to the correct `/admin/polysniffer/sniff/<id>/workspace/ingest/` route and is CSRF-exempt |
| **Polling** | `workspace/poll` is wrapped so schema/tenant errors return a graceful empty-capture JSON response instead of 500 HTML |
| **Mattermost shim** | `querySelector` colon-escaping patch removes the red SyntaxError banner |

---

## Certified behaviors

| Feature | Status |
|---------|--------|
| `PolySniffer` title + endpoint meta on one topbar line | ✓ |
| `Start Native` and `Start Passthrough` buttons without separate labels | ✓ |
| Descriptions to the right of each mode button | ✓ |
| Mattermost SPA renders in `<object>` after login | ✓ |
| No red `querySelector` SyntaxError banner | ✓ |
| `store-mm-token` responds with JSON, no 500 HTML | ✓ |
| `workspace/poll` no longer serves 500 HTML on schema/tenant issues | ✓ |
| `ingest` endpoint returns JSON, no 404/403 from `sendBeacon` | ✓ |
| `python manage.py check` clean | ✓ |

---

## Screenshot

![PolySniffer final layout](assets/BINGO_POLYSNIFFER_FINAL_LAYOUT_2026-08-12_workspace.png)

*(Drop the final-layout screenshot as `documentation/assets/BINGO_POLYSNIFFER_FINAL_LAYOUT_2026-08-12_workspace.png` if it is not already present.)*

---

## Files in this commit

| File | Role |
|------|------|
| `dose/templates/polysniffer/sniff_workspace.html` | Topbar, mode-card layout, `<object>` pane, token JS, placeholder |
| `dose/polysniffer/views/sniff_v2_workspace.py` | `store_mm_token`, `workspace_ingest`, `workspace_poll` hardening |
| `dose/polysniffer/sniff_urls.py` | `workspace_ingest` route registration |
| `dose/polysniffer/sniff_pt_proxy.py` | Correct `INGEST` URL for client-capture shim |
| `dose/polysniffer/workspace_client_capture.py` | Correct `INGEST` URL for native client-capture shim |
| `dose/passthrough/handlers/mattermost_handler.py` | `querySelector` colon-escape patch, token/cookie fallback |

---

## Operator checklist

1. Restart: `.\runall.ps1`
2. Admin → PassThrough Endpoints → open the PolySniffer workspace
3. Confirm top line reads `PolySniffer Mattermost - localhost:8065` on one line
4. Confirm the two mode cards show `Start Native` / `Start Passthrough` buttons with descriptions to the right
5. Start **Passthrough** → log in to Mattermost → confirm Town Square renders without a red JS banner
6. Confirm no `ingest` 404 or `store-mm-token` 500 in the browser console

```powershell
python manage.py check
```

---

## Known limits

- The screenshot asset must be placed at `documentation/assets/BINGO_POLYSNIFFER_FINAL_LAYOUT_2026-08-12_workspace.png` for the image in this doc to render.
- Final layout is fixed for the current two-column PolySniffer workspace; further UI changes should extend `sniff_workspace.html`.
