<!-- THIS CODE IS FROZEN — NO CHANGES TO THIS CODE ARE ALLOWED WITHOUT THE OWNER'S PERMISSION -->

# Odoo Passthrough Login Issue (Condo Machine)

**Date:** 2026-07-31  
**Status:** Investigating why Odoo link shows login page instead of embedded app

## Symptom

When clicking the Odoo passthrough link in the admin sidebar (condo machine), the page shows Odoo's login screen instead of the embedded application.

## Root Cause Analysis

**The Odoo handler's `get_upstream_cookies()` returns an empty dict when:**

1. **Missing Credentials** — The TenantApp for Odoo doesn't have `odoo_login` and `odoo_password` in `extra_config`. Without these, the handler can't authenticate to Odoo and returns no session cookies, so the user lands on the login page.

2. **Invalid Session** — The cached `odoo_session_id` has expired (older than 30 minutes), but new credentials aren't available to re-authenticate.

3. **Wrong Endpoint** — The PassThroughEndpoint endpoint_url might point to the wrong Odoo instance (production vs. local Docker).

## Steps to Debug on Condo

### 1. Check Endpoint Configuration

**Expected:** endpoint_url should be the Odoo instance (e.g., `http://localhost:8086` for local Docker or `https://polysaas-odoo2.onrender.com` for production). `starting_uri` should be empty or `/` — Odoo appends `/web` internally.

```bash
cd D:\PolySaaS
python manage.py shell
```

Then run:

```python
from django.db import connection
from dose.models import PassThroughEndpoint, Tenant

# Check public schema
with connection.cursor() as c:
    c.execute('SET search_path TO public')

odoo_ep = PassThroughEndpoint.objects.filter(slug='odoo').first()
print(f"PUBLIC Odoo endpoint:")
print(f"  endpoint_url: {odoo_ep.endpoint_url}")
print(f"  starting_uri: {odoo_ep.starting_uri}")
print(f"  is_enabled: {odoo_ep.is_enabled}")

# Check pso5 schema
pso5 = Tenant.objects.get(schema_name='pso5')
with connection.cursor() as c:
    c.execute(f'SET search_path TO pso5')

odoo_ep = PassThroughEndpoint.objects.filter(slug='odoo').first()
print(f"\nPSO5 Odoo endpoint:")
print(f"  endpoint_url: {odoo_ep.endpoint_url}")
print(f"  starting_uri: {odoo_ep.starting_uri}")
print(f"  is_enabled: {odoo_ep.is_enabled}")
```

**Expected output (laptop):**
```
PUBLIC Odoo endpoint:
  endpoint_url: http://localhost:8086
  starting_uri: /web
  is_enabled: True

PSO5 Odoo endpoint:
  endpoint_url: http://localhost:8086
  starting_uri: /web
  is_enabled: True
```

### 2. Check TenantApp Odoo Credentials (PRIMARY CHECK)

This is the **most likely cause** of the login screen:

```python
from django.db import connection
from dose.models import TenantApp, Tenant
import json

pso5 = Tenant.objects.get(schema_name='pso5')
with connection.cursor() as c:
    c.execute('SET search_path TO pso5')

odoo_app = TenantApp.objects.filter(app_name='odoo', status='active').first()
if odoo_app:
    print(f"Odoo TenantApp found:")
    print(f"  app_slug: {odoo_app.app_slug}")
    print(f"  app_url: {odoo_app.app_url}")
    print(f"\n  extra_config:")
    print(json.dumps(odoo_app.extra_config, indent=4))
else:
    print("❌ No active Odoo TenantApp found in pso5")
```

**What to look for:**

- `odoo_login` — Must exist and be a valid Odoo username
- `odoo_password` — Must exist and be a valid Odoo password  
- `odoo_db` — Database name (optional, defaults to `polysaas_odoo` or `ODOO_SHARED_DB` setting)
- `odoo_session_id` — Cached session token (can be empty if not yet authenticated)

**If `odoo_login` or `odoo_password` are missing:**

Run the Odoo provisioning service to populate them. Contact Michael/Shela for the provisioning command or check `documentation/LOCAL_STANDALONE_STACK.md` for setup instructions.

### 3. If Credentials Exist But Still Showing Login

Enable debug logging in the Odoo handler to see what's happening:

```python
# In dose/passthrough/handlers/odoo_handler.py, the logs will show:
# - "[ODOO HANDLER] get_upstream_cookies: authenticating tenant=..."
# - "[ODOO HANDLER] Using cached Odoo session for tenant=..."
# - "[ODOO HANDLER] get_upstream_cookies: missing odoo_login/password in extra_config"
```

Check server logs (e.g., `runall.ps1` console output) for these messages when you click the Odoo link.

## Recent Changes (Commit 06269607)

This commit changed how endpoints are resolved locally. The local_dev_registrations now explicitly map `localhost:8086 -> OdooPassthroughHandler`. The real issue is credential provisioning: if the TenantApp doesn't have `odoo_login` and `odoo_password`, the handler can't authenticate and the user sees the login page.

## Verification Checklist

- [ ] Odoo endpoint URL is correct (local Docker or production)
- [ ] TenantApp.extra_config has `odoo_login` and `odoo_password`
- [ ] If credentials are missing, provision them (contact Michael/Shela or see LOCAL_STANDALONE_STACK.md)
- [ ] Restart PolySaaS after fixing credentials
- [ ] Hard refresh browser and test again

## Files Involved

- `dose/models/pass_through_endpoint.py` — PassThroughEndpoint model
- `dose/passthrough/handlers/odoo_handler.py` — Odoo-specific passthrough logic
- `dose/passthrough/local_dev_registrations.py` — Local handler registration (recent)
- `dose/passthrough/middleware.py` — Endpoint resolution (recently changed)
