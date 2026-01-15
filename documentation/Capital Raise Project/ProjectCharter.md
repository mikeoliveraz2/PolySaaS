# PolySaaS – Project Charter (Dec 2025)

Project Name: PolySaaS
Launch Date: 31 December 2025 (hard)

Purpose
Instant-provisioned, multi-tenant SaaS operating system that turns five open-source giants into one subscription, one login, one bill.

Five Open-Source Apps We Host & Provision
1. osTicket – Helpdesk
2. Odoo – Full ERP
3. SuiteCRM – CRM
4. Nextcloud – Files & Collaboration
5. Dolibarr – Lightweight ERP/CRM

Sixth Service (Native Pass-Through)
Google Workspace (Gmail, Calendar, Drive) – OAuth only, no Docker

MVP Success Criteria
- 60-second tenant provisioning with all selected apps
- 12 signed LOIs converted to paying customers on launch day
- $1.35M ARR run-rate live on 1 Jan 2026
- Zero tenant data leakage (schema-per-tenant + key prefixing)
- Public OpenAPI + webhooks day-1

Tech Stack
GCP • Docker • Celery • FastAPI • Next.js • PostgreSQL schemas • Redis • Atomic Services framework
