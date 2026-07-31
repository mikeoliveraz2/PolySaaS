<!-- THIS CODE IS FROZEN — NO CHANGES TO THIS CODE ARE ALLOWED WITHOUT THE OWNER'S PERMISSION -->

# Odoo Passthrough Login Issue (Condo Machine)

**Date:** 2026-07-31  
**Status:** Investigating why Odoo link shows login page instead of embedded app

## Symptom

When clicking the Odoo passthrough link in the admin sidebar (condo machine), the page shows Odoo's login screen instead of the embedded application.

## Root Cause Analysis

The issue is likely one of:

1. **Endpoint URL Mismatch** — The Odoo PassThroughEndpoint in condo's database might be pointing to a production URL (e.g., `https://polysaas-odoo2.onrender.com`) instead of the local Docker address (`http://localhost:8086`).

2. **Starting URI Issue** — The `starting_uri` field might be empty or incorrect, causing Odoo to land on a login page instead of the app entry point.

3. **Session/Cookies** — The Odoo handler's `get_upstream_cookies()` might not be retrieving valid session tokens from the provisioned TenantApp.

## Steps to Debug on Condo

### 1. Check Endpoint Configuration

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

### 2. If Endpoint URL is Wrong

If the condo's endpoint_url is pointing to a production URL (e.g., `https://polysaas-odoo2.onrender.com`), update it:

```python
from django.db import connection
from dose.models import PassThroughEndpoint, Tenant

# Fix public schema
with connection.cursor() as c:
    c.execute('SET search_path TO public')

odoo_ep = PassThroughEndpoint.objects.filter(slug='odoo').first()
if odoo_ep:
    odoo_ep.endpoint_url = 'http://localhost:8086'
    odoo_ep.starting_uri = '/web'
    odoo_ep.save()
    print("✓ Updated PUBLIC odoo endpoint")

# Fix pso5 schema
pso5 = Tenant.objects.get(schema_name='pso5')
with connection.cursor() as c:
    c.execute('SET search_path TO pso5')

odoo_ep = PassThroughEndpoint.objects.filter(slug='odoo').first()
if odoo_ep:
    odoo_ep.endpoint_url = 'http://localhost:8086'
    odoo_ep.starting_uri = '/web'
    odoo_ep.save()
    print("✓ Updated PSO5 odoo endpoint")
```

### 3. Check Odoo Session Provisioning

Verify that the TenantApp for Odoo has valid credentials in `extra_config`:

```python
from dose.models import TenantApp, Tenant

pso5 = Tenant.objects.get(schema_name='pso5')
with connection.cursor() as c:
    c.execute('SET search_path TO pso5')

odoo_app = TenantApp.objects.filter(app_slug='odoo').first()
if odoo_app:
    print(f"Odoo TenantApp extra_config:")
    import json
    print(json.dumps(odoo_app.extra_config, indent=2))
else:
    print("No Odoo TenantApp found in pso5")
```

Look for fields like `odoo_session_id` or `odoo_uid` in the `extra_config`.

## Recent Changes (Commit 06269607)

This commit cleared `starting_uri` for local endpoints to let the upstream app handle redirects. However, Odoo's login page still needs the correct auth flow. Verify:

1. **Endpoint is localhost:8086** (not a production URL)
2. **Starting URI is `/web`** (Odoo's application entry point)
3. **Session credentials exist** in TenantApp.extra_config

## Next Step

Run the diagnostic checks above on the condo machine, then report back with the findings. If the endpoint URL is pointing to production, update it to `http://localhost:8086` and test again.

## Files Involved

- `dose/models/pass_through_endpoint.py` — PassThroughEndpoint model
- `dose/passthrough/handlers/odoo_handler.py` — Odoo-specific passthrough logic
- `dose/passthrough/local_dev_registrations.py` — Local handler registration (recent)
- `dose/passthrough/middleware.py` — Endpoint resolution (recently changed)
