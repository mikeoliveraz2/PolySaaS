# Bingo: WordPress Passthrough SSO + Mattermost OIDC Local Setup

**Date:** 2026-03-08
**Author:** Desktop-CC (Cursor Agent)
**Reviewed by:** Shela (architecture input on passthrough middleware)

---

## Summary

Implemented the two halves of POL-5 (single-sign-on across bundled apps):

1. **WordPress Passthrough SSO** — custom mu-plugin that reads `REMOTE_USER` / `X-User-Email` headers injected by the Django passthrough middleware and auto-logs in (or auto-provisions) WordPress users.
2. **Mattermost Native OIDC** — Docker Compose for local Mattermost Enterprise + a management command (`setup_mattermost_oidc`) that registers the OAuth2 app in DOT and configures Mattermost's OpenID Connect in one shot.

## Files Created

| File | Purpose |
|------|---------|
| `dose/wordpress/mu-plugins/polysaas-passthrough.php` | WP must-use plugin: REMOTE_USER auto-login with auto-provisioning, role mapping (staff→editor), optional tenant slug validation |
| `docker-compose.mattermost.yml` | Local Mattermost Enterprise with PostgreSQL on port 8065 |
| `dose/management/commands/setup_mattermost_oidc.py` | Django mgmt command: registers DOT OAuth2 app + PATCHes MM OIDC config via admin API |

## Files Modified

| File | Change |
|------|--------|
| `docker-compose.wordpress.yml` | Added bind-mount for `dose/wordpress/mu-plugins` → `/var/www/html/wp-content/mu-plugins` |

## Architecture Notes

- **Passthrough flow (WordPress):** User authenticates in PolySaaS → navigates to `/pt/wordpress/` → `PassthroughAuthMiddleware` injects `REMOTE_USER` + `X-User-*` headers → mu-plugin reads headers and sets WP auth cookie → seamless login.
- **Native OIDC flow (Mattermost):** User clicks "Log in with PolySaaS" on MM login page → redirected to PolySaaS `/o/authorize/` → consent auto-approved (same tenant) → redirected back to MM with auth code → MM exchanges code for ID token at `/o/token/` → user logged in.
- Both flows converge at the same Django OIDC provider (Phase 1, committed 2026-03-07).

## Header Alignment

The mu-plugin reads the exact headers the middleware injects:

| Django Middleware (`passthrough_auth.py`) | WordPress mu-plugin reads |
|------------------------------------------|--------------------------|
| `REMOTE_USER` = user.email | `$_SERVER['HTTP_REMOTE_USER']` or `$_SERVER['REMOTE_USER']` |
| `X-User-Email` = user.email | `$_SERVER['HTTP_X_USER_EMAIL']` (fallback) |
| `X-User-Name` = full name | `$_SERVER['HTTP_X_USER_NAME']` (display name) |
| `X-User-Is-Staff` = true/false | `$_SERVER['HTTP_X_USER_IS_STAFF']` (role mapping) |
| `X-Tenant-Slug` = tenant slug | `$_SERVER['HTTP_X_TENANT_SLUG']` (anti-spoof check) |

## POL-5 Test Steps

```bash
# WordPress passthrough
1. Start WP:  docker-compose -f docker-compose.wordpress.yml up -d
2. Login to PolySaaS (localhost:8000)
3. Navigate to /pt/wordpress/ → expect instant WP login

# Mattermost native OIDC
1. Start MM:  docker-compose -f docker-compose.mattermost.yml up -d
2. Create MM admin at localhost:8065, get personal access token
3. Run:       python manage.py setup_mattermost_oidc --tenant olient
4. Open MM login page → click "Log in with PolySaaS" → expect SSO
```

## Status

- **POL-2 (Passthrough middleware):** COMPLETE — header + JWT modes
- **POL-5 (Single login test):** READY FOR LOCAL TESTING
- **R-3 (Native OIDC):** Mattermost wired; Odoo/Nextcloud provisioner stubs ready

---

*Tested: code review + static analysis. Live POL-5 test pending Docker spinup.*
