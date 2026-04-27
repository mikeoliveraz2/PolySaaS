# DEBUG: Tenant Refactor (tenant_id → tenant_slug) — Login/Subscribe Impact Report

**Date:** April 27, 2026
**Scope:** Identify remaining `tenant_id` vs `tenant_slug` usage and why username/password login can break while Google OAuth still works.

---

## Executive summary

Your codebase is in a **mixed state**:

- The **Tenant model** uses **`slug` as the primary key**.
- Runtime session state now often stores a **string slug** (e.g. `betatest`) under:
  - `session["tenant_slug"]` (correct)
  - `session["tenant_id"]` (legacy compatibility key, but now also a *slug string*)

However, several middleware/components still treat `tenant_id` as a **numeric bigint** (casting to `int`, validating `.isdigit()`, using `IntegerField`, etc.).

This creates inconsistent behavior across flows:

- **Schema switching / tenant context middleware** may fail to resolve the active tenant if `session["tenant_id"]` contains a slug string.
- Some code paths still access **`tenant.id`** (attribute does not exist if `slug` is PK), causing exceptions.
- Some DB tables still appear to have **`tenant_id` bigint columns**; passing a slug string yields DB errors like:
  - `invalid input syntax for type bigint: "betatest"`

---

## Repo-wide search results

- `tenant_id` matches: **180 matches across 67 files**
- `tenant_slug` matches: **119 matches across 33 files**

This report focuses on the subset that affects:

- Authentication (username/password)
- Session tenant alignment
- Schema (`search_path`) switching
- Subscribe provisioning

---

## 1) Username/password login flow (mapped)

### Request path

- **GET** `/accounts/login/`
  - URL: `mysite/urls.py` → `path('accounts/', include('allauth.urls'))`
  - View: django-allauth `LoginView`
  - Template: `templates/account/login.html`

- **POST** `/accounts/login/`
  - django-allauth authenticates using:
    - `AUTHENTICATION_BACKENDS` from `mysite/settings.py`
      - `mysite.auth_backends_allauth.AllauthCaseInsensitiveBackend`
      - `django.contrib.auth.backends.ModelBackend`
  - On success it redirects via:
    - `ACCOUNT_ADAPTER = 'dose.account_adapter.CustomAccountAdapter'`

### Middleware involved (important)

`mysite/settings.py` middleware order:

- `SessionMiddleware`
- `AuthenticationMiddleware`
- `UserRequestTrackingMiddleware`
- `AdminTenantSessionMiddleware`
- `TenantContextMiddleware`
- `SessionTenantMiddleware`

Key point:

- On login POST, the user is unauthenticated at first; after authentication, the response cycle runs `process_response` hooks.
- After login succeeds, the system relies on session tenant keys + middleware to set schema (`search_path`) correctly.

### Critical auth-adjacent code that still assumes numeric `tenant_id`

#### A) `dose/account_adapter.py`

```py
if len(memberships) > 1 and not request.session.get("tenant_id"):
    return "/dose/select-tenant/"
```

- **Issue:** still checks presence of `tenant_id` rather than `tenant_slug`.
- **Impact:** can incorrectly trigger tenant selection logic or skip it depending on which keys are present.

---

## 2) Google OAuth login flow (mapped)

### Request path

- **GET** `/accounts/google/login/` (allauth provider)
- Provider redirects to Google; callback returns to `/accounts/google/login/callback/`
- django-allauth finalizes the user/session

### Key differences vs password flow

- Uses `SOCIALACCOUNT_ADAPTER = 'dose.adapters.CustomSocialAccountAdapter'`.
- That adapter patches `Site` and `SocialApp` lookups to force **public schema** access.

Notable: this adapter and the social login flow are **less dependent** on `TenantContextMiddleware` resolving tenant from `session['tenant_id']` (and it does not try to cast it to int).

This helps explain why social login can continue working even when other tenant-id casts are broken.

---

## 3) Concrete breakpoints: `tenant_id` usage that conflicts with slug PK

### Breakpoint 1 — `TenantContextMiddleware` casts `session['tenant_id']` to int

**File:** `mysite/tenant_context_middleware.py`

```py
header_tid = request.META.get("HTTP_X_TENANT_ID")
if header_tid is not None and str(header_tid).strip().isdigit():
    tenant_id = int(header_tid)
...
if tenant_id is None:
    tid = request.session.get("tenant_id")
    if tid is not None:
        try:
            tenant_id = int(tid)
        except (TypeError, ValueError):
            tenant_id = None
```

- **Why this is a problem now:** `session['tenant_id']` is often a **slug string** (e.g. `betatest`).
- The `int()` conversion fails → `tenant_id` becomes `None` → middleware exits.

**Impact:**

- Tenant context (`request.current_tenant_id`, role, membership) is not set.
- Any downstream logic expecting `request.current_tenant_id` or membership may behave unexpectedly.

### Breakpoint 2 — `SessionTenantMiddleware` still uses `tenant_id` key name

**File:** `mysite/session_tenant_middleware.py`

```py
tenant_id = request.session.get('tenant_id')
...
tenant = Tenant.objects.filter(pk=tenant_id).first()
...
logger.info(f"... for tenant_id={tenant_id}")
```

- **Observation:** This will *work* with slug PK because it uses `pk=tenant_id`.
- **But:** It is semantically misleading and coupled to a legacy key name.

### Breakpoint 3 — Admin tenant session middleware uses `tenant.id`

**File:** `mysite/admin_tenant_session_middleware.py`

```py
tenant = profile.tenant
tenant_id = tenant.id
request.session['tenant_id'] = tenant.id
logger.info(... tenant_id={tenant.id} ...)
```

- **Why this is a hard bug:** `Tenant` does **not** have `.id` if `slug` is the PK.
- Even though this is wrapped in a try/except, it will throw, and it prevents consistent session alignment on admin requests.

### Breakpoint 4 — Tenant switching API still demands integer tenant_id

**File:** `dose/views/tenant_switch_api.py`

```py
class SwitchTenantSerializer(serializers.Serializer):
    tenant_id = serializers.IntegerField(min_value=1)
...
UserTenantMembership.objects...get(user=request.user, tenant_id=tid)
```

- **Mismatch:** This endpoint is still designed around bigint tenant ids.
- **Impact:** tenant switching will not work correctly in a slug-PK world.

### Breakpoint 5 — Passthrough auth still emits `X-Tenant-ID`

**File:** `dose/middleware/passthrough_auth.py`

```py
if profile and profile.tenant_id:
    return {
        'tenant_id': str(profile.tenant_id),
        'tenant_slug': profile.tenant.slug,
    }
...
headers['X-Tenant-ID'] = tenant_info['tenant_id']
```

- With `UserProfile.tenant` being FK to `Tenant(slug)`, `profile.tenant_id` is likely a **string slug** now.
- Downstream middleware (`TenantContextMiddleware`) only accepts header `X-Tenant-Id` if it is numeric (`isdigit()`), so tenant header propagation becomes inconsistent.

---

## 4) Subscribe flow touchpoints

**File:** `dose/subscription_views.py`

- Subscription creation now uses `tenant_slug` and `Tenant.objects.get(slug=tenant_slug)`.
- This portion appears correctly aligned to slug PK.

However, logs show **DB-level bigint mismatches** still exist in other models used during provisioning:

Example error (from logs):

- `... dose_tenantapp.tenant_id = 'betatest' ... invalid input syntax for type bigint`

That indicates at least one model/table still stores tenant relationship as `BIGINT tenant_id` but runtime is passing slug strings.

---

## 5) Why Google OAuth can still work

Google OAuth login uses allauth social flow + `CustomSocialAccountAdapter`.

That adapter is heavily focused on:

- Ensuring `Site` queries always hit **public schema**
- Ensuring `SocialApp` queries can find config across schemas

It is therefore less likely to be impacted by:

- `TenantContextMiddleware` failing to cast slug → int
- Session tenant alignment based on `tenant_id` semantics

In other words:

- Social login has its own schema resilience layer.
- Password login relies more on the general-purpose middleware stack and session tenant semantics, which are currently mixed.

---

## High-risk files still referencing `tenant_id` (auth/session related)

- `mysite/tenant_context_middleware.py`
  - Uses `tenant_id` everywhere and casts session values to `int`.
- `mysite/admin_tenant_session_middleware.py`
  - Uses `tenant.id` (invalid in slug-PK model).
- `dose/account_adapter.py`
  - Uses `request.session.get("tenant_id")` for tenant selection logic.
- `dose/views/tenant_switch_api.py`
  - Expects integer `tenant_id` input and queries membership by `tenant_id`.
- `dose/middleware/passthrough_auth.py`
  - Emits `X-Tenant-ID` that may now be a slug, but `TenantContextMiddleware` only accepts numeric.
- `mysite/session_tenant_middleware.py`
  - Uses legacy session key name `tenant_id` for schema switching.

---

## Notes / next investigation items

To complete the diagnosis for password login breakage, the next most useful inspection points are:

- `allauth` login POST response and whether `CustomAccountAdapter.get_login_redirect_url()` is reached.
- Any middleware exceptions happening during login response that might prevent session from persisting.
- DB schema types for models that still have bigint `tenant_id` columns (e.g. `TenantApp`, `NavigationPanel`, request tracker models).

---

## Appendix: key code excerpts captured

- `mysite/tenant_context_middleware.py` — int casting of `tenant_id`
- `mysite/admin_tenant_session_middleware.py` — uses `tenant.id`
- `dose/account_adapter.py` — checks `session["tenant_id"]`
- `dose/views/tenant_switch_api.py` — IntegerField tenant_id
- `dose/middleware/passthrough_auth.py` — header `X-Tenant-ID`
