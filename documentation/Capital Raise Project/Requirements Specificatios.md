# Requirements – FINAL Locked Scope

Subscribe Form Checkboxes (all async provisioned)
☐ osTicket Helpdesk
☐ Odoo ERP
☐ SuiteCRM
☐ Nextcloud Files & Collab
☐ Dolibarr ERP/CRM
☐ Google Workspace (native)

Atomic Services Already Built
- osticket_tenant_provisioner.py
- odoo_tenant_provisioner.py
- suitecrm_tenant_provisioner.py
- nextcloud_tenant_provisioner.py
- dolibarr_tenant_provisioner.py

Non-Functional
- Schema-per-tenant isolation (no tenant_id columns)
- Single domain routing (app.polysaas.online)
- Stripe → instant provisioning (< 60 s)
- Public OpenAPI 3.1 with Swagger/ReDoc
- Celery + Redis/RabbitMQ for all background jobs