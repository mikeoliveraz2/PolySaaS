# BINGO — Subscribe & Login Flow
**Date:** 2026-04-03  
**Tested by:** demoadmin_123 (Demo Corporation tenant)  
**Status:** ✅ COMPLETE — Full end-to-end flow confirmed working

---

## What Was Built & Fixed

### 1. Subscribe Form — Password Show/Hide
- 👁 eye icon button on the password field toggles between `type="password"` and `type="text"`
- Same eye icon added to the login page password field

### 2. Subscribe Success — Login Link
- On successful subscription the form shows:
  *"Subscription saved! **Click here to log in** — redirecting in 4 seconds…"*
- Link routes through `/accounts/logout/?next=/accounts/login/` to clear any existing session before landing on the login page
- Auto-redirects after 4 seconds as a fallback
- **Fix:** `looksOk` check simplified — any clean 2xx response without an `error`/`detail` field is treated as success (previous check required `plan_tier` + `id` and was too strict)

### 3. Subscribe Success — Credentials Pre-Fill
- On success the form captures username and password from the subscribe fields and saves to `sessionStorage` (key: `polysaas_new_user_creds`)
- The login page reads and clears this key on load, pre-fills the Username and Password fields
- A green banner confirms: *"✅ Your new account 'demoadmin_123' has been pre-filled. Click Login to continue."*

### 4. Session Clearing
- The success redirect goes through `/accounts/logout/` first, clearing the old user's session (e.g. demouser, olientAdmin) before the new user logs in

### 5. subscribe View — `search_path=public` Before User Creation
- **Bug:** `User.objects.create_user` ran while `search_path` was set to the logged-in user's tenant schema (e.g. `olient`), potentially writing the new user to the wrong schema
- **Fix:** `SET search_path TO public` is explicitly run inside the `transaction.atomic()` block before any `User` or `Tenant` ORM calls, ensuring auth_user always lands in the public schema

### 6. Schema Name — Hyphens in Slugs
- **Bug:** `SET search_path TO demo-c,public;` fails — PostgreSQL requires double-quoting for identifiers with hyphens
- **Fix:** All 14 production files updated to use `f'SET search_path TO "{schema_name}",public;'`
- **Lesson:** A broken automated fix script first introduced `{"schema_name"}` (string literal instead of variable), breaking ALL tenant logins; corrected with targeted StrReplace on each file

### 7. Login Page — Custom Template
- Replaced `{{ form.as_p }}` with individually rendered fields so the sessionStorage pre-fill JS can target `id_login` and `id_password`
- Added 👁 show/hide password toggle
- Added Google Login button with Google icon
- Demo credentials box updated to correct passwords (9-char, special char compliant):
  - User: `demouser` / `demouser_123`
  - Admin: `adminuser` / `adminuser_123`

---

## End-to-End Flow Confirmed

```
/dose/subscribe/
  ↓  Fill form (tenant, username, password, apps, plan, card)
  ↓  Click Subscribe & Pay
  ↓  Stripe charge
  ↓  DB: public.auth_user created, Tenant created, schema provisioned
  ↓  "Subscription saved! Click here to log in"
  ↓  Auto-redirect → /accounts/logout/ → /accounts/login/
  ↓  Login form pre-filled from sessionStorage (username + password)
  ↓  Click Login
  ↓  /admin/ — correct tenant name in navbar
     Two-column admin dashboard ✅
```

**Tested tenant:** Demo Corporation (`democ`) — user `demoadmin_123`  
**Result:** Admin dashboard shows "DEMO CORPORATION - DEMOADMIN_123" ✅

---

## Files Modified
| File | Change |
|------|--------|
| `dose/templates/dose/subscribe.html` | Eye toggle, success login link, looksOk fix |
| `templates/account/login.html` | Full rewrite — individual fields, pre-fill JS, eye toggle, demo creds |
| `dose/subscription_views.py` | `SET search_path TO public` before user/tenant creation |
| 14× `*.py` production files | Double-quote schema names in `SET search_path` calls |

---

**BINGO** ✅  
Subscribe → pay → login link → pre-filled login → admin dashboard. Complete.
