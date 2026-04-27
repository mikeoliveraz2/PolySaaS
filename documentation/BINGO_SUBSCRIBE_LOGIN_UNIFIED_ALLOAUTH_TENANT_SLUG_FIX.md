# BINGO: Subscribe + Unified Login + Tenant Slug Fix

**Date:** April 27, 2026
**Status:** **Verified locally** — subscribe returns `201`, logout popup removed, unified allauth login page renders.
**Branch:** `main`

---

## Summary

This session fixed the broken subscribe→login experience and resolved the tenant primary-key mismatch that caused crashes when provisioning tenants.

Key outcomes:

- Subscribe successfully creates tenant + user (API `POST /dose/api/subscriptions/` returns `201`).
- Removed forced logout redirect after subscribe (eliminated the “sign out” popup before login).
- Standardized runtime tenant lookup/session usage to `tenant_slug` (Tenant slug is the PK) with backward compatibility for legacy `tenant_id` session keys.
- Restored a single unified login flow via django-allauth (`/accounts/login/`) with PolySaaS branding.

---

## Primary issues fixed

### 1) Tenant PK mismatch (`tenant.id` / bigint vs slug)

Root cause: Tenant uses `slug` as primary key, but multiple code paths still assumed an integer `id`.

Fix: updated tenant resolution and OAuth app registration to use `tenant.pk` / `tenant.slug`.

### 2) Subscribe success flow forced a logout

Root cause: `subscribe.html` redirected to `/accounts/logout/?next=...` after a successful subscription.

Fix: redirect directly to `/accounts/login/?next=/admin/`.

### 3) Duplicate/overridden login view broke allauth behavior

Root cause: a custom override for `/accounts/login/` interfered with the normal allauth login flow.

Fix: remove the override and let `include('allauth.urls')` own `/accounts/login/`.

---

## Files changed (high-level)

| File | Change |
|------|--------|
| `dose/templates/dose/subscribe.html` | Added pre-POST console logging + improved non-JSON response logging; removed logout-then-login redirect after `201` |
| `mysite/urls.py` | Removed custom `/accounts/login/` mapping so django-allauth handles unified login; keep `/admin/login/` redirect to allauth |
| `templates/account/login.html` | Updated branding to PolySaaS + logo; label “Username or email”; button “Sign in” |
| `dose/subscription_views.py` | Use tenant slug PK consistently during provisioning / oauth registration |
| `dose/services/oauth2_registration.py` | Tenant lookup uses slug PK instead of `tenant.id` |
| `dose/utils.py` | `get_current_tenant()` reads `tenant_slug` (fallback to legacy `tenant_id` treated as slug) |
| `dose/doseusertenantmiddleware.py` | Session tenant attachment uses `tenant_slug` + slug lookup; session setter writes `tenant_slug` (and legacy `tenant_id` as slug) |
| `dose/tenant_session.py` | Ensure session persists `tenant_slug` (and legacy `tenant_id` as slug) |
| `dose/doserequestcontroller.py` | Session tenant attach fixed to use slug + correct `connection.cursor()` usage |
| `dose/views/main.py` | Fallback tenant lookup via session uses slug |

---

## Known follow-ups (not blocking the BINGO outcome)

- Several tables/models still appear to store `tenant_id` as `BIGINT` in DB, but runtime now passes slug strings (examples seen in logs: request tracking, navigation panel queries, tenant app queries). These should be migrated/refactored to `tenant_slug` consistently.
- Background provisioning enqueues failed when Redis/Celery broker isn’t running (non-blocking for subscribe + login UI).

---

## New working rule

When the user declares **BINGO**, the process is:

1. Write a session summary into `documentation/`
2. Commit relevant changes
3. Push to repo
