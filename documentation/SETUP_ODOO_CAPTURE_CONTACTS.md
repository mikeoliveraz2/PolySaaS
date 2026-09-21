# Setup: Capture Odoo contacts → Captured Topics

Tenant: **PolySaaS Online** (`slug` / `schema` = `polysaas`)  
Hostinger Docker network: Odoo upstream = `http://odoo:8069`

## What this does

```
Odoo Control Panel → Capture contacts
  → GET res.partner (customer_rank > 0)
  → WebhookMailbox topic RES.odoo.contacts.<user>
  → Captured Topics → Consume to History
  → history_contact (ContactHistory)
```

## 1. Migrate history table (once)

Inside the Django container:

```bash
python manage.py migrate
```

Confirms `0068_contact_history` exists in schema `polysaas` (and `olient` if you use it).

## 2. PassThroughEndpoint (Control Panel home)

Identity is **slug `odoo`**. Upstream must be the compose service, not localhost:

```bash
python manage.py shell -c "
from django.db import connection
from dose.models import PassThroughEndpoint
with connection.cursor() as c:
    c.execute('SET search_path TO \"polysaas\", public')
ep, _ = PassThroughEndpoint.objects.update_or_create(
    slug='odoo',
    defaults={
        'endpoint_url': 'http://odoo:8069',
        'api_endpoint': 'http://odoo:8069/xmlrpc/2',
        'is_enabled': True,
        'show_in_menu': True,
        'menu_title': 'Odoo',
        'menu_sort_order': 20,
        'starting_uri': '/web',
        'passthrough_type': 'scraper',
        'integration_mode': 'web_api',
    },
)
print(ep.slug, ep.endpoint_url, ep.is_enabled)
"
```

Or:

```bash
python manage.py setup_default_passthrough_endpoints \
  --tenant-slug polysaas \
  --odoo-url http://odoo:8069 \
  --mattermost-url http://mattermost:8065
```

(Needs image with commit `61f026d9+` for HubSpot/Slack lines; Odoo update works on older images too if you pass `--odoo-url`.)

**Browse / passthrough URL:** `/pt/admin/odoo/`  
Do **not** use `/pt/admin/localhost:8069/` or `/pt/admin/odoo:8069/`.

## 3. Odoo RPC credentials (TenantApp)

Capture uses JSON/XML-RPC via `load_odoo_rpc_config`:

1. `TenantApp.extra_config` for app `odoo` (preferred): `odoo_url`, `odoo_db`, `odoo_login` / `odoo_username`, `odoo_password`
2. Else PassThroughEndpoint URL
3. Else env: `ODOO_SHARED_URL`, `ODOO_SHARED_DB`, `ODOO_XMLRPC_ADMIN_LOGIN`, `ODOO_XMLRPC_ADMIN_PASSWORD`

On Hostinger compose, Django usually has `ODOO_SHARED_URL=http://odoo:8069` and `ODOO_SHARED_DB=polysaas_odoo`. Ensure password is set in env or on TenantApp.

Check:

```bash
python manage.py shell -c "
from django.db import connection
from django.conf import settings
from dose.models import TenantApp
from dose.tenant_app_lookup import get_tenant_app_in_schema
from dose.models import Tenant
t = Tenant.objects.get(slug='polysaas')
print('env', settings.ODOO_SHARED_URL, settings.ODOO_SHARED_DB)
with connection.cursor() as c:
    c.execute('SET search_path TO \"polysaas\", public')
ta = get_tenant_app_in_schema(t, 'odoo')
extra = (ta.extra_config if ta else None) or {}
print('TenantApp', ta and ta.status, {k: ('***' if 'pass' in k else extra.get(k)) for k in ('odoo_url','odoo_db','odoo_login','odoo_username','odoo_password')})
"
```

## 4. Bookmarks (Capture contacts button)

Default Odoo Control Panel bookmark is seeded as `odoo.capture_contacts` when endpoints use default bookmarks. Open:

`/dose/apps/<endpoint_host>/`

where `endpoint_host` is the netloc of `endpoint_url` (e.g. `odoo:8069`), **or** open Odoo from the sidebar and use the Control Panel.

Click **Capture contacts**.

## 5. Consume to history

1. Admin → **Captured Topics**
2. Open topic named like **Odoo contacts** (`RES.odoo.contacts.<username>`)
3. **Consume to History** (or Consume all pending)
4. **Topic History** → rows in `ContactHistory` (`source_app=odoo`)

## Checklist

| Step | OK when |
|------|---------|
| Migrate | `history_contact` in `polysaas` |
| Endpoint | slug `odoo`, URL `http://odoo:8069`, enabled |
| RPC | auth works (env or TenantApp password) |
| Capture | mailbox row appears under Captured Topics |
| Consume | Topic History shows name / email / company |

## Local (Waitress + Docker Odoo)

Use `http://localhost:8086` instead of `http://odoo:8069` for `endpoint_url` / `--odoo-url`.
