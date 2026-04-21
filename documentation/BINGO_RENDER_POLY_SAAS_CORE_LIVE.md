# BINGO: PolySaaS-Core live on Render (Django)

**Date:** April 19, 2026  
**Status:** **Production web service verified** — deploy succeeds; admin login template loads at primary URL.  
**Branch:** `main`  
**Primary URL:** `https://polysaas-core.onrender.com`

---

## Summary

**PolySaaS-Core** (Django / DOSE) is **running on Render** in workspace **PolySaaS-Main**, using the **existing** container path: **`Dockerfile.django`**, **`scripts/railway-entrypoint.sh`**, and **`mysite.settings_railway`**. No replacement entrypoint was required; naming is legacy (“Railway”) only.

This BINGO certifies the **Render cutover for the main Django web service** after resolving Dockerfile mis-selection, Postgres connectivity (workspace-internal host), credential precedence, and **`DATABASE_URL` parsing** (`django-environ` / `urllib` — malformed URLs when passwords contained unescaped `@` / `:` or typos in host).

---

## Certified (operator-verified on Render)

| Area | Notes |
|------|--------|
| **Build** | Service uses **`Dockerfile.django`** with Docker context **`.`** (repo root). **Not** repo-root stub **`Dockerfile`** (Alpine guard). |
| **Runtime** | **`DJANGO_SECRET_KEY`**, **`DJANGO_SETTINGS_MODULE=mysite.settings_railway`**, Postgres reachable from same workspace. |
| **Database** | Working pattern: **`DB_*`** discrete vars **or** a single correctly formed **`DATABASE_URL`** (encoded password, explicit **`:5432`** when helpful). **`DOSE_DB_PASSWORD`** overrides **`DB_PASSWORD`** when set — remove or align. |
| **Health** | Render health check path **`/health/`** (per `render.yaml` / ops). |
| **UI** | Custom admin login (**`admin/login.html`**) renders; “DOSE LOGIN PAGE” path confirmed in browser. |

---

## Follow-up (not blocking “live”, do next)

1. **`ALLOWED_HOSTS` / `CSRF_TRUSTED_ORIGINS`** — include **`https://polysaas-core.onrender.com`**; avoid long-term **`ALLOWED_HOSTS=*`** in production.  
2. **`DEBUG=False`** when debugging window is closed.  
3. **Celery** — add Render **Redis** (or broker) and set **`CELERY_BROKER_URL`**; worker service from same image per `render.yaml`.  
4. **Odoo** — **`deploy/odoo-render/Dockerfile`** + context **`deploy/odoo-render`**; **`entrypoint-render.sh`** for Render `PORT` vs Postgres port.  
5. **Secrets hygiene** — rotate any DB or Django secrets that appeared in chat, screenshots, or mis-pasted URLs.  
6. **Adminer** (optional) — same workspace as Postgres; lock down access.

---

## BINGO — certification statement

- [x] **PolySaaS-Core** Django web service is **live on Render** with successful build, DB connectivity, bootstrap, and Gunicorn serving the admin login page.  
- [ ] **Celery + broker**, **Odoo**, and **hardening checklist** above remain **follow-up** work.

**BINGO — PolySaaS-Core on Render is certified live for this milestone.**
