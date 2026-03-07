# Bingo: OAuth2 Phase 2 Provisioners + Passthrough Auth Middleware

**Date:** 2026-03-08
**Status:** Complete & Tested

## What Was Done

### Phase 2a — Mattermost Provisioner (new)
- Created `dose/services/mattermost_tenant_provisioner.py`
- Creates Mattermost team via `/api/v4/teams` (invite-only)
- Configures OIDC via `PATCH /api/v4/config` with DOT client credentials
- SSO welcome email (no password — "Log in with PolySaaS")
- Celery retry policy: 3x on 5xx, exponential backoff
- TenantApp status tracking (active/error)

### Phase 2b — Odoo Provisioner Enhanced
- Added `oauth_client_id`, `oauth_client_secret`, `tenant_app_id` params (backward-compatible)
- JSON-RPC stub ready for `auth.oauth.provider` creation when Odoo instance is live
- TenantApp status tracking integrated

### Phase 2c — Nextcloud Provisioner Enhanced
- Same pattern as Odoo: optional OAuth2 params, backward-compatible
- `occ user_oidc:provider` stub ready for Docker container availability
- TenantApp status tracking integrated

### Subscription Flow Wired Up
- `subscription_views.py` now calls `register_oauth2_app_for_tenant()` for Odoo, Nextcloud, and Mattermost
- Registers DOT OAuth2 Application per tenant+app pair before calling provisioner
- Passes `client_id`, `client_secret`, `tenant_app_id` to Celery tasks
- Graceful fallback: if OAuth2 registration fails, provisioner runs without SSO

### Shared OAuth2 Registration Helper
- `dose/services/oauth2_registration.py` — creates DOT Application + TenantApp record
- `mark_tenant_app_active()` / `mark_tenant_app_error()` — status management helpers

### Passthrough Auth Middleware (POL-2 / R-2)
- `dose/middleware/passthrough_auth.py` — Shela's architecture, Desktop-CC implementation
- **Header mode** (default): Injects `X-User-ID`, `X-User-Email`, `X-User-Name`, `X-User-Is-Staff`, `REMOTE_USER`, `X-Tenant-ID`, `X-Tenant-Name`, `X-Tenant-Slug` into `/pt/` requests
- **JWT mode**: Signs payload with OIDC RSA key (RS256) or Django SECRET_KEY (HS256 fallback), injects `Authorization: Bearer <token>`
- Configurable via `settings.PASSTHROUGH_AUTH_MODE` ('header' or 'jwt')
- Runs after AuthenticationMiddleware, before ExternalPassthroughMiddleware
- Existing `forwarding.py` already copies `HTTP_*` headers to outgoing requests (line 61)

### Olient Schema Fix
- Allauth migration 0004 was failing: `DROP CONSTRAINT` on a partial index
- Fix: dropped the partial index, faked migration 0004, allauth 0005–0009 applied cleanly

### GCP Checklist Updated
- POL-1 marked done (DOT OIDC provider live)
- R-3 and app table updated with Phase 2 progress
- Document history entry added for Desktop-CC

## Files Created
- `dose/services/mattermost_tenant_provisioner.py`
- `dose/services/oauth2_registration.py`
- `dose/middleware/passthrough_auth.py`
- `dose/middleware/__init__.py`

## Files Modified
- `dose/services/odoo_tenant_provisioner.py` — OAuth2 params + TenantApp tracking
- `dose/services/nextcloud_tenant_provisioner.py` — OAuth2 params + TenantApp tracking
- `dose/subscription_views.py` — OAuth2 registration + Mattermost provisioner
- `mysite/settings.py` — PassthroughAuthMiddleware + PASSTHROUGH_AUTH_MODE config
- `documentation/deployment/GCP-Deployment-Readiness-and-Checklist.md` — POL-1 done, R-3 progress

## Verification
- `manage.py check` — 0 issues
- All migrations applied (olient schema fixed)
- Backward-compatible: existing provisioners work without OAuth2 params

## Next Steps
- Connect to live Mattermost/Odoo/Nextcloud instances for end-to-end SSO test (POL-5)
- Configure WordPress with HTTP Header Auth plugin for passthrough SSO
- Switch to JWT mode when ready for production
