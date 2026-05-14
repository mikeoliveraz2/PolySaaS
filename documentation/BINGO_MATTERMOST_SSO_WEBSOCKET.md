# BINGO — Mattermost SSO + WebSocket Fix

**Date**: 2026-05-13  
**Status**: ✅ COMPLETE  
**Branch**: `fix/mattermost-sso-restore` → merged to `main`

---

## Result
- Straight in — no login form, no loop
- Full Town Square channels view renders
- No red "Mattermost unreachable / check WebSocket port" banner
- Modals (About Mattermost, etc.) work inside the embed

---

## Root Causes Fixed

### 1. Broken `mattermost_handler.py` (from origin/main debug session)
- Auto-submit was commented out → login bridge never submitted
- False-positive bounce detector (`MM_LOGIN_TS` in sessionStorage) blocked login within 60s
- Aggressive token clearing caused the infinite loop
- **Fix**: Restored `mattermost_handler.py` from checkpoint commit `6664558`

### 2. WebSocket routed through WSGI proxy
- The client shim's `WebSocket` interceptor was rewriting all `wss://` URLs to go through the PolySaaS proxy (`u.hostname = location.hostname`)
- WSGI cannot handle WebSocket protocol upgrades → "Mattermost unreachable" red banner
- **Fix**: Changed shim to route WebSocket directly to the upstream Mattermost server (`B = base_origin = https://polysaas-mattermost.onrender.com`)

### 3. Aggressive CSS containment in `passthrough_embed.html`
- 129 lines of Mattermost-specific CSS (added during debug session on origin/main)
- `contain: layout style` + `transform: translateZ(0)` created new containing block
- Mattermost SPA rendered but its main channel view was hidden/zero-sized
- **Fix**: Restored `passthrough_embed.html` from checkpoint

### 4. Render env vars added
- `MM_SERVICESETTINGS_WEBSOCKETURL = wss://polysaas-mattermost.onrender.com`
- `MM_SERVICESETTINGS_ALLOWCORSFROM = *`
- `MM_SERVICESETTINGS_CORSALLOWCREDENTIALS = true`

---

## Files Changed
| File | Change |
|------|--------|
| `dose/passthrough/handlers/mattermost_handler.py` | Restored from checkpoint; WebSocket shim fixed to route direct |
| `dose/templates/admin/passthrough_embed.html` | Restored from checkpoint; removed 129 lines of broken CSS |
| `render.yaml` | Added WebSocket URL + CORS env vars for Mattermost service |

---

## Follow-ups
| Priority | Task |
|----------|------|
| 1 | Set env vars on Render Mattermost service + redeploy (already done manually) |
| 2 | `polysaasot` tenant — store PAT `condotest` in TenantApp extra_config for server-side SSO |
| 3 | Nextcloud SSO — apply same server-side pattern |
| 4 | Merge `fix/mattermost-sso-restore` → `main` ✅ done |
