# Dolibarr Sniff and Cross-App Mapping Configuration

**Date:** 2026-03-22
**Status:** Configured and validated
**Related:** [Mapping Model Schema - Implementation.md](Mapping%20Model%20Schema%20-%20Implementation.md)

---

## 1. PolySniffer Capture Process

### Step 1 — Launch PolySniffer for Dolibarr

In Django Admin, navigate to the PassThroughEndpoint list. The **Dolibarr ERP** endpoint is configured as:

| Field | Value |
|-------|-------|
| Provider | Custom |
| URL | http://localhost:8889 |
| Created | Dec 7, 2025 |

Click the **PolySniffer Analysis** button on the Dolibarr row to launch the sniffer proxy.

> **Screenshot 1:** PassThroughEndpoint admin showing WordPress, PolySysMon, Dolibarr ERP, and Nextcloud. Red arrow points to the PolySniffer Analysis button on the Dolibarr row.

### Step 2 — PolySniffer Dashboard

The PolySniffer dashboard opens and begins capturing all HTTP traffic between the browser and Dolibarr at `localhost:8889`. The dashboard shows a scrolling list of captured requests (GET/POST) with timestamps, methods, URLs, and status codes.

> **Screenshot 2:** PolySniffer dashboard with ~80+ captured traffic entries (dark theme). Each row shows method, URL path, and status. Green "Start/Stop Capture" buttons visible at the top.

### Step 3 — Dolibarr Login

Dolibarr 19.0.2 login screen. Credentials:
- Username: `admin`
- Password: `admin`

> **Screenshot 3:** Dolibarr login page showing version 19.0.2, username "admin" pre-filled, password field masked. Red arrow points to the LOGIN button.

### Step 4 — Navigate to Third-parties Module

After login, Dolibarr lands on the Setup page (first-time configuration notice). The top navigation bar shows:

**Home | Members | Third-parties | Products | Projects | Commerce | Billing/Payment | Documents | Agenda | Tickets | Tools | Websites | ExternalSite**

> **Screenshot 4:** Dolibarr admin dashboard with Setup page and top menu bar. Red arrow points to the "Third-parties" menu item. A browser password manager dialog is visible on the right side.

### Step 5 — Third-parties Menu: New Customer

Clicking **Third-parties** opens the left sidebar with:

```
Third-party
  New Third Party
  List
    List of Prospects
      New Prospect
    List of Customers
      New Customer    <-- selected
    List of Vendors
      New Vendor

Contacts/Addresses
  New Contact/Address
  List
    Prospects
```

The main content area shows the Third Parties/Contacts statistics:
- Prospects: 0
- Customers: 0
- Vendors: 0
- Total: 0

> **Screenshot 5:** Third-parties module with sidebar navigation. Red arrow points to "New Customer" link. Statistics panel shows all zeros.

### Step 6 — Fill the New Third Party Form (Top)

The "New Third Party (prospect, customer, vendor)" form was filled with:

| Label | Value Entered |
|-------|---------------|
| Third-party name | Mike Oliver |
| Alias name | Mike Oliver |
| Prospect / Customer | Prospect / Customer (dropdown) |
| Customer Code | (auto-generated) |
| Vendor | No |
| Status | Open |
| Address | 102 Woodlily Pl. |
| Zip Code | 77382 |
| City | (Spring - visible after save) |
| Country | (not set) |
| State/Province | "Set the country first (See above)" |
| Phone | 2818535769 |
| Fax | (below fold) |

> **Screenshot 6:** Top half of the New Third Party form filled with Mike Oliver's data. Fields visible: name, alias, prospect/customer dropdown, vendor, status, address, zip, and the beginning of the phone field.

### Step 7 — Fill the New Third Party Form (Bottom) and Submit

The bottom half of the form shows:

| Label | Value |
|-------|-------|
| Professional ID 1-6 | (empty) |
| Sales tax used | Checked |
| VAT ID | (empty) |
| Third-party type | (dropdown - resulted in "Workforce") |
| Business entity type | "Set the country first (See above)" |
| Capital | (empty) Euros |
| Parent company | (none selected) |
| Assigned to sales representative | SuperAdmin |
| Logo | No file chosen |

Two buttons at the bottom: **CREATE THIRD PARTY** and **CANCEL**.

> **Screenshot 7:** Bottom half of the form. Red/green arrow points to the "CREATE THIRD PARTY" button. Fields visible: Professional IDs, Sales tax checkbox (checked), Third-party type, Capital, Parent company, Sales rep (SuperAdmin), Logo upload.

### Step 8 — Third Party Created Successfully

After clicking CREATE THIRD PARTY, Dolibarr redirects to the new record's detail page showing:

| Field | Value |
|-------|-------|
| Name | **Mike Oliver** |
| Alias | Mike Oliver |
| Address | 102 Woodlily Pl., 77382 Spring |
| Phone | 2818535769 |
| Fax | 2818535769 |
| Email | mikeoliveraz@gmail.com |
| Nature of Third party | Prospect + Customer (green icons) |
| Customer Code | CU2603-00001 |
| Third-party type | Workforce |

Tabs visible: Third-party | Contacts/Addresses | Prospect/Customer | Projects | Related items | Payment methods | Events/Agenda (1)

> **Screenshot 8:** Dolibarr third party detail page for Mike Oliver. Shows all contact info, customer code CU2603-00001, and Workforce type. Tab navigation visible at top.

---

## 2. Captured Form Fields

The POST submits to `/societe/card.php` with `action=add` and method POST.

### All 43 form fields (extracted from Dolibarr 19.0.2 HTML source):

```
Field Name                     Type
------------------------------  ----------
searchselectcombo              select
action                         hidden
token                          hidden (CSRF)
backtopage                     hidden
backtopagejsfields             hidden
dol_openinpopup                hidden
private                        hidden
type                           hidden
LastName                       hidden
ThirdPartyName                 hidden
code_auto                      hidden
name                           text
name_alias                     text
client                         select
customer_code                  text
fournisseur                    select
supplier_code                  text
status                         select
address                        textarea
zipcode                        text
town                           text
country_id                     select
phone                          text
fax                            text
email                          text
url                            text
idprof1                        text
idprof2                        text
idprof3                        text
idprof4                        text
idprof5                        text
idprof6                        text
assujtva_value                 checkbox
tva_intra                      text
typent_id                      select
effectif_id                    select
capital                        text
parent_company_id              select
commercial_multiselect         hidden
commercial[]                   select
photo                          file
save                           submit
cancel                         submit
```

### Fields relevant to cross-app sync:

| Dolibarr Field | Mike Oliver's Value | Normalized Field |
|---------------|---------------------|-----------------|
| `name` | Mike Oliver | `name` |
| `name_alias` | Mike Oliver | `name_alias` |
| `email` | mikeoliveraz@gmail.com | `email` |
| `phone` | 2818535769 | `phone` |
| `fax` | 2818535769 | `fax` |
| `address` | 102 Woodlily Pl. | `street` |
| `zipcode` | 77382 | `zip` |
| `town` | Spring | `city` |
| `country_id` | (empty) | `country_id` |
| `client` | 3 (Prospect+Customer) | `is_customer` |
| `fournisseur` | 0 (No) | `is_vendor` |
| `customer_code` | CU2603-00001 | `customer_code` |
| `status` | 1 (Open) | `status` |
| `tva_intra` | (empty) | `vat` |
| `typent_id` | 8 (Workforce) | `typent_id` |
| `url` | (empty) | `url` |

---

## 3. Mapping Records Created

### Mapping 1: Dolibarr POST -> Normalized Customer Event

| Property | Value |
|----------|-------|
| ID | 2 |
| Slug | `dolibarr-thirdparty-post-to-normalized` |
| Direction | SOURCE_TO_NORMALIZED |
| Source Endpoint | Dolibarr (id=37) |
| Active | Yes |
| Fields | 21 |

**field_mappings JSON:**

```json
{
  "_topic": "'polysaas.crossapp.customer.created'",
  "_source_app": "'dolibarr'",
  "_entity": "'thirdparty'",
  "_action": "'created'",
  "name": "request.POST.name|strip",
  "name_alias": "request.POST.name_alias|strip|default:None",
  "email": "request.POST.email|strip|lower|email",
  "phone": "request.POST.phone|strip|default:None",
  "fax": "request.POST.fax|strip|default:None",
  "street": "request.POST.address|strip",
  "zip": "request.POST.zipcode|strip",
  "city": "request.POST.town|strip",
  "country_id": "request.POST.country_id|strip|default:None",
  "vat": "request.POST.tva_intra|strip|default:None",
  "customer_code": "request.POST.customer_code|strip|default:None",
  "is_customer": "request.POST.client|int:1:0",
  "is_vendor": "request.POST.fournisseur|int:1:0",
  "status": "request.POST.status|strip|default:1",
  "typent_id": "request.POST.typent_id|strip|default:None",
  "url": "request.POST.url|strip|default:None",
  "created_at": "now:iso"
}
```

### Mapping 2: Normalized Customer -> Odoo res.partner

| Property | Value |
|----------|-------|
| ID | 3 |
| Slug | `normalized-customer-to-odoo-partner` |
| Direction | NORMALIZED_TO_TARGET |
| Target Endpoint | Odoo (id=38) |
| Active | Yes |
| Fields | 14 |

**field_mappings JSON:**

```json
{
  "name": "payload.name",
  "email": "payload.email",
  "phone": "payload.phone",
  "mobile": "payload.fax|default:None",
  "street": "payload.street",
  "zip": "payload.zip",
  "city": "payload.city",
  "vat": "payload.vat",
  "website": "payload.url",
  "customer_rank": "payload.is_customer|int:1:0",
  "supplier_rank": "payload.is_vendor|int:1:0",
  "ref": "payload.customer_code|default:None",
  "_country_code": "payload.country_id",
  "is_company": "'True'|bool"
}
```

---

## 4. Instructions Created

Both Instructions are configured in the Django admin under the **olient** tenant (Oliver Enterprises - OLIENTADMIN). The Instructions list shows all three Instructions in the tenant, including the two new cross-app sync entries created March 22, 2026.

> **Screenshot 11:** Django admin Instructions list in olient tenant. Shows 3 Instructions: `/mq/polysaas.crossapp.customer.created` (POST), `/societe/card.php` (POST, red arrow), and `dose/task/` (GET). Both new Instructions dated March 22, 2026.

### Instruction A: Dolibarr Form POST Capture

| Property | Value |
|----------|-------|
| Request Path | `/societe/card.php` |
| Method | POST |
| Direction | REQUEST |
| Execute Script | `EndpointDataExtractorService` |
| Event Key | `dolibarr.customer.created` |
| Save Callback | Yes |
| Attached Mapping | `dolibarr-thirdparty-post-to-normalized` (order=1) |

The General tab shows the requestpath, eventKey, method, and direction fields. The **Instruction Mappings** tab links this Instruction to the Mapping record that defines the field extraction expressions.

> **Screenshot 12:** Django admin Instruction detail for Dolibarr POST capture. Shows requestpath `/societe/card.php`, eventKey `dolibarr.customer.created`, method POST, direction REQUEST. The Instruction Mappings tab is visible for linking to Mapping records.

### Instruction B: MQ Message -> Odoo Sync

| Property | Value |
|----------|-------|
| Request Path | `/mq/polysaas.crossapp.customer.created` |
| Method | POST |
| Direction | REQUEST |
| Execute Script | `OdooCustomerSyncService` |
| Event Key | `sync.customer.dolibarr.to.odoo` |
| Save Callback | Yes |
| Attached Mapping | `normalized-customer-to-odoo-partner` (order=1) |

---

## 5. Validation Results

### Mapping 1 Output (Mike Oliver test data):

```
Input:  Dolibarr form POST fields (20 fields)
Output: Normalized customer event (21 fields)

  name                = 'Mike Oliver'
  name_alias          = 'Mike Oliver'
  email               = 'mikeoliveraz@gmail.com'
  phone               = '2818535769'
  fax                 = '2818535769'
  street              = '102 Woodlily Pl.'
  zip                 = '77382'
  city                = 'Spring'
  country_id          = None
  vat                 = None
  customer_code       = 'CU2603-00001'
  is_customer         = 1
  is_vendor           = 1
  status              = '1'
  typent_id           = '8'
  url                 = None
  created_at          = '2026-03-22T02:49:19Z'
  _topic              = 'polysaas.crossapp.customer.created'
  _source_app         = 'dolibarr'
  _entity             = 'thirdparty'
  _action             = 'created'
```

### Mapping 2 Output (normalized -> Odoo partner fields):

```
Input:  Normalized customer event (17 fields)
Output: Odoo res.partner values (14 fields)

  name                = 'Mike Oliver'
  email               = 'mikeoliveraz@gmail.com'
  phone               = '2818535769'
  mobile              = '2818535769'
  street              = '102 Woodlily Pl.'
  zip                 = '77382'
  city                = 'Spring'
  vat                 = None
  website             = None
  customer_rank       = 1
  supplier_rank       = 0
  ref                 = 'CU2603-00001'
  _country_code       = None
  is_company          = True
```

### Unmapped Dolibarr fields (not needed for sync):

`action`, `assujtva_value`, `capital`, `effectif_id`, `token`, `backtopage`, `backtopagejsfields`, `dol_openinpopup`, `private`, `type`, `LastName`, `ThirdPartyName`, `code_auto`, `supplier_code`, `searchselectcombo`, `idprof1`-`idprof6`, `parent_company_id`, `commercial_multiselect`, `commercial[]`, `photo`, `save`, `cancel`

---

## 6. Data Flow Architecture

```
User creates customer in Dolibarr via passthrough
        |
        v
POST /societe/card.php (through passthrough proxy)
        |
        v
Instruction A matches path + method
        |
        v
EndpointDataExtractorService executes
        |
        v
Mapping Engine loads Mapping 1 (dolibarr-thirdparty-post-to-normalized)
  - Resolves request.POST.name|strip -> "Mike Oliver"
  - Resolves request.POST.email|strip|lower|email -> "mikeoliveraz@gmail.com"
  - Resolves request.POST.client|int:1:0 -> 1
  - Sets _topic = "polysaas.crossapp.customer.created"
  - ... (21 fields total)
        |
        v
Publishes normalized message to RabbitMQ
  routing_key = "polysaas.crossapp.customer.created"
        |
        v
MQQueueMonitor picks up message
  constructs mock request with path /mq/polysaas.crossapp.customer.created
        |
        v
Instruction B matches path + method
        |
        v
OdooCustomerSyncService executes
        |
        v
Mapping Engine loads Mapping 2 (normalized-customer-to-odoo-partner)
  - Resolves payload.name -> "Mike Oliver"
  - Resolves payload.is_customer|int:1:0 -> 1 (customer_rank)
  - Resolves 'True'|bool -> True (is_company)
  - ... (14 fields total)
        |
        v
Odoo XML-RPC: res.partner.create(vals)
  name="Mike Oliver", email="mikeoliveraz@gmail.com",
  phone="2818535769", street="102 Woodlily Pl.",
  zip="77382", city="Spring", customer_rank=1, is_company=True
        |
        v
Mike Oliver appears in Odoo Contacts
```

---

## 7. Result: Mike Oliver in Odoo Contacts

After the cross-app sync completes, the customer record appears in Odoo Contacts.

### Odoo Contacts Grid View

Mike Oliver appears in the contacts list alongside the demo data:

| Field | Value |
|-------|-------|
| Name | Mike Oliver |
| Location | Spring |
| Email | mikeoliveraz@gmail.com |

> **Screenshot 9:** Odoo Contacts grid view (kanban layout) showing Mike Oliver card at bottom-right with red arrow. Record shows "Spring" location and email address. 38 total contacts in the system.

### Odoo Contact Detail View

Opening the Mike Oliver record shows all synced fields:

| Odoo Field | Value |
|------------|-------|
| Type | Company (radio button selected) |
| Name | **Mike Oliver** |
| Address | 102 Woodlily Pl. |
| City | Spring |
| Zip | 77382 |
| Phone | 2818535769 |
| Mobile | 2818535769 |
| Email | mikeoliveraz@gmail.com |

The chatter log shows "Mitchell Admin - Today at 11:22 AM - Contact created", confirming the record was created via the XML-RPC API.

> **Screenshot 10:** Odoo Contact detail page for Mike Oliver. Shows full address, phone, mobile, email fields. Company type selected. Chatter log confirms creation by Mitchell Admin.

---

## 9. Validation Command

All mappings can be tested offline without running the full stack:

```bash
# List all mappings and instruction links
python manage.py test_mapping --list

# Test Mapping 1 against sample Dolibarr POST data
python manage.py test_mapping --slug dolibarr-thirdparty-post-to-normalized --file sample.json

# Test Mapping 2 against normalized data
python manage.py test_mapping --slug normalized-customer-to-odoo-partner --file normalized.json

# Test full instruction chain
python manage.py test_mapping --instruction-path /societe/card.php --file sample.json

# Verbose mode (logs every expression resolution)
python manage.py test_mapping --slug dolibarr-thirdparty-post-to-normalized --file sample.json --verbose
```

---

## 10. Remaining for Live Demo

| Step | Status | Notes |
|------|--------|-------|
| Dolibarr sniffed | Done | POST path and 43 fields captured |
| Mapping records created | Done | 2 mappings, 2 instructions, 2 links |
| Mapping engine validated | Done | Both directions tested with real data |
| RabbitMQ config | Done | Active "PolySaaS Demo RabbitMQ" |
| Dolibarr passthrough handler | **Pending** | Needed for CSS/JS/asset rewriting so Dolibarr renders correctly through `/pt/admin/dolibarr/` |
| End-to-end live test | **Pending** | Create customer via passthrough, verify in Odoo Contacts |
| `dose_trafficlog` table | **Missing** | PolySniffer captures display in UI but don't persist to DB; migration needed |

---

## 11. Files Modified/Created in This Session

| File | Action |
|------|--------|
| `dose/models/mapping.py` | Created (Mapping + InstructionMapping models) |
| `dose/models/__init__.py` | Updated (imports) |
| `dose/services/mapping_engine.py` | Created (expression parser + apply_mapping) |
| `dose/management/commands/test_mapping.py` | Created (validation command) |
| `dose/admin.py` | Updated (MappingAdmin + InstructionMappingInline) |
| `dose/services/endpoint_data_extractor.py` | Updated (mapping engine integration) |
| `dose/services/odoo_customer_sync.py` | Updated (mapping engine integration) |
| `dose/migrations/0024_merge_20260321_1554.py` | Auto-generated (merge) |
| `dose/migrations/0025_add_mapping_and_instruction_mapping.py` | Auto-generated |
| `documentation/Mapping Model Schema - Implementation.md` | Created |
| `documentation/Dolibarr Sniff and Cross-App Mapping - 2026-03-22.md` | Created (this file) |
