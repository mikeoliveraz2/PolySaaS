# Architecture – FINAL (GCP Native)

┌─────────────────────┐
│   Cloud Load Balancer │
└───────┬─────────────┬─┘
        │             │
┌───────▼─────┐ ┌─────▼───────┐
│ Cloud Run    │ │ Cloud Run    │
│ FastAPI      │ │ Next.js      │
└───────┬─────┘ └─────┬───────┘
        │             │
   ┌────▼─────────────▼─────┐
   │ Cloud SQL PostgreSQL    │ → one schema per tenant
   └────┬────────────────────┘
        │
   ┌────▼────────────────────┐
   │ Memorystore Redis        │ → Celery broker + cache
   └────┬────────────────────┘
        │
   ┌────▼────────────────────┐
   │ Five Dockerized Apps     │ → Cloud Run / GKE Autopilot
   │ osTicket • Odoo • SuiteCRM • Nextcloud • Dolibarr │
   └─────────────────────────┘