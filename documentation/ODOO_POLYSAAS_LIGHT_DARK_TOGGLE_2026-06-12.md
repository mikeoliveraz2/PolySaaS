# BINGO — Odoo One-Way PolySaaS Light/Dark Toggle

**Date:** 2026-06-12  
**Declared by:** Michael  
**Commit:** `04c5ec2e`  
**Test tenant:** PolySaaS Test 152 (`polysast152`)  
**Test URL:** `http://localhost:8000/pt/admin/polysaas-odoo2.onrender.com/web`

---

## What Was Achieved

When a subscriber toggles PolySaaS admin **light/dark** (Jazzmin `display_mode`), the **next** Odoo passthrough open follows the same mode. One-way only — Odoo user preferences do not change PolySaaS.

Odoo’s own dark palette varies by screen (apps grid vs accounting lists vs forms). That is upstream Odoo styling; PolySaaS only forces light vs dark asset bundles and scope classes.

### Certified behaviors

| Feature | Status |
|---------|--------|
| PolySaaS dark → Odoo loads `web.assets_web_dark` bundles | ✓ |
| PolySaaS light → Odoo loads standard `web.assets_web` bundles | ✓ |
| `color_scheme` cookie forced on every upstream proxied request | ✓ |
| Upstream `Set-Cookie` suppressed so Odoo cannot reset browser to light | ✓ |
| Embed scope preserves `o_dark` / `o_light` stripped from upstream `<body>` | ✓ |
| Odoo classes never applied to Jazzmin `document.body` (admin shell stays intact) | ✓ |
| Handler-only logic in `OdooPassthroughHandler` + generic embed hook in forwarder | ✓ |

---

## How It Works

```
PolySaaS admin: Toggle light/dark
    → display_mode cookie + session updated

User opens Odoo passthrough (sidebar)
    → OdooPassthroughHandler._polysaas_display_mode(request)
    → filter_cookies_for_upstream / override_upstream_cookies: color_scheme=dark|light
    → Upstream /web HTML returns matching asset bundle names
    → process_html_response: rewrite web.assets_web → web.assets_web_dark when dark
    → _wrap_in_admin_template: passthrough_embed_scope_classes → o_dark on .polysaas-passthrough-scope
    → passthrough_embed.html: theme on scope + inner .o_web_client shell only
    → apply_browser_response_cookies: browser color_scheme aligned with PolySaaS
```

**Note:** Writing `res.users.color_scheme` via RPC fails with `AccessError` for provisioned tenant users. Theme sync relies on the `color_scheme` cookie and HTML asset bundle selection, not Odoo user record updates.

---

## Files in This BINGO

| File | Change |
|------|--------|
| `dose/passthrough/handlers/odoo_handler.py` | Theme sync: cookies, asset rewrite, scope classes, shim, suppress upstream Set-Cookie |
| `dose/passthrough/forwarding.py` | Extract upstream html/body classes; `passthrough_embed_scope_classes` hook; `data-polysaas-display-mode` |
| `dose/templates/admin/passthrough_embed.html` | Scope dark background; `_applyScope_themeMode`; harvest Odoo classes off Jazzmin body |
| `*.bak-odoo-dark-embed`, `*.bak-blank-fix`, `*.bak-theme-sync-fix` | Backups before edit |

---

## Verification Steps

1. `.\runall`
2. Log in to test tenant admin (e.g. t152)
3. Set PolySaaS to **dark** (Toggle light/dark)
4. Open **Odoo** from passthrough sidebar — apps / invoicing views should be dark-themed
5. Set PolySaaS to **light**, open Odoo again — UI should be light
6. Console: `[PolySaaS Odoo] color_scheme cookie set to dark`, `[ODOO SHIM] color_scheme set to dark`
7. Server log: `[ODOO HANDLER] embed scope classes: 'o_dark' (mode=dark)`, `[ODOO HANDLER] Suppressing upstream Set-Cookie`

---

## Out of Scope (by design)

- Odoo → PolySaaS theme sync (reverse direction)
- Per-screen identical darkness inside Odoo (Odoo module CSS differs by app)
- `res.users.color_scheme` RPC sync (blocked by Odoo ACLs for provisioned users)
- Bootswatch palette name sync (only light vs dark mode)

---

## Related

- Mattermost one-way theme sync: `documentation/BINGO_MATTERMOST_POLYSAAS_THEME_SYNC_2026-06-13.md`
- SSO architecture: `.cursor/rules/sso-architecture.mdc`
