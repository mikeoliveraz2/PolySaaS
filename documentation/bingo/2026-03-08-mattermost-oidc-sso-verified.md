# BINGO — Mattermost OIDC SSO End-to-End Verified

**Date:** 2026-03-08  
**Session:** Desktop evening — Mattermost SSO live test  
**Status:** TESTED & VERIFIED  

---

## What Was Done

### 1. Resolved Docker ↔ Host Split-Horizon DNS

The core blocker for Mattermost OIDC testing was that the browser and Docker
containers needed to reach Django's OIDC endpoints using the **same** base URL,
but `host.docker.internal` resolved to a stale LAN IP (`192.168.8.61`) on the
host while the machine had moved to `192.168.8.180`.

**Fix:** Updated `C:\Windows\System32\drivers\etc\hosts` to map
`host.docker.internal` → `127.0.0.1`. Now both the browser and Docker
containers (which use Docker Desktop's internal gateway) reach Django on
`0.0.0.0:8000` via `host.docker.internal:8000`.

### 2. Added Standard OIDC Claims to UserInfo / ID Tokens

Mattermost rejected the SSO login with "Invalid email" because the OIDC
userinfo endpoint only returned `sub` + tenant claims. Standard claims required
by Mattermost (and Odoo/Nextcloud) were missing.

**Fix:** Extended `TenantAwareValidator` in `dose/oauth.py`:
- `email`, `email_verified` (scope: `email`)
- `name`, `given_name`, `family_name`, `preferred_username` (scope: `profile`)
- Existing `tenant_id`, `tenant_name`, `tenant_slug` (scope: `tenant`)

### 3. Full SSO Flow Verified

Tested the complete Authorization Code flow end-to-end:

1. Open `http://localhost:8065/login`
2. Click **"Log in with PolySaaS"**
3. Browser redirects to `http://host.docker.internal:8000/o/authorize/`
4. Django shows consent screen ("Authorize Oliver Enterprises-mattermost")
5. Click **Authorize** → Django issues auth code → redirects to Mattermost
6. Mattermost exchanges code for tokens (server-to-server via `host.docker.internal:8000`)
7. Mattermost reads userinfo (email, name) → creates user → logs in
8. User lands on Mattermost **Select Team** page — **fully authenticated**

---

## Files Changed

| File | Change |
|------|--------|
| `dose/oauth.py` | Added standard OIDC claims (email, name, profile) to `oidc_claim_scope` and `get_additional_claims()` |

## Infrastructure Changes (Not in Git)

| Item | Change |
|------|--------|
| Windows hosts file | `host.docker.internal` → `127.0.0.1` (was stale `192.168.8.61`) |
| Mattermost OIDC config | Discovery endpoint updated to `http://host.docker.internal:8000/o/.well-known/openid-configuration` via API |
| Django binding | Confirmed running on `0.0.0.0:8000` (set in previous session's `go.ps1`) |

---

## POL-5 Milestone Status

| Step | Status |
|------|--------|
| Django as OIDC Provider (DOT + RSA keys) | DONE |
| Custom consent screen | DONE |
| Tenant-aware claims in ID tokens | DONE |
| Standard OIDC claims (email, profile) | **DONE** (this session) |
| Mattermost native OIDC integration | **VERIFIED** |
| Odoo `auth_oidc` integration | Pending (provisioner ready) |
| Nextcloud `user_oidc` integration | Pending (provisioner ready) |
| WordPress passthrough SSO (mu-plugin) | DONE (needs live proxy test) |

---

## Tested By

- Cursor IDE browser automation against local Django (`0.0.0.0:8000`) +
  Mattermost Enterprise Edition (Docker, `localhost:8065`)
- UserInfo endpoint verified via `curl` with Bearer token
- Discovery endpoint verified from both host and Docker network
