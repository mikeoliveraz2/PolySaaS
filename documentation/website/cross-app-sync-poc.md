# Cross-Application Sync POC (Dolibarr → Odoo)

**Canonical public page (layout + dark mode + all screenshots):**  
https://polysaas.online/cross-app-sync/

**Related links:** [Dynamic Orchestration](https://polysaas.online/dynamic-orchestration/) · [PolySniffer](https://polysaas.online/polysniffer/)

This file is kept in git as the **textual mirror** of that page. When WordPress copy or media changes, update this document to match and push `main`.

**WordPress:** page id `2700`, slug `cross-app-sync`. REST `modified_gmt` may stay old if only media is replaced; **screenshot URLs below** were verified against live `content.rendered` (assets under `/wp-content/uploads/2026/03/`).

---

## Title block (as on page)

- **Heading:** Cross-Application Sync  
- **Subhead:** Dolibarr to Odoo Customer Sync via Dynamic Orchestration  
- **Tagline:** Demonstrated March 22, 2026 using PolySniffer, Mapping Engine, and RabbitMQ  

**Intro:** Live demonstration of cross-application sync: create a new **customer in Dolibarr ERP** and automatically synchronize to **Odoo CRM** as a contact/partner. Uses **PolySniffer** for traffic capture, **Mapping Engine** for field transformation, **RabbitMQ** as the message broker, and **Dynamic Orchestration** to wire it together with **zero code changes** to mapping rules.

---

## End-to-end data flow

1. User creates customer in Dolibarr via Passthrough Proxy  
2. **Instruction A** matches `POST` … `/societe/card.php`  
3. Mapping Engine extracts & normalizes **21** fields from the POST body  
4. Normalized event published to RabbitMQ: `polysaas.crossapp.customer.created`  
5. MQ Monitor picks up message, triggers **Instruction B**  
6. Mapping Engine transforms normalized data to **14** Odoo partner fields  
7. Odoo XML-RPC: `res.partner.create()` — customer appears in Odoo Contacts  

---

## Screenshots on the live page (current assets)

| # | Step / section | Alt text (from page) | Image URL |
|---|----------------|----------------------|-----------|
| 1 | PolySniffer launch | PassThrough endpoint admin with PolySniffer Analysis button for Dolibarr | https://polysaas.online/wp-content/uploads/2026/03/crossapp-passthrough-endpoints-admin-scaled.png |
| 2 | Live capture | PolySniffer live capture dashboard with Dolibarr traffic entries | https://polysaas.online/wp-content/uploads/2026/03/crossapp-polysniffer-dolibarr-capture-scaled.png |
| 3 | Login | Dolibarr 19.0.2 login screen | https://polysaas.online/wp-content/uploads/2026/03/crossapp-dolibarr-login-scaled.png |
| 4 | Third-parties | Dolibarr admin with Third-parties menu highlighted | https://polysaas.online/wp-content/uploads/2026/03/crossapp-dolibarr-setup-thirdparties-scaled.png |
| 5 | New Customer | Third-parties sidebar with New Customer highlighted | https://polysaas.online/wp-content/uploads/2026/03/crossapp-dolibarr-thirdparties-menu-scaled.png |
| 6 | Form | Dolibarr New Third Party form filled with Mike Oliver data | https://polysaas.online/wp-content/uploads/2026/03/crossapp-dolibarr-new-thirdparty-form-scaled.png |
| 7 | Submit | Create Third Party button at bottom of Dolibarr form | https://polysaas.online/wp-content/uploads/2026/03/crossapp-dolibarr-create-thirdparty-submit-scaled.png |
| 8 | Created in Dolibarr | Mike Oliver customer card in Dolibarr showing all synced fields | https://polysaas.online/wp-content/uploads/2026/03/crossapp-dolibarr-customer-created-scaled.png |
| 9 | Odoo grid | Odoo Contacts grid view showing Mike Oliver synced from Dolibarr | https://polysaas.online/wp-content/uploads/2026/03/crossapp-odoo-contacts-grid-mike-oliver.jpg |
| 10 | Odoo detail | Odoo Contact detail page for Mike Oliver showing all synced fields | https://polysaas.online/wp-content/uploads/2026/03/crossapp-odoo-contact-mike-oliver-detail.jpg |
| 11 | Instructions list | Django admin Instructions list in olient tenant | https://polysaas.online/wp-content/uploads/2026/03/crossapp-instruction-list-olient.jpg |
| 12 | Instruction detail | Instruction detail for Dolibarr POST capture | https://polysaas.online/wp-content/uploads/2026/03/crossapp-instruction-detail-dolibarr.jpg |

**Body copy beside each image** on the site matches the step headings in the next section (PolySniffer launch, capture, login, Third-parties, New Customer, form fields table, submit, Dolibarr card, Odoo grid, Odoo detail, then **Instructions** / **Mapping Engine** sections).

---

## Step-by-step narrative (aligned with page)

1. **Launch PolySniffer for Dolibarr** — Django admin → PassThrough endpoints → **PolySniffer Analysis** on the Dolibarr row.  
2. **PolySniffer captures all traffic** — Dashboard shows each request (headers, cookies, body).  
3. **Login through proxy** — Dolibarr **19.0.2**; login request captured (CSRF pattern).  
4. **Navigate to Third-parties** — Main menu: Home, Members, Third-parties, Products, etc.  
5. **New Customer** — Sidebar: 0 Prospects / 0 Customers / 0 Vendors; open **New Customer**.  
6. **Fill New Third Party form** — Core fields: name, alias, prospect/customer, address, zip, city, phone, email, third-party type.  
7. **Submit** — **CREATE THIRD PARTY**; POST body ~43 fields (CSRF, action, form values).  
8. **Customer in Dolibarr** — e.g. code **CU2603-00001**, type Workforce, Prospect + Customer.  
9. **Odoo Contacts** — Same person appears after Dolibarr → Mapping → RabbitMQ → Mapping → XML-RPC.  
10. **Odoo contact detail** — Confirms mapped fields (name, address, zip, city, phone, mobile, email).  

### Form field table (as on page)

| Form field | Value entered | Normalized to |
|------------|---------------|---------------|
| Third-party name | Mike Oliver | `name` |
| Alias | Mike Oliver | `name_alias` |
| Prospect / Customer | Prospect / Customer | `is_customer = 1` |
| Address | 102 Woodlily Pl. | `street` |
| Zip Code | 77382 | `zip` |
| City | Spring | `city` |
| Phone | 2818535769 | `phone` |
| Email | mikeoliveraz@gmail.com | `email` |
| Third-party type | Workforce | `typent_id` |

### Dolibarr → Odoo field mapping table (as on page)

| Dolibarr field | Normalized | Odoo field | Value |
|----------------|------------|------------|--------|
| name | name | name | Mike Oliver |
| address | street | street | 102 Woodlily Pl. |
| zipcode | zip | zip | 77382 |
| town | city | city | Spring |
| phone | phone | phone | 2818535769 |
| fax | fax | mobile | 2818535769 |
| email | email | email | mikeoliveraz@gmail.com |
| customer_code | customer_code | ref | CU2603-00001 |

**Footer line on page:** **Sync Complete** — Zero code changes. Entirely driven by database-configured Mappings and Instructions.

---

## Instructions (tenant admin)

**Context:** **Oliver Enterprises** tenant (**olient**). Two Instructions drive this flow (plus any pre-existing rows — page shows three lines in the list screenshot).

| Request path | Method | Service | Purpose |
|--------------|--------|---------|---------|
| `/societe/card.php` | POST | `EndpointDataExtractorService` | Captures Dolibarr POST, extracts & publishes to RabbitMQ |
| `/mq/polysaas.crossapp.customer.created` | POST | `OdooCustomerSyncService` | MQ message → map to Odoo partner → XML-RPC |

**Dolibarr instruction:** `requestpath` contains `/societe/card.php`, `eventKey` `dolibarr.customer.created`, method POST, direction REQUEST; **Instruction Mappings** tab links extraction mappings.

> **Repo note:** `EndpointDataExtractorService` / `OdooCustomerSyncService` are **not** present under `dose/services/` in this repository as of last check; they may exist only on the deployment host or in unpushed branches.

---

## Mapping engine (as on page)

Database-driven — expressions with **pipe** operators.

### Mapping 1: Dolibarr POST → normalized event

**Direction:** SOURCE → NORMALIZED  

| Normalized field | Expression (pipe syntax) | Result |
|------------------|-------------------------|--------|
| `name` | `request.POST.name` → `strip` | Mike Oliver |
| `email` | `request.POST.email` → `strip` → `lower` → `email` | mikeoliveraz@gmail.com |
| `phone` | `request.POST.phone` → `strip` → `default:None` | 2818535769 |
| `street` | `request.POST.address` → `strip` | 102 Woodlily Pl. |
| `zip` | `request.POST.zipcode` → `strip` | 77382 |
| `city` | `request.POST.town` → `strip` | Spring |
| `is_customer` | `request.POST.client` → `int:1:0` | 1 |
| `customer_code` | `request.POST.customer_code` → `strip` | CU2603-00001 |

### Mapping 2: Normalized → Odoo `res.partner`

**Direction:** NORMALIZED → TARGET  

| Odoo field | Expression (pipe syntax) | Result |
|------------|---------------------------|--------|
| `name` | `payload.name` | Mike Oliver |
| `email` | `payload.email` | mikeoliveraz@gmail.com |
| `customer_rank` | `payload.is_customer` → `int:1:0` | 1 |
| `ref` | `payload.customer_code` → `default:None` | CU2603-00001 |
| `is_company` | literal `'True'` → `bool` | True |
| `street` | `payload.street` | 102 Woodlily Pl. |
| `city` | `payload.city` | Spring |

**Pipe operators (as listed on page):** `strip`, `lower`, `upper`, `email`, `int:1:0`, `default:value`, `truncate:120`, `prefix:DOL-`, `bool`, `if:path`, `coalesce:fallback.path`.

---

## Technology stack (as on page)

| Component | Role | Status |
|-----------|------|--------|
| PolySniffer | Passive traffic capture | Active |
| Mapping Engine | DB-driven field extraction & transforms | Active |
| RabbitMQ | Broker between extractor and sync | Active |
| Atomic services | `EndpointDataExtractorService` + `OdooCustomerSyncService` | Active |
| Instructions | Paths `/societe/card.php` and `/mq/...` | Active |
| Passthrough proxy | Dolibarr through PolySaaS | Handler Pending |
| Odoo XML-RPC | `res.partner` create/update | Active |

**Closing:** Cross-application sync is one example of what Dynamic Orchestration enables. Footer links on the page: Dynamic Orchestration, PolySniffer, Schedule a Demo.

---

## Maintenance

- After changing the **WordPress** page: refresh this file so tables, counts, and **screenshot URLs** stay accurate.  
- To re-list media from WP: `python documentation/website/_extract_cross_app_sync_wp.py` → writes `_cross_app_sync_extract.txt` (gitignored optional).  
