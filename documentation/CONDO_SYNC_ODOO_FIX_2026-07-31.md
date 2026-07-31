<!-- THIS CODE IS FROZEN — NO CHANGES TO THIS CODE ARE ALLOWED WITHOUT THE OWNER'S PERMISSION -->

# Condo Machine Sync — Odoo Passthrough Fix (2026-07-31)

**From:** Laptop (Michael)  
**To:** Condo (Shela)  
**Date:** Friday, Jul 31, 2026  
**Status:** Laptop complete, ready for condo sync

---

## What Changed on Laptop

✅ **Fixed Passthrough Sidebar**
- Copied all 5 PassThroughEndpoints from public schema to pso5 tenant schema
- Sidebar now shows: Odoo, Mattermost, NextCloud, Dolibarr, HubSpot

✅ **Fixed Odoo Link**
- Cleared `starting_uri` on Odoo PassThroughEndpoint (both public and pso5)
- Link is now bare base (`/pt/admin/localhost:8086/`) instead of `/pt/admin/localhost:8086/web`
- Odoo now redirects internally to `/web` after handler injection

✅ **Code Committed & Pushed**
- `scripts/fix_odoo_starting_uri.py` — Fix script to apply to condo
- `documentation/ODOO_PASSTHROUGH_DEBUG_CONDO.md` — Debug guide

---

## Why This Fix Works

**The Problem:** With `starting_uri = '/web'`, the initial request goes to `http://localhost:8086/web`. Odoo then tries to redirect to `/web/login.php`, but the handler's path handling breaks during the double-redirect. The user sees a login page instead of the app.

**The Solution:** With empty `starting_uri = ''`, the initial request goes to `http://localhost:8086/` (bare base). Odoo redirects to `/web/login.php` from the root, which the handler correctly processes. The user sees the app.

---

## What Condo Needs to Do

### Step 1: Pull Latest Changes

```bash
cd D:\PolySaaS
git pull origin main
```

### Step 2: Apply the Fix Script

This clears `starting_uri` on Odoo endpoints (same as laptop):

```bash
python manage.py shell
exec(open('scripts/fix_odoo_starting_uri.py').read())
```

Expected output:
```
Clearing Odoo starting_uri...
  PUBLIC: '/web' -> ""
  pso5: '/web' -> ""
✅ Done. Restart PolySaaS and test Odoo link.
```

### Step 3: Restart PolySaaS

```bash
# Stop current runall
# Run fresh start
powershell -ExecutionPolicy Bypass -File .\runall.ps1
```

### Step 4: Hard Refresh Browser

- Go to `http://localhost:8000`
- Hard refresh (Ctrl+Shift+R)
- Click the Odoo link in the sidebar

**Expected result:** Odoo page loads (or login screen if no credentials provisioned)

---

## If Odoo Shows Login Screen

This means the TenantApp for Odoo doesn't have credentials. Check:

```bash
python manage.py shell
```

Then:

```python
from django.db import connection
from dose.models import TenantApp
import json

with connection.cursor() as c:
    c.execute('SET search_path TO pso5')

odoo_app = TenantApp.objects.filter(app_name='odoo', status='active').first()
if odoo_app:
    print(json.dumps(odoo_app.extra_config, indent=2))
else:
    print("❌ No active Odoo TenantApp found")
    print("Must provision Odoo credentials (odoo_login, odoo_password)")
```

**To provision:** Run the Odoo provisioning service or manually create TenantApp with credentials:

```python
from dose.models import TenantApp, Tenant

pso5 = Tenant.objects.get(schema_name='pso5')
with connection.cursor() as c:
    c.execute('SET search_path TO pso5')

# If no TenantApp exists, create one
odoo_app, created = TenantApp.objects.get_or_create(
    tenant=pso5,
    app_name='odoo',
    defaults={
        'app_slug': 'odoo',
        'app_url': 'http://localhost:8086',
        'status': 'active',
        'extra_config': {
            'odoo_login': '<username>',  # e.g., admin
            'odoo_password': '<password>',
            'odoo_db': 'polysaas_odoo',
        }
    }
)

if created:
    print(f"✅ Created Odoo TenantApp for pso5")
else:
    print(f"Odoo TenantApp already exists: {odoo_app.extra_config}")
```

---

## What Still Works (No Changes Needed)

- CloudSQL sync credentials (from secret manager or .env)
- Passthrough middleware and handlers
- All other bundled apps (Mattermost, NextCloud, etc.)

---

## Verification Checklist

- [ ] `git pull origin main` completes
- [ ] `scripts/fix_odoo_starting_uri.py` runs successfully
- [ ] PolySaaS restart completes
- [ ] Browser hard refresh done
- [ ] Sidebar shows 5 passthrough services
- [ ] Odoo link shows app (or login screen if not provisioned)

---

## Files Modified/Created

| File | Status |
|------|--------|
| `scripts/fix_odoo_starting_uri.py` | **NEW** — Fix script |
| `documentation/ODOO_PASSTHROUGH_DEBUG_CONDO.md` | **UPDATED** — Debug guide |
| Database (pso5 schema) | **MODIFIED** — `PassThroughEndpoint.starting_uri` cleared |

---

## Questions?

If anything fails or is unclear, check `documentation/ODOO_PASSTHROUGH_DEBUG_CONDO.md` for detailed debugging steps.

**Timeline expectation:** ~5 minutes to sync and test.
