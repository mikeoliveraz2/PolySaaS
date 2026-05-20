# Mattermost Passthrough - Final Working State (2026-05-20)

**URL:** `http://localhost:8000/pt/admin/mattermost/`

**Status:** Working in embedded PolySaaS passthrough mode. Login succeeds, the Mattermost document loads fully, and Town Square is reachable inside the embed.

## Key Changes

- Root passthrough handling now prefers a direct Mattermost document response and bypasses PolySaaS admin wrapping when the handler returns a raw response.
- Mattermost login pages are replaced by the local login bridge based on both request path and returned login-document content, avoiding false negatives when Mattermost serves login HTML on protected routes.
- Server-side token refresh now prefers encrypted session credentials, then tenant config, then the shared app-admin password fallback.
- Mattermost provisioning now persists the effective username, password, token, and team metadata into `TenantApp.extra_config` so passthrough recovery works after reprovision or fresh browser sessions.
- Passthrough asset requests (`/static/*`, manifests, bundles) bypass Django auth redirects, preventing recursive `/login/login/...` behavior.
- The dedicated Mattermost static proxy no longer requires Django login, so SPA assets load under the passthrough origin.
- Response generation for passthrough HTML error pages and wrapped responses is encoded as UTF-8 to avoid Windows `UnicodeEncodeError` failures.

## Tested Flow

1. Visit `/pt/admin/mattermost/`.
2. If no valid browser token is present, the PolySaaS login bridge is shown instead of the upstream Mattermost login shell.
3. Login completes and sets the Mattermost session token for passthrough use.
4. Mattermost loads inside the PolySaaS embed with channels and Town Square visible.
5. No blank white screen, no recursive login loop, and no asset redirect to Django login.

## Files Changed In Final Stabilization

- `dose/passthrough/handlers/mattermost_handler.py`
- `dose/passthrough/forwarding.py`
- `dose/passthrough/middleware.py`
- `dose/polysniffer/views/mattermost_static_proxy.py`
- `dose/services/mattermost_provisioning_service.py`
- `dose/services/mattermost_tenant_provisioner.py`
- `mysite/settings.py`

## Notes

- The shared app password fallback comes from `POLYSAAS_APP_ADMIN_PASSWORD`.
- Local scratch artifacts such as `_mm_login_resp.html` are not part of the final change set.
- A follow-up pass can still improve performance tuning, dark-mode sync, and plugin/static edge cases.