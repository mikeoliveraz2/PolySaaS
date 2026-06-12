# BINGO — Mattermost One-Way PolySaaS Theme Sync

**Date:** 2026-06-13  
**Declared by:** Michael  
**Commit:** _(recorded in follow-up hash commit)_  
**Baseline:** BINGO `09c5587b` — Gemini AQ keys + Copilot errors (2026-06-12 EOD)  
**Test tenant:** PolySaaS Test 152 (`polysast152`)  
**Test URL:** `http://localhost:8000/pt/admin/polysaas-mattermost.onrender.com/`

---

## What Was Achieved

When a subscriber toggles PolySaaS admin **light/dark** (Jazzmin `display_mode`), the **next** Mattermost passthrough open applies a matching Mattermost theme. One-way only — Mattermost theme changes do not alter PolySaaS.

### Certified behaviors

| Feature | Status |
|---------|--------|
| PolySaaS light → Mattermost classic light theme on passthrough open | ✓ |
| PolySaaS dark → Mattermost Onyx-style dark theme on passthrough open | ✓ |
| Sync only when `display_mode` changed since last MM sync (session key) | ✓ |
| Mattermost OS theme sync disabled (`enable_theme_sync=false`) | ✓ |
| Uses tenant MM token + `mm_user_id` (or `/users/me`) — per-user, not global | ✓ |
| Handler-only logic in `MattermostPassthroughHandler` (no forwarder changes) | ✓ |

---

## How It Works

```
PolySaaS admin: Toggle light/dark
    → display_mode cookie + session updated

User opens Mattermost passthrough (sidebar)
    → MattermostPassthroughHandler._inject_client_shim()
    → _polysaas_display_mode(request)  (same rules as Odoo handler)
    → if session polysaas_mm_theme_sync_mode != display_mode:
         PUT /api/v4/users/{id}/preferences  (theme JSON)
         session polysaas_mm_theme_sync_mode = display_mode
    → Mattermost SPA loads with updated user theme
```

---

## Files in This BINGO

| File | Change |
|------|--------|
| `dose/passthrough/handlers/mattermost_handler.py` | `_polysaas_display_mode`, `_sync_polysaas_theme_to_mattermost`, call on shim inject |
| `dose/passthrough/handlers/mm_theme_presets.py` | Built-in light/dark theme JSON presets |
| `dose/passthrough/handlers/mattermost_handler.py.bak-theme-sync` | Backup before edit |

---

## Verification Steps

1. `.\runall`
2. Log in to a test tenant admin
3. Set PolySaaS to **dark** (top bar Toggle light/dark)
4. Open **Mattermost** from passthrough sidebar — UI should be dark
5. Set PolySaaS to **light**, open Mattermost again — UI should be light
6. Server log: `[MM THEME] synced Mattermost theme to PolySaaS mode=dark` (or `light`)

---

## Out of Scope (by design)

- Mattermost → PolySaaS theme sync (reverse direction)
- Live sync while Mattermost tab stays open without re-navigation
- Bootswatch palette name sync (only light vs dark mode, not Sandstone vs Darkly colors)
