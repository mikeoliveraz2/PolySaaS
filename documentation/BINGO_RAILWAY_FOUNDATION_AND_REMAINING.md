# BINGO: Railway foundation certified — remaining work (priority order)

**Date:** March 23, 2026  
**Status:** Foundation in repo and documented; **production cutover** and items below are **operator / follow-up** work.  
**Branch:** `main`

---

## Summary

The **Railway-first** path is **implemented in the codebase**: Django **`Dockerfile.django`**, **`mysite.settings_railway`**, health endpoints, **`railway.toml`**, **Gunicorn + `PORT` + Whitenoise**, **Celery app** (`mysite/celery.py`) with **worker / beat scripts**, **`django-celery-beat` + `django-celery-results`**, **Stripe** hardcoded key removed from `dose/views.py`, **DoseRequestController** bypass for `/health/`, **MonitorLogger** rebrand in stack docs, **`STRIPE-RAILWAY.md`**, **`docker-compose.railway-stack.yml`**, and **deployment plan** updates.

This BINGO **certifies that foundation**. The **ordered checklist below** is what remains to **tackle in priority order** (Michael + agents + Railway dashboard).

---

## Certified in repository (reference commits)

| Area | Deliverables |
|------|----------------|
| Container | `Dockerfile.django`, `scripts/railway-entrypoint.sh`, `PORT`, health-aware `HEALTHCHECK` |
| Settings | `mysite/settings_railway.py` — DB URL / discrete DB, broker, sessions, Whitenoise, TLS proxy, logging |
| Health | `GET /health/`, `GET /health/ready/` in `mysite/urls.py` |
| Railway config | `railway.toml` — Dockerfile path, healthcheck path |
| Celery | `mysite/celery.py`, `/celery-worker.sh`, `/celery-beat.sh` in image |
| Celery Django | `django-celery-beat`, `django-celery-results` in `INSTALLED_APPS` + `requirements.txt` |
| Stripe | `STRIPE-RAILWAY.md`; views use `STRIPE_SECRET_KEY` only |
| Stack docs | `RAILWAY-DEPLOYMENT-PLAN.md`, `.env.railway.example`, compose stack, MonitorLogger naming |
| Related | `GCP-Deployment-Readiness-and-Checklist.md` Railway pointer; prior `BINGO_RAILWAY_DJANGO_DEPLOY_AND_STACK.md` |

---

## Remaining work — **do in this order**

### P1 — Railway web + data + broker (blocking)

1. **Railway project:** Create **web** service from repo, **`Dockerfile.django`**.
2. **PostgreSQL** service (or container in project); set **`DATABASE_URL`** (or `DB_*` + `DOSE_DB_PASSWORD`).
3. **RabbitMQ** service; set **`CELERY_BROKER_URL`**; align **MQConfig** in admin if used for `pika`.
4. **Secrets / env:** `DJANGO_SECRET_KEY`, `DJANGO_SETTINGS_MODULE=mysite.settings_railway`, `ALLOWED_HOSTS`, `CSRF_TRUSTED_ORIGINS`, Stripe keys.
5. **First migrate:** Enable **`RUN_MIGRATIONS=1`** once on web (or one-off deploy command), then disable if desired. Ensures **django_celery_*** tables among others.
6. **Smoke test:** `/health/`, `/health/ready/`, `/admin/`, one critical user flow.

### P2 — Stripe production

7. **Stripe Dashboard:** Webhook → `https://<host>/dose/webhook/stripe/`; set **`STRIPE_WEBHOOK_SECRET`** on Railway.
8. **Optional:** Enrich **Swagger** text for subscribe / payment-related APIs.

### P3 — Celery on Railway

9. **Worker** service — same image, start **`/celery-worker.sh`** or `celery -A mysite worker …`.
10. **Beat** service — same image, start **`/celery-beat.sh`** or `celery -A mysite beat …`.

### P4 — Rest of internal stack (when needed)

11. **Elasticsearch** service + later **Django client / indexes** when a feature needs search.
12. **Grafana** + **MonitorLogger** services; **OTLP / log shipping** from Django (not implemented yet).

### P5 — Product / parity / GCP

13. **Cross-app POC code:** Commit or add **`EndpointDataExtractorService`** / **`OdooCustomerSyncService`** if still only on desktop.
14. **Dolibarr passthrough** “handler pending” — implement or update marketing copy when done.
15. **GCP path** — after OAuth2/SSO readiness gate (`GCP-Deployment-Readiness-and-Checklist.md`).

### Hygiene

16. **Laptop / optional oauth:** Commit or drop local **`dose/oauth.py`**, **`oauth2_registration.py`**, **`go.ps1`** changes when ready.
17. **Legacy FastAPI** root `Dockerfile` / `docker-compose.yml` — document or archive so deploys don’t use them by mistake.

---

## BINGO — certification statement

- [x] Railway **foundation** (Django container, settings, health, Celery packages, scripts, docs, Stripe doc, MonitorLogger rebrand) is **in `main`** and described above.  
- [ ] **P1–P3** are **confirmed** when Michael completes Railway smoke + webhook + worker/beat.  
- [ ] **P4–P5** are **separate** phases.

**BINGO — this document certifies the repository and documentation state as of the commit that adds this file; remaining rows are intentional follow-up, not gaps in the foundation commit.**

---

*After this commit: pull on other machines, then execute P1 on Railway in order.*
