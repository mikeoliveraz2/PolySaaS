# Cross-Application Sync POC (Dolibarr → Odoo)

**Public page (screenshots + styled layout):** [polysaas.online/cross-app-sync/](https://polysaas.online/cross-app-sync/)  
**Related:** [Dynamic Orchestration](https://polysaas.online/dynamic-orchestration/) · [PolySniffer](https://polysaas.online/polysniffer/)

**Repo sync:** This file is the **textual** mirror of the public page for version control and Cursor/desktop-cc. When you change the WordPress page or replace screenshot media, update this markdown (or commit a note in `documentation/collaboration/notes-from-desktop.md`) and **push to `main`**.

**Last checked against WordPress REST API:** `modified_gmt` **2026-03-22T05:13:30** (page id 2700, slug `cross-app-sync`). If only media files were replaced without re-saving the page, that timestamp may not move—re-save the page or bump this paragraph manually.

---

## Summary

Live demonstration: create a **new customer in Dolibarr** and sync to **Odoo CRM** as a contact/partner using **PolySniffer** (capture), **Mapping Engine** (transform), **RabbitMQ** (broker), and **Dynamic Orchestration** (instructions + atomic services)—**no code deploy** for mapping rules.

**Demonstrated:** March 22, 2026.

---

## End-to-end data flow

1. User creates customer in Dolibarr via Passthrough Proxy  
2. **Instruction A** matches `POST` … `/societe/card.php`  
3. Mapping Engine extracts & normalizes **21** fields from POST body  
4. Normalized event published to RabbitMQ: `polysaas.crossapp.customer.created`  
5. MQ Monitor consumes message, triggers **Instruction B**  
6. Mapping Engine maps normalized payload → **14** Odoo partner fields  
7. Odoo XML-RPC: `res.partner.create()` → contact appears in Odoo  

---

## Step-by-step (see site for images)

| Step | What |
|------|------|
| 1 | Django admin → PassThrough → **PolySniffer Analysis** on Dolibarr row |
| 2 | PolySniffer dashboard: all GET/POST captured (headers, cookies, body) |
| 3 | Dolibarr **19.0.2** through proxy; login captured (CSRF pattern) |
| 4 | Navigate **Third-parties** |
| 5 | **New Customer** (demo: zero prior prospects/customers/vendors) |
| 6 | Form: name, alias, prospect/customer, address, zip, city, phone, email, third-party type, etc. |
| 7 | **CREATE THIRD PARTY** → POST triggers sync chain (~43 form fields in body) |
| 8 | Dolibarr card: e.g. customer code **CU2603-00001** |
| 9 | Odoo **Contacts**: same person appears (synced) |
| 10 | Open contact: fields match mapped values |

### Sample form → normalized (excerpt)

| Form field | Value (demo) | Normalized |
|------------|----------------|------------|
| Third-party name | Mike Oliver | `name` |
| Email | mikeoliveraz@gmail.com | `email` |
| Address / Zip / City | 102 Woodlily Pl. / 77382 / Spring | `street` / `zip` / `city` |
| Customer code | CU2603-00001 | `customer_code` |

### Dolibarr → Odoo field mapping (excerpt)

| Dolibarr | Normalized | Odoo | Value |
|----------|------------|------|--------|
| name | name | name | Mike Oliver |
| address | street | street | 102 Woodlily Pl. |
| zipcode | zip | zip | 77382 |
| town | city | city | Spring |
| phone | phone | phone | 2818535769 |
| email | email | email | mikeoliveraz@gmail.com |
| customer_code | customer_code | ref | CU2603-00001 |

---

## Instructions (tenant admin — e.g. Oliver Enterprises / `olient`)

| Request path | Method | Atomic service | Purpose |
|--------------|--------|----------------|---------|
| `/societe/card.php` | POST | `EndpointDataExtractorService` | Capture POST, extract, publish to RabbitMQ |
| `/mq/polysaas.crossapp.customer.created` | POST | `OdooCustomerSyncService` | Consume MQ, map to Odoo, XML-RPC sync |

**Instruction detail (Dolibarr):** `eventKey` e.g. `dolibarr.customer.created`, direction REQUEST, Mappings tab → extraction mapping.

> **Note for developers:** Service class names above are **not** currently present under `dose/services/` in this repo; they may live only on the deployment machine or in unpushed work. See `documentation/collaboration/notes-from-laptop.md` for handoff.

---

## Mapping engine (concept)

Database-driven expressions with **pipes**, e.g. `|strip`, `|lower`, `|email`, `|int:1:0`, `|default:…`, `|truncate`, `|prefix`, `|bool`, `|if:path`, `|coalesce:…`.

**Mapping 1 — SOURCE → NORMALIZED (examples):**

- `name` ← `request.POST.name` then pipe `strip` → Mike Oliver  
- `email` ← `request.POST.email` → pipes `strip`, `lower`, `email` → mikeoliveraz@gmail.com  
- `street` ← `request.POST.address` → pipe `strip` → 102 Woodlily Pl.  

**Mapping 2 — NORMALIZED → Odoo `res.partner` (examples):**

- `name` ← `payload.name`  
- `customer_rank` ← `payload.is_customer` with conditional int cast  
- `ref` ← `payload.customer_code` with default  

---

## Technology stack (status as on public page)

| Component | Role | Status |
|-----------|------|--------|
| PolySniffer | Passive capture, discover paths/fields | Active |
| Mapping Engine | DB-driven transforms | Active |
| RabbitMQ | Broker | Active |
| Atomic services | Extractor + Odoo sync | Active (deploy) |
| Instructions | Path routing | Active |
| Passthrough proxy | Dolibarr through PolySaaS | Handler pending (per WP) |
| Odoo XML-RPC | `res.partner` | Active |

---

## Maintenance checklist

- [ ] After new screenshots: update media on WP, verify [cross-app-sync](https://polysaas.online/cross-app-sync/)  
- [ ] Bump **Last checked** at top of this file (or note in collaboration notes)  
- [ ] If narrative changes: edit this file + `git pull` / `commit` / `push` on both machines  
