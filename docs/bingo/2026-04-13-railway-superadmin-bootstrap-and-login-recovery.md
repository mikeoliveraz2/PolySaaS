# BINGO — Railway SuperAdmin Bootstrap And Login Recovery

**Date:** 2026-04-13
**Status:** Operationally recovered; user account state confirmed in database
**Commit covers:** this bingo note

---

## What Was Achieved

PolySaaS Railway login recovery was documented end-to-end for the tenant admin path, including:

- service targeting for bootstrap environment variables
- root-cause sequence for failed login attempts
- production-safe fallback by direct SQL update
- verification path in both `public` and `olient` schemas
- dependency hotfix merges required to restore healthy boot behavior

This note is intended to be the single operational runbook for future incidents where
credentials appear valid but login still fails during or after unstable Railway deploys.

---

## Incident Timeline Summary

1. Initial password reset attempts were executed from local terminals against local settings,
   not the Railway runtime database.
2. Railway CLI was unavailable locally (`railway: command not found`), so local command success
   did not guarantee production DB updates.
3. Deploy logs showed repeated `/health/` failures (`service unavailable`) ending in
   `Healthcheck failed`, preventing reliable startup completion.
4. Missing runtime dependencies were identified and merged via PR workflow:
   - PR #18: gunicorn requirement
   - PR #19: whitenoise requirement
5. Tenant admin bootstrap behavior was confirmed in code:
   - creates/updates user
   - forces tenant membership role to `admin`
   - links `UserProfile` to target tenant
6. Direct DB verification later confirmed `SuperAdmin` exists and is active/staff/superuser.

---

## Bootstrap Behavior (Authoritative)

The command `python manage.py bootstrap_auth` runs from the Railway web entrypoint and performs
these tenant-admin actions when env vars are set:

- resolves target tenant by slug (creates tenant if missing)
- creates or updates the tenant admin user
- sets `is_active=True`, `is_staff=True`, `is_superuser=True`
- sets password when user is newly created or when force flag is enabled
- ensures `user_tenant_memberships` record with role `admin`
- ensures `dose_userprofile` points to the selected tenant

Relevant implementation references:

- `scripts/railway-entrypoint.sh`
- `dose/management/commands/bootstrap_auth.py`
- `dose/models/user_tenant_membership.py`
- `dose/models/user_profile.py`
- `dose/models/tenant.py`

---

## Correct Railway Variable Placement

These variables must be placed on the Django web service (the service running the app entrypoint),
not on Postgres/Redis/Adminer.

Required incident vars used during recovery:

- `BOOTSTRAP_TENANT_ADMIN_USERNAME=SuperAdmin`
- `BOOTSTRAP_TENANT_ADMIN_PASSWORD=PolySaaS2026!`
- `BOOTSTRAP_TENANT_ADMIN_TENANT_SLUG=olient`
- `BOOTSTRAP_TENANT_ADMIN_FORCE_PASSWORD=1`

Operational caution:

- Leaving force password enabled continuously will reset the password on every deploy.
- This is acceptable as a temporary stabilization tactic and should be disabled later.

---

## Why Login Failed Even With "Correct" Credentials

Several independent factors overlapped:

- local shell commands hit local DB due local settings and env context
- Railway service instability blocked healthy app startup
- if bootstrap does not run to completion, expected user/password mutation may not occur
- case-sensitive password mismatch attempts occurred (`PolySaaS2026!` vs `PolySaas2026!`)

Net effect:

- UI showed invalid credentials even though user rows looked plausible in one schema
- true state needed to be enforced and verified in both `public` and tenant schema contexts

---

## Production Fallback That Works Reliably

When bootstrap timing is questionable, execute SQL directly in Railway Postgres Query:

1. set/update password hash in `public.auth_user` for `SuperAdmin`
2. set/update password hash in `olient.auth_user` for `SuperAdmin`
3. verify rows in both schemas
4. verify membership/profile links if needed

Password hash used in recovery:

- `pbkdf2_sha256$1000000$t0IEhHktstYxrJ09vcTPIk$Uxihh+bf8bQ8buLwLFXbdNLgDMibH0dyu+VlSHyyYz8=`

This corresponds to the target password:

- `PolySaaS2026!`

---

## Verification Checklist

Post-recovery checks:

1. Railway deploy is green (no repeated `/health/` failure loop)
2. `auth_user` contains `SuperAdmin` in `public` schema and target tenant schema
3. `is_active`, `is_staff`, `is_superuser` all true
4. membership exists in `user_tenant_memberships` with role `admin` for tenant `olient`
5. `dose_userprofile` points `SuperAdmin` to `olient` tenant
6. login tested with exact case-sensitive credentials in fresh/incognito browser session

---

## Scope Boundaries

- Included in this documentation:
  - incident chronology
  - deploy/auth root causes
  - bootstrap behavior
  - env var placement
  - schema-specific fallback and validation
- Not included in this documentation:
  - direct Railway dashboard actions taken by user
  - transient local scratch files created during troubleshooting

---

## Outcome

- Recovery path is now codified and repeatable.
- Bootstrap expectations are clearly aligned with actual code behavior.
- Operational team has a deterministic fallback even when service startup is unstable.

**Status: BINGO — Railway SuperAdmin bootstrap/login recovery documented end-to-end.**
