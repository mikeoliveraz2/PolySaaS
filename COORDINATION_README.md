# Mattermost Passthrough — Coordination README

**Session ended:** Worktree `PolySaaS-a136a386`  
**Status:** Partial fix applied, deployment env var needed  
**Next step:** Add `MATTERMOST_ADMIN_TOKEN` to Render deployment, restart, test

---

## What Was Fixed This Session

### 1. Login Bridge No Longer Wraps in Admin Template
**File:** `dose/passthrough/handlers/mattermost_handler.py`

The login bridge (`_serve_login_bridge`) was wrapping its HTML response in the PolySaaS admin template via `_wrap_in_admin_template()`, causing the Mattermost page to be nested inside the PolySaaS chrome (double header/sidebar). **Removed the wrapping.** The bridge now returns a standalone HTML page.

### 2. Credential Lookup Fixed
**File:** `dose/passthrough/handlers/mattermost_handler.py`

The login bridge was trying to auto-login with stale stored credentials (`pst19` for `polysaase2e2` — wrong user). Now it:
- Prefers the current user's email address
- Only auto-submits the login form when stored credentials match the current user
- Falls back to showing the form pre-filled with the user's email for manual entry

**Credential fallback chain (all locations):**
```
mattermost_login_id → mm_login_id → mattermost_username → login_id → user's email
```

### 3. URL Consistency — Render URL
**Files changed:**
- `dose/services/mattermost_tenant_provisioner.py`
- `dose/services/ai_peer_service.py`
- `dose/oauth.py`

Updated default Mattermost URL from `https://mm.polysaas.online` to `https://polysaas-mattermost.onrender.com` everywhere.

### 4. PassThroughEndpoint Upsert Fixed
**File:** `dose/services/mattermost_tenant_provisioner.py`

Changed `_ensure_passthrough_endpoint` to use `endpoint_url` as the lookup key instead of the removed `trigger_path` field.

### 5. Provisioning Consistency
**File:** `dose/services/mattermost_tenant_provisioner.py`

`_store_credentials` now sets all three username keys for consistency:
- `mm_login_id`
- `mattermost_login_id`
- `mattermost_username`

---

## Root Cause of the Login Loop

The tenant `polysaase2e2` was created via subscribe flow, but **Mattermost provisioning failed** because the `MATTERMOST_ADMIN_TOKEN` env var is missing from the Render deployment. This left stale/wrong credentials in the TenantApp (`mattermost_login_id: pst19` — a different tenant's user).

When the user clicked Mattermost in the sidebar:
1. Handler found the stale `pst19` credentials
2. Login bridge auto-submitted them
3. Mattermost rejected them (401)
4. The response was processed by the handler, which detected the 401
5. Handler served the login bridge again
6. Bridge auto-submitted the same wrong credentials → **loop**

---

## What You Need To Do (On Your Laptop)

### Step 1: Add MATTERMOST_ADMIN_TOKEN to Render

1. Go to your Render dashboard → your Django service → Environment
2. Add variable:
   ```
   MATTERMOST_ADMIN_TOKEN=<your-admin-token>
   ```
3. To get the token:
   - Log into Mattermost at `https://polysaas-mattermost.onrender.com`
   - System Console → Integrations → Personal Access Tokens
   - Create one (or use an existing admin token)
   - Copy the token value

### Step 2: Deploy & Restart

1. Push this branch to GitHub (already done: `main` updated)
2. Trigger a deploy on Render (auto-deploy if linked)
3. Wait for the service to restart

### Step 3: Fix Existing Tenant (polysaase2e2)

After restart, you have two options:

**Option A: Re-provision (cleanest)**
```python
# In Django shell on Render
from dose.services.mattermost_tenant_provisioner import provision_mattermost_tenant
from dose.models import Tenant
from django.db import connection

with connection.cursor() as cur:
    cur.execute('SET search_path TO public')
t = Tenant.objects.get(slug='polysaase2e2')
ta = t.tenant_apps.filter(app_name='mattermost').first()

result = provision_mattermost_tenant(
    tenant_schema=t.schema_name,
    tenant_name=t.name,
    admin_email='polysaase2e2@example.com',  # Use actual admin email
    company_name=t.name,
    tenant_app_id=ta.id if ta else None,
    admin_username='polysaase2e2',
    admin_password='PolySaaS2026!',
)
print(result)
```

**Option B: Manual credential fix (quick)**
```python
# In Django shell
from dose.models import TenantApp
from django.db import connection

with connection.cursor() as cur:
    cur.execute('SET search_path TO public')

ta = TenantApp.objects.get(tenant__slug='polysaase2e2', app_name='mattermost')
cfg = ta.extra_config or {}
cfg['mattermost_login_id'] = 'polysaase2e2'  # or the user's email
cfg['mm_login_id'] = 'polysaase2e2'
cfg['mattermost_username'] = 'polysaase2e2'
ta.extra_config = cfg
ta.save(update_fields=['extra_config'])
```

### Step 4: Test

1. Log into PolySaaS as `polysaase2e2`
2. Click "Mattermost" in the sidebar
3. Expected behavior:
   - If token valid → redirects to Town Square, Mattermost loads standalone
   - If no token → login bridge appears with user's email pre-filled
   - Enter password → click Sign In → should succeed and redirect

---

## Files Changed This Session

| File | Change |
|------|--------|
| `dose/passthrough/handlers/mattermost_handler.py` | Removed admin template wrapping; fixed credential fallback chains; login bridge prefers user email; auto-submit only when credentials match user |
| `dose/services/mattermost_tenant_provisioner.py` | Default URL → Render; PassThroughEndpoint upsert uses `endpoint_url`; stores all three username keys |
| `dose/services/ai_peer_service.py` | Default URL → Render |
| `dose/oauth.py` | Mattermost redirect URI → Render |

---

## This Session (Morning Fixes)

### 6. Token Stripping Fix
**File:** `dose/services/mattermost_tenant_provisioner.py`

Added `.strip()` to `_get_admin_token()` to remove trailing newlines from GCP Secret Manager tokens.

### 7. Username & Password Validation
**File:** `dose/services/mattermost_tenant_provisioner.py`

- Added `re` import and username sanitization to ensure Mattermost constraints (starts with letter, only a-z0-9._-)
- Replaced weak `_secrets.token_urlsafe(16)` password generation with `_generate_strong_password()` that includes uppercase, lowercase, number, and symbol

### 8. Sidebar Links Hidden Until Active
**File:** `dose/middleware/jazzmin_tenant_theme.py`

Modified `JazzminTenantThemeMiddleware` to check `TenantApp.status` before adding passthrough links to the sidebar. Links only appear when `status='active'`. Added `_endpoint_to_app_name()` helper to map endpoints to TenantApp app_names.

### 9. Provisioning Green-Bar Messages
**File:** `dose/subscription_views.py`

Modified `_register_provisioning_synchronous` to:
- Accept `request` parameter
- Emit `messages.info()` when provisioning starts
- Emit `messages.success()` when provisioning completes
- Emit `messages.error()` when provisioning fails

---

## Pending (Not Done)

1. **Callback data timestamps** — `CallBackData.pub_date` needs `django.utils.timezone.now` with `auto_now_add=True`.
2. **Mattermost header as `<div>`** — NOT implemented; handler serves full page.

---

## Branch Info

- **Worktree:** `C:\Users\PC\.windsurf\worktrees\PolySaaS\PolySaaS-a136a386`
- **Branch:** `cascade/debugging-mattermost-sso-a136a3` (merged to `main`)
- **Commits pushed:** 8+ commits with fixes
