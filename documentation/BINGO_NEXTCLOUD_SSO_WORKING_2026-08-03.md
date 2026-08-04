<!-- THIS CODE IS FROZEN — NO CHANGES TO THIS CODE ARE ALLOWED WITHOUT THE OWNER'S PERMISSION -->
<!-- BINGO: Nextcloud server-side SSO working — 2026-08-03 -->

# BINGO: Nextcloud Server-Side SSO Working

**Date:** 2026-08-03  
**Verified by:** agent (Django test client, tenant `pso17`) + owner-approved implementation  
**Commit:** `9afaaa12` (`9afaaa128f5540a4fbb71d0bd954243d4ddc346b`)

## What this certifies

Nextcloud passthrough for tenant **pso17** auto-authenticates under the PolySaaS admin shell:

- Menu/proxy: **`/pt/admin/nextcloud/`** (slug identity)
- Landing: **`/apps/files/`**
- Server-side SSO: reads `TenantApp.extra_config` (`nc_login` / `nc_password`) → Nextcloud form login → browser `Set-Cookie` (`nc_username`, `nc_session_id`, `nc_token`, …) → redirect into Files
- No manual Nextcloud login when credentials are present

## Root causes fixed

### 1. Unreachable upstream URL

`PassThroughEndpoint.endpoint_url` / `nc_url` pointed at Docker DNS `http://polysaas-nextcloud:80`, which Waitress on the host cannot resolve. Pointed at `http://localhost:8888` (host-mapped port).

### 2. User never existed / wrong admin

Shared NC only had `admin`. Provisioner used `ncadmin` + settings password that did not match the live container. Created `pso17` via `occ`, synced password into `extra_config`.

### 3. SSO never ran for `/apps/files/`

Middleware only early-invokes `try_root_display_shell_response` for `passthrough_early_shell_paths()`. Nextcloud had none, and the forwarder only auto-calls try_root for `/`. Added early paths for `/`, `/login`, `/apps/files`, `/apps/dashboard`, etc.

### 4. Server-side SSO (Odoo-style, not client password form)

Handler `_server_side_nc_login`: GET `/login` → `requesttoken` → POST `/login` → forward session cookies. On OCS probe failure (or login path), `try_nextcloud_sso` redirects with cookies.

## Verification

Django test client (`force_login` + `tenant_slug=pso17`):

```
[PT-CORE] Early shell intercept for upstream subpath '/apps/files'
[NC_OCS] user probe failed — attempting server SSO
[NC-SSO] server login OK user=pso17 cookies=7
status 302
location /pt/admin/nextcloud/apps/files/
set_cookies [… nc_username, nc_token, nc_session_id …]
SSO_REDIRECT_OK
```

## Provisioner / settings alignment

- `NEXTCLOUD_SHARED_URL` default / host rewrite → `http://localhost:8888`
- Admin login default `admin`; `NEXTCLOUD_SHARED_ADMIN_PASSWORD` (fallback `POLYSAAS_APP_ADMIN_PASSWORD`)
- Endpoint `starting_uri` → `/apps/files/`
- On OCS “user exists”, sync password so stored creds stay valid
- `extra_config` also writes `nextcloud_login` / `nextcloud_password` aliases

## Files in this commit

| Path | Role |
|------|------|
| `dose/passthrough/handlers/nextcloud_handler.py` | SSO + early shell paths |
| `dose/services/nextcloud_tenant_provisioner.py` | Local URL/admin, starting_uri, password sync |
| `mysite/settings.py` | NC admin URL/login/password settings |
| `*.bak` | Pre-edit backups |
| `documentation/BINGO_NEXTCLOUD_SSO_WORKING_2026-08-03.md` | This certification |

## Freeze

Source files carry:

```
THIS CODE IS FROZEN — NO CHANGES TO THIS CODE ARE ALLOWED WITHOUT THE OWNER'S PERMISSION
```

plus `BINGO: Nextcloud server-side SSO working — 2026-08-03`.

## GOLD ZIP

`D:\BINGO ZIPS\BINGO_NEXTCLOUD_SSO_2026-08-03.zip` (retain max 4 GOLD zips).

## Note

`.env` local URL/admin login updates are machine-local and not required in git (secrets stay out of the commit).
