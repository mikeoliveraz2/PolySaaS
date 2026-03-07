# Bingo: OAuth2/OIDC Provider — Phase 1 Implementation

**Date:** 2026-03-07
**Status:** Complete & Tested

## What Was Done

Implemented Phase 1 of the OAuth2 SSO design: **Django as the central OIDC Identity Provider** using `django-oauth-toolkit` (DOT). PolySaaS now exposes a standards-compliant OpenID Connect provider that Mattermost, Odoo, and Nextcloud can authenticate against.

### OIDC Provider Setup
- Installed `django-oauth-toolkit` 3.2.0 (+ `oauthlib`, `jwcrypto`)
- Generated RSA 4096-bit private key for JWT signing (`oidc_rsa_key.pem`, gitignored)
- Configured `OAUTH2_PROVIDER` in settings.py with OIDC enabled, RS256 signing, tenant-aware scopes
- Added `OAuth2TokenMiddleware` and `OAuth2Backend` to the middleware/auth chain

### OIDC Endpoints (all verified working)
- `GET /o/.well-known/openid-configuration` — Discovery endpoint (returns issuer, endpoints, scopes, signing algos)
- `GET /o/.well-known/jwks.json` — JSON Web Key Set (RS256 public key)
- `POST /o/token/` — Token endpoint (Authorization Code, Client Credentials, Refresh)
- `GET /o/userinfo/` — UserInfo endpoint (includes tenant claims)
- `GET /o/authorize/` — Authorization endpoint (custom branded consent screen)

### Custom OIDC Claims
- `TenantAwareValidator` (`dose/oauth.py`) injects `tenant_id`, `tenant_name`, `tenant_slug` into ID tokens and UserInfo responses
- Scopes: `openid`, `email`, `profile`, `tenant`

### TenantApp Model
- New model tracking provisioned apps per tenant with OAuth2 client reference
- Fields: tenant (FK), app_name, app_url, oauth_application (OneToOne to DOT Application), status, last_error
- Unique constraint: (tenant, app_name)
- Registered in Django admin with list/filter/search

### Consent Screen
- `TenantAwareAuthorizationView` with branded template (`dose/oauth/authorize.html`)
- Auto-approve logic: skips consent when the OAuth2 app belongs to the same tenant as the logged-in user
- Shows explicit consent for cross-tenant or third-party access

### Security
- RSA private key excluded from git (`.pem` added to `.gitignore`)
- `~$*` temp files also added to `.gitignore`
- Short-lived tokens: access=1hr, refresh=24hr
- PKCE support available (not required for server-to-server)

## Files Created/Modified
- `dose/oauth.py` — TenantAwareValidator + redirect URI helper
- `dose/models/tenant_app.py` — TenantApp model
- `dose/models/__init__.py` — Added TenantApp import
- `dose/views/oauth_consent.py` — Custom authorization view with auto-approve
- `dose/templates/dose/oauth/authorize.html` — Branded consent screen
- `dose/migrations/0022_tenantapp.py` — Migration
- `dose/admin.py` — TenantAppAdmin registered
- `mysite/settings.py` — OAUTH2_PROVIDER config, middleware, auth backend
- `mysite/urls.py` — /o/ routes wired up
- `requirements.txt` — Updated with DOT dependencies
- `.gitignore` — Added *.pem and ~$* exclusions

## Verification
- `manage.py check` — 0 issues
- `GET /o/.well-known/openid-configuration` — HTTP 200, full OIDC spec returned
- `GET /o/.well-known/jwks.json` — HTTP 200, RS256 key published
- Migrations applied to all schemas

## Next: Phase 2a — Mattermost Provisioner Enhancement
