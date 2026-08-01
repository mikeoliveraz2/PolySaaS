# Passthrough Readiness UI + Local Tenant Cleanup — 2026-08-01

## 1. Odoo passthrough — full-page navigation 404 fix

**Symptom:** Clicking "Activate Invoicing" inside the Odoo passthrough produced a Django 404
for `GET /odoo` (not `/pt/admin/localhost:8086/odoo`).

**Cause:** Odoo's own JS does full-page navigations via `window.location.href = '/odoo/...'`
(and `.assign()` / `.replace()`). The existing client-side shim in `OdooPassthroughHandler`
patched `fetch`, `XHR`, `history.pushState`, and asset attributes, but not `Location`. The
browser resolved the relative path against the PolySaaS origin (`localhost:8000`) instead of
routing it back through the passthrough prefix.

**Fix (owner-approved, frozen-file exception):** `dose/passthrough/handlers/odoo_handler.py`
now also patches `Location.prototype.href` (setter), `.assign()`, and `.replace()` in the
injected shim, rewriting the target through the same `rewriteUrl()` helper already used for
fetch/XHR so full-page navigations stay inside `/pt/admin/<endpoint>/...`.

Backup: `odoo_handler.py.bak_20260801_location_shim_fix`.

## 2. Passthrough readiness UI (sidebar)

**Problem:** `PassThroughEndpoint` rows are created by a provisioner (Step 1) before the
underlying app account/database actually finishes provisioning (Step 2+). The sidebar built
`passthrough_services` purely from `PassThroughEndpoint` (`is_enabled` + `show_in_menu`), with
no check against the app's actual readiness — so a passthrough card could be clickable in the
sidebar before it was usable.

**Fix:** `TenantApp.status` (`provisioning` / `active` / `error` / `disabled` — already existed
in `dose/models/tenant_app.py`) is now the source of truth for readiness.

- `dose/context_processors.py` — for each passthrough service, looks up the matching
  `TenantApp` by `app_name == endpoint.slug` in the tenant's schema and adds `ready` (bool,
  `status == 'active'`) and `app_status` to `service_data`. If no `TenantApp` row exists for
  that slug (e.g. Gmail, which isn't in `APP_CHOICES`), defaults to `ready=True` so nothing
  that worked without app-registry tracking gets hidden/disabled.
- `dose/templates/admin/includes/custom_sidebar.html` — a passthrough card renders as a real
  `<a href="...">` (clickable) when `ready`, or a `<span>` with no `href`,
  `aria-disabled="true"`, `tabindex="-1"` when not ready — genuinely non-clickable, not just
  styled that way. A status dot renders green (ready), pulsing amber (provisioning), or red
  (error/disabled).
- `dose/templates/admin/includes/custom_sidebar_head.html` — added `.pss-pt-card--not-ready`
  (grayscale, dimmed, `pointer-events: none`) and `.pss-pt-status-dot` CSS, including a
  collapsed-sidebar-scaled variant.

Backups: `context_processors.py.bak_20260801_passthrough_readiness`,
`custom_sidebar.html.bak_20260801_passthrough_readiness`,
`custom_sidebar_head.html.bak_20260801_passthrough_readiness`.

**Bug found + fixed during this same session:** the first pass used multi-line Django
`{# ... #}` comments to document the change inline. Django's `{# #}` comment tag only supports
a single line — a multi-line one isn't recognized as a comment at all, so the raw comment text
was output as literal page content (visible above the Odoo card in the sidebar). Fixed by
collapsing all added `{# #}` comments to single lines.

**Verified:**
- Rendered the real sidebar for tenant `pso13` via `django.test.Client` — all three endpoints
  (Odoo, NextCloud, Dolibarr) currently have `TenantApp.status == 'active'`, so all rendered as
  clickable `<a>` cards with a green dot, matching reality.
- Rendered `custom_sidebar.html` directly with mock `provisioning` and `error` service data —
  confirmed the not-ready path emits a correctly-closed `<span>` (no dangling tag mismatch),
  the right dot color, and no navigable `href`.
- Re-verified after the comment fix that no template comment text leaks into rendered output.

## 3. Local tenant/user cleanup

Removed three local test tenants that were created but never logged into:
`pso7`, `pso8`, `pso9` (schema=name=slug identical to username for each).

- `python manage.py prune_tenants --keep polysaas pso10 pso13 psol6 --yes-i-really-mean-it`
  (dry-run confirmed first) — dropped their PostgreSQL schemas (CASCADE) and deleted their
  `Tenant` / `UserProfile` / `UserTenantMembership` rows.
- `prune_tenants` intentionally does not touch `auth.User` rows, so the corresponding
  `pso7` / `pso8` / `pso9` user accounts were deleted separately via the ORM.

Kept: `polysaas` (main), `pso10`, `pso13`, `psol6` — untouched.

This was scoped to the local dev database only; the cloud/production database was already
reset separately and was not touched here.
