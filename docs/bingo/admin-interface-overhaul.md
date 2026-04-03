# BINGO — Admin Interface Overhaul
**Date:** 2026-04-03  
**Tested by:** olientAdmin (Oliver Enterprises tenant)  
**Status:** ✅ COMPLETE — All items below confirmed working in browser

---

## What Was Fixed

### 1. Template Single-Source-of-Truth
- Deleted the shadowed `templates/admin/base_site.html` and `templates/admin/includes/custom_sidebar.html` stubs
- `dose/templates/admin/` is now the sole authoritative location
- Added Cursor rule `admin-templates-locked.mdc` to enforce this permanently
- **Commits:** `b668acf`, `e646660`

### 2. Company Name / Tenant Display in Navbar
- Navbar badge now shows the current tenant name and logged-in username dynamically (e.g. "OLIVER ENTERPRISES – OLIENTADMIN")
- Replaced hardcoded "Oliver Enterprises" with `{{ request.tenant.name }}`
- **Commit:** `d3c4797`

### 3. Google OAuth2 Tenant Selection
- `CustomAccountAdapter` (dose/account_adapter.py) detects post-OAuth login
- If user belongs to multiple tenants: redirected to `/dose/select-tenant/`
- If user belongs to one tenant: auto-selected, session set
- **Files:** `dose/account_adapter.py`, `dose/views/main.py`, `dose/templates/dose/select_tenant.html`

### 4. Light/Dark Theme Toggle
- Theme picker modal in navbar (Paint icon)
- Saves light/dark preference to `UserProfile` via `/admin/select-theme/api/`
- On page load, inline `<script>` in `{% block extrahead %}` swaps the Jazzmin theme `<link>` href to the user's selected Bootswatch theme before render — no flash of wrong theme
- **Commit:** `0d772bf`, `62a99a6`

### 5. Dark Mode Navbar Readability
- Injected `<style id="ps-dark-navbar">` dynamically when a dark theme is active
- Targets `#jazzy-navbar *`, `.usermenu`, `.user-panel`, and all dropdown elements — forces white text (`#f8f9fa`) on dark background (`#343a40`)
- Tenant badge container background is now theme-aware: dark grey in dark themes, light grey in light themes
- **Commits:** `069bd5d`, `65bc032`, `8cb3fd6`

### 6. Three-Column Admin Layout
- Left: collapsible PolySaaS navigation sidebar (280px, sticky)
- Center: Django admin content area — **two columns** via Jazzmin's native `col-md-6` Bootstrap split
- Right: Recent Actions activity sidebar (320px, sticky)
- **Grid:** `.admin-content-grid { grid-template-columns: 280px 1fr 320px; }`
- **Commits:** `9d69612`, `0841a9c`

### 7. Responsive Collapse Below 900px
- At `max-width: 899px`: left nav and right activity sidebar hidden, content collapses to single full-width column
- `col-md-6` override applied only in the media query so Jazzmin's 2-col layout is preserved at ≥ 900px
- **Commit:** `0841a9c`

### 8. Artifact Elimination
- Removed stray `{% block nav-global %}` reference from comment header (caused `TemplateSyntaxError`)
- Converted all multi-line `{# #}` comments to single-line to prevent Django tokenizer leakage
- **Commit:** `c7aed91`, `62a99a6`

---

## Layout Confirmation (screenshot 2026-04-03)
```
┌─────────────────────────────────────────────────────────────────────────┐
│  PolySaaS  Home  Support  Toggle light/dark  API Docs  [TENANT-USER]   │
├──────────────┬───────────────────────┬───────────────┬──────────────────┤
│ Navigation   │ Accounts              │ Djstripe      │ Recent Actions   │
│ Bar          │ AI Parameters         │ Accounts      │                  │
│              │ Authentication...     │ Active ent.   │ 1 mo 2 wks ago   │
│ PASSTHROUGH  │ Django OAuth Toolkit  │ Api keys      │ Endpoint: ...    │
│  Odoo        │                       │ App fees      │                  │
│  Gmail       │                       │ ...           │ 2 mo 1 wk ago    │
│  PolySysMon  │                       │               │ POST /admin/...  │
│  Nextcloud   │                       │               │                  │
│ EXTERNAL     │                       │               │                  │
│  Notion      │                       │               │                  │
│  Airtable    │                       │               │                  │
└──────────────┴───────────────────────┴───────────────┴──────────────────┘
```

---

## Files Modified (this session)
| File | Purpose |
|------|---------|
| `dose/templates/admin/base_site.html` | Sole admin base — theme, navbar badge, dark CSS injection |
| `dose/templates/admin/includes/custom_sidebar.html` | Grid layout, left nav, right activity sidebar, responsive |
| `dose/account_adapter.py` | OAuth tenant selection redirect |
| `dose/views/main.py` | `select_tenant_view` |
| `dose/templates/dose/select_tenant.html` | Tenant picker UI |
| `dose/admin_views.py` | `/admin/select-theme/api/` endpoint |
| `dose/context_processors.py` | `jazzmin_theme` context for per-user theme |
| `.cursor/rules/admin-templates-locked.mdc` | Enforces single-source template discipline |

---

**BINGO** ✅  
The admin interface is fully operational: correct tenant name, OAuth tenant picker, working theme toggle with dark mode readability, three-column responsive layout.
