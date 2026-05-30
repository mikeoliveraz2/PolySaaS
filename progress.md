# PolySaaS Odoo Passthrough — Progress Notes

## Status: WORKING ✓ (2026-05-30)

### What works
- Sidebar Odoo tile → PolySaaS admin shell with Odoo in iframe ✓
- Odoo apps grid renders correctly inside the content column ✓
- Sidebar and Jazzmin navbar remain visible ✓
- Static assets (CSS, JS, fonts, images) proxy through correctly ✓
- Auto-login shim boots inside iframe, authenticates via /web/session/authenticate ✓
- DB manager page detection + redirect to /web/login ✓

### Architecture: Iframe Shell Pattern
**Browser request** (`GET /pt/admin/polysaas-odoo2.onrender.com/...`)
→ `odoo_handler.process_html_response()` detects no `__pss_raw=1`
→ Returns `passthrough_odoo_shell.html` — PolySaaS admin shell with `<iframe src="...?__pss_raw=1">`

**Iframe request** (`GET /pt/admin/.../...?__pss_raw=1`)
→ `odoo_handler.process_html_response()` detects `__pss_raw=1`
→ Returns raw shimmed Odoo HTML directly (no admin wrapping)
→ Shim injects into `<head>`, auto-login fires, OWL mounts to its own `document.body`

### Key files
- `dose/passthrough/handlers/odoo_handler.py` — main handler, shim injection, iframe split logic
- `dose/templates/admin/passthrough_odoo_shell.html` — iframe shell template (NEW)
- `dose/templates/admin/passthrough_embed.html` — generic embed template (not used for Odoo now)
- `dose/passthrough/forwarding.py` — returns HttpResponse directly if handler returns one (line 788-790)

### Known issues / next session
- Odoo "Oops! Something went wrong" when clicking app modules (e.g. Invoicing) — this is
  Odoo's own "Request Access" error for modules not fully provisioned on the shared instance.
  Not a PolySaaS bug. May need per-tenant Odoo provisioning or correct admin credentials.
- Orchestration hook errors: `invalid input syntax for type bigint: "polysaast13"` — separate issue,
  tenant_slug used where bigint ID expected in instruction lookup query.
- gcloud auth expired — `google.auth.exceptions.RefreshError` in background; run
  `gcloud auth application-default login` to fix.

### Credentials (shared Odoo instance)
- Upstream: `https://polysaas-odoo2.onrender.com`
- Admin login: `pst13@me.com`
- DB: configured in odoo_handler fallback credentials
