# Cross-App Sync Demo: Dolibarr Customer to Odoo Contact

## Overview

This document describes the end-to-end process for syncing a new customer created in Dolibarr to an Odoo Contact record, using the PolySaaS passthrough, Instruction matching, Atomic Services, and RabbitMQ message queue.

## Architecture

```
User Browser
    |
    | (1) Navigate to /pt/admin/dolibarr/societe/card.php?action=create
    v
Django Application (manage.py runserver)
    |
    |-- ExternalPassthroughMiddleware (dose/passthrough/middleware.py)
    |       Matches /pt/admin/dolibarr/ trigger path
    |       Calls DolibarrPassthroughHandler for URL rewriting
    |       Forwards request to http://localhost:8889
    |       Returns rendered Dolibarr page to browser
    |
    | (2) User fills form, clicks Save (POST)
    v
DoseRequestController (dose/doserequestcontroller.py)
    |       Sees POST to /pt/admin/dolibarr/societe/card.php
    |       Matches Instruction (requestpath substring match)
    |       Fires EndpointDataExtractorService
    |
    v
EndpointDataExtractorService (dose/services/endpoint_data_extractor.py)
    |       Extracts form POST data from request.POST
    |       Normalizes customer fields (name, email, phone, address, etc.)
    |       Publishes to RabbitMQ topic: dolibarr/newcustomer
    |
    v
RabbitMQ (localhost:5672, exchange: polysaas.events)
    |       Message sits in queue: polysaas.crossapp.sync
    |       Routing key: dolibarr/newcustomer
    |
    v
MQQueueMonitor (dose/mq/queue_monitor.py)
    |       Polls queue, picks up message
    |       Builds mock request path: /mq/dolibarr/newcustomer
    |       Matches Instruction for that path
    |       Fires OdooCustomerSyncService
    |
    v
OdooCustomerSyncService (dose/services/odoo_customer_sync.py)
    |       Maps normalized data to Odoo res.partner fields
    |       Connects to Odoo via XML-RPC (localhost:8069)
    |       Creates or updates partner record
    |
    v
Odoo Contact record created
```

## Prerequisites

### Running Services

| Service | Container | URL | Credentials |
|---------|-----------|-----|-------------|
| Django App | host (not containerized) | http://localhost:8000 | Google SSO |
| Dolibarr | polysaas-dolibarr | http://localhost:8889 | admin / admin |
| Odoo | polysaas-odoo | http://localhost:8069 | admin / admin |
| RabbitMQ | polysaas-rabbitmq | http://localhost:15672 | polysaas / polysaas123 |
| Dolibarr DB | polysaas-dolibarr-db (MariaDB) | port 3306 (internal) | dolibarr / dolibarr |
| Odoo DB | polysaas-odoo-db (PostgreSQL) | port 5432 (internal) | odoo / odoo |

Start containers: `docker-compose -f docker-compose.demo-sync.yml up -d`

Start Django: `$env:PYTHONIOENCODING = "utf-8"; python manage.py runserver 8000`

Note: `PYTHONIOENCODING=utf-8` is required on Windows to prevent cp1252 encoding crashes from emoji characters in log/print statements.

### Dolibarr Modules Required

Enable via Dolibarr admin (Setup > Modules/Applications):
- **Third Parties** (Companies and contacts management)
- **API / Web services (REST server)** (for potential future API-based extraction)

### Odoo Modules Required

Installed via: `docker exec polysaas-odoo odoo -d odoo -i crm,contacts --stop-after-init --db_host=odoo-db --db_user=odoo --db_password=odoo --no-http`
- **CRM** (sales pipeline)
- **Contacts** (partner management)

## Step-by-Step Setup Process

### Step 1: Sniff Dolibarr

**Why:** We need to capture Dolibarr's traffic patterns to:
- Identify asset paths (CSS, JS, images, fonts) for URL rewriting in the handler
- Identify the exact form POST path and field names for the "new customer" save action
- Understand any CSRF, session, or authentication requirements

**How:**
1. Navigate to the PolySniffer in Django admin
2. Select the Dolibarr PassThroughEndpoint
3. Use the sniffer proxy to browse Dolibarr:
   - Login page
   - Dashboard
   - Third Parties > New Third Party (the customer creation form)
   - Fill in sample data and Save
4. The sniffer captures all requests/responses as TrafficLog records

**What to look for in captures:**
- Static asset URL patterns (e.g., `/theme/eldy/`, `/core/js/`, `/includes/`)
- The form action URL for saving a new third party (likely `/societe/card.php` with POST method)
- The form field names (e.g., `name`, `email`, `phone`, `address`, `zip`, `town`, `country_code`, `client`)
- CSRF token field name and mechanism
- Session cookie name (likely `DOLSESSID_*`)

### Step 2: Create Dolibarr Handler

**Why:** Without a handler, the passthrough returns raw HTML. The browser can't load CSS/JS/images because their paths (like `/theme/eldy/style.css`) are relative to Dolibarr's origin, not the Django server.

**Pattern to follow:** `nextcloud_handler.py` and `liferay_handler.py` - they use:
- `STATIC_EXTENSIONS`: list of file extensions to rewrite (`.css`, `.js`, `.woff`, `.png`, etc.)
- `STATIC_PREFIXES`: Dolibarr-specific URL prefixes for assets
- Regex replacement of `src=` and `href=` attributes pointing to static assets
- JS injection to patch any XHR/fetch calls that use absolute paths

**File to create:** `dose/passthrough/handlers/dolibarr_handler.py`

**Register in:** `dose/passthrough/handlers/registry.py` - add:
```python
if trigger_path.lower() == 'dolibarr':
    from dose.passthrough.handlers.dolibarr_handler import DolibarrPassthroughHandler
    return DolibarrPassthroughHandler()
```

**AI-assisted:** Run `ai_generate_handler` on the sniffer captures to get a starting point. The generated code is stored in `endpoint.discovered_subpaths['ai_generated_handler']` in the DB. Copy and refine into the handler file.

### Step 3: Create the Instruction for Customer Save

**Why:** The Instruction tells DoseRequestController to fire an atomic service when a specific request path and method are matched.

**What we need from the sniffer:** The exact POST path for saving a new customer in Dolibarr. Expected to be something like:
- `/pt/admin/dolibarr/societe/card.php` (POST, with `action=add` or similar)

**Instruction fields:**
- `requestpath`: The Dolibarr form POST path (from sniffer capture)
- `requestmethod`: POST
- `direction`: REQ
- `executescript`: EndpointDataExtractorService
- `eventKey`: dolibarr.customer.created
- `save_callbackdata`: True
- `description`: Extract new customer data from Dolibarr form POST, publish to RabbitMQ

**How matching works:** DoseRequestController uses substring matching:
```python
instr.requestpath.rstrip('/').lower() in normalized_request_path
```
So an instruction with `requestpath=/societe/card.php` would match any request containing that path.

### Step 4: Update EndpointDataExtractorService

**Why:** The current extractor was written assuming API/JSON payloads. Dolibarr's form submission is a standard HTML form POST (`application/x-www-form-urlencoded`), so the service needs to extract from `request.POST` (Django's parsed form data) rather than `request.body` JSON.

**Fields to extract from Dolibarr form POST** (exact names from sniffer):
- Customer/company name
- Email, phone, address, zip, city, country
- Customer type flag

**Publish to:** RabbitMQ topic `dolibarr/newcustomer`

### Step 5: Create Instruction for MQ Consumer

**Why:** When MQQueueMonitor picks up a message from `dolibarr/newcustomer`, it needs an Instruction to match and fire the Odoo sync service.

**Instruction fields:**
- `requestpath`: /mq/dolibarr/newcustomer
- `requestmethod`: POST
- `direction`: REQ
- `executescript`: OdooCustomerSyncService
- `eventKey`: sync.dolibarr.customer.to.odoo
- `save_callbackdata`: True
- `description`: Sync Dolibarr customer to Odoo partner

**How MQQueueMonitor dispatches:**
1. Consumes message from queue
2. Builds `requestpath = f"/mq/{routing_key}"` (e.g., `/mq/dolibarr/newcustomer`)
3. Creates MockRequest with POST data = message body
4. Matches Instruction and fires OdooCustomerSyncService

### Step 6: Verify OdooCustomerSyncService

**Already written** at `dose/services/odoo_customer_sync.py`. Connects to Odoo via XML-RPC and creates/updates `res.partner` records. Needs verification that:
- The normalized field mapping matches what the extractor publishes
- Odoo connection settings are correct (URL, db name, credentials from PassThroughEndpoint)
- Create/update logic works (search by email first, then by name)

## Testing Plan

1. **Handler test**: Navigate to http://localhost:8000/pt/admin/dolibarr/ - page should render with full CSS/JS styling
2. **Navigation test**: Browse to Third Parties > New Third Party through the passthrough
3. **Form submission test**: Fill in a test customer and click Save
4. **Extraction test**: Check Django console logs for EndpointDataExtractorService output
5. **RabbitMQ test**: Check http://localhost:15672 for message in `polysaas.crossapp.sync` queue
6. **Sync test**: Check Odoo Contacts at http://localhost:8069 for the new partner record
7. **CallBackData test**: Check Django admin for CallBackData records showing the extraction and sync results

## Files Involved

| File | Purpose |
|------|---------|
| `docker-compose.demo-sync.yml` | Container definitions for Dolibarr, Odoo, RabbitMQ |
| `dose/passthrough/middleware.py` | Intercepts /pt/ requests, routes to handler + forwarder |
| `dose/passthrough/forwarding.py` | Strips prefix, forwards to external service, applies handler |
| `dose/passthrough/handlers/registry.py` | Maps trigger_path to handler class |
| `dose/passthrough/handlers/dolibarr_handler.py` | TO BE CREATED - URL rewriting for Dolibarr |
| `dose/doserequestcontroller.py` | Matches Instructions to request paths, fires atomic services |
| `dose/services/endpoint_data_extractor.py` | Extracts form data, publishes to MQ |
| `dose/services/odoo_customer_sync.py` | Consumes MQ message, writes to Odoo |
| `dose/mq/queue_monitor.py` | Polls RabbitMQ, dispatches to MQRequestController |
| `dose/mq/mq_request_controller.py` | Processes MQ messages, matches Instructions |
| `dose/mq/adapters/rabbitmq_adapter.py` | RabbitMQ connection, publish, consume |
| `dose/models/instruction.py` | Instruction model (path matching, atomic service binding) |
| `dose/models/mq_config.py` | MQ connection configuration |
| `dose/models/pass_through_endpoint.py` | Endpoint URL, trigger_path, credentials |

## Known Issues

1. **Windows encoding**: Print/log statements with emoji characters crash on Windows cp1252 console. Fixed by setting `PYTHONIOENCODING=utf-8` before starting Django. Some emoji characters in source files have been replaced with ASCII equivalents.

2. **Orphaned DB columns**: `starting_uri`, `capture_method` exist in the `dose_passthroughendpoint` table but not in the Django model. DB defaults have been set to prevent NOT NULL violations on insert.

3. **Handler return value**: Handlers return `(content, None)` tuples, but `forwarding.py` assigns `content = processed` without unpacking. This needs verification - the PolySniffer proxy correctly unpacks `handler_result[0]` but the main forwarding path may not.

4. **Forwarding path stripping**: Was rewritten to use a generic regex pattern. The original had hardcoded service-specific path replacements. The generic version works but should be verified against all existing passthroughs (Nextcloud, Liferay, PolySysMon, etc.) to ensure no regressions.
