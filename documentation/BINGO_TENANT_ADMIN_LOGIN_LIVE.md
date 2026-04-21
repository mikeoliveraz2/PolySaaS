# BINGO: Tenant Admin Login Live on Render

**Date:** April 21, 2026
**Status:** **Verified in production** — tenant created, admin user authenticated, admin dashboard loads.
**Branch:** `main`
**Primary URL:** `https://polysaas-core.onrender.com`

---

## Summary

First real tenant provisioned on Render via `create_tenant_and_admin` management command.
Admin dashboard accessible and showing correct tenant context in top bar.

---

## Certified (operator-verified on Render)

| Area | Detail |
|------|--------|
| **Tenant created** | `PolySaaS Online LLC` · slug `polysaas` · schema `polysaas` |
| **Schema migrated** | `migrate_all_schemas` applied all migrations to new `polysaas` schema |
| **Admin user** | `Michael.Oliver@polysaas.online` · `is_staff=True` · `UserProfile` + `UserTenantMembership(role=admin)` |
| **Login** | `/dose/login/` and `/admin/` both authenticate successfully |
| **Admin dashboard** | Shows `POLYSAAS ONLINE LLC - MICHAEL.OLIVER@POLYSAAS.ONLINE` in top bar |
| **Case-insensitive login** | `CaseInsensitiveModelBackend` in `AUTHENTICATION_BACKENDS`; username lookup uses `iexact`, password remains case-sensitive |

---

## What was built / fixed in this session

| File | Change |
|------|--------|
| `dose/management/commands/create_tenant_and_admin.py` | New management command: creates Tenant + schema, runs `migrate_all_schemas`, creates User + UserProfile + UserTenantMembership, seeds passthrough endpoints |
| `mysite/auth_backends.py` | New `CaseInsensitiveModelBackend` — `iexact` username lookup |
| `mysite/settings.py` | `AUTHENTICATION_BACKENDS` updated to use `CaseInsensitiveModelBackend` |
| `dose/middleware/jazzmin_tenant_theme.py` | Fixed `UnboundLocalError` → 500 on `/admin/` when middleware try-block fails before assigning `passthrough_endpoints`; set safe defaults at top of `process_request` |
| `parameters/models.py` | Added `encrypted_payload` (Fernet at-rest secrets) + `has_encrypted_secrets()` / `get_decrypted_secrets()` |
| `parameters/crypto.py` | Fernet encrypt/decrypt helpers; key from `PARAMETER_FERNET_KEY` or HKDF(`SECRET_KEY`) |
| `parameters/forms.py` | `ParameterAdminForm` — superuser-only plaintext secrets input, stored only as ciphertext |
| `parameters/admin.py` | Superuser-only encrypted secrets fieldset; staff see no secret rows |
| `parameters/views.py` | Hides secret-bearing Parameter rows from non-superusers |
| `parameters/tests.py` | Crypto round-trip + empty secrets test |
| `parameters/migrations/0002_parameter_encrypted_payload.py` | Migration for `encrypted_payload` field |
| `mysite/settings.py` | `PARAMETER_FERNET_KEY` env var |
| `.env.example` | Documented `PARAMETER_FERNET_KEY` |
| `dose/services/mattermost_provisioning_service.py` | `_load_config` reads decrypted secrets first, falls back to `param1`/`param2` |

---

## Follow-up (not blocking)

1. **Repeat migrate** after `parameters/migrations/0002_parameter_encrypted_payload.py` is pushed — `python manage.py migrate` shows "dose has unapplied changes" warning (encrypted_payload migration not yet applied on Render).
2. **`ADMIN_STATUS_BANNER_ENABLED=0`** — set env var on Render to stop the repeated green bootstrap banner on admin dashboard.
3. **Odoo** — deploy and wire PolySaaS ↔ Odoo passthrough.
4. **Admin 500** — confirm resolved after deploy; if still present, paste traceback from Render Logs.
