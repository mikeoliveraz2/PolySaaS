# BINGO: Railway-first deploy, Django container, internal stack, docs

**Date:** March 23, 2026  
**Status:** Complete and tested (syntax / deps); **Railway project wiring** is operator follow-up on dashboard.  
**Branch:** `main` (commits include `a959456`, `8b455f4` and related doc commits)

---

## Summary

PolySaaS is **ready to deploy Django on Railway** using a **dedicated Dockerfile** (not the legacy FastAPI root `Dockerfile`), **`mysite.settings_railway`** (12-factor env), **Gunicorn + Whitenoise**, and **documented internal services** (Postgres, RabbitMQ, Elasticsearch, Grafana, OpenObserve) via **`docker-compose.railway-stack.yml`**. **Stripe** subscription path in `dose/views.py` no longer embeds a secret key.

**Backup:** Per project rules, daily source backup runs with **`.\go.ps1`** (after runserver exit) or your backup script; ensure `git push origin main` after this commit so both machines stay in sync.

---

## 1. Railway deployment plan & local stack

| Deliverable | Purpose |
|-------------|---------|
| `documentation/deployment/railway/RAILWAY-DEPLOYMENT-PLAN.md` | Service list, boot order, env vars, Stripe webhook path, Celery/MQ notes, GCP checklist cross-link |
| `docker-compose.railway-stack.yml` | Local parity: Postgres (host `5433`), RabbitMQ + management UI, Elasticsearch (single-node), Grafana, OpenObserve |
| `documentation/deployment/railway/.env.railway.example` | Variable names for compose + Railway UI |
| `documentation/website/.gitignore` | Ignore `_cross_app_sync_extract.txt` |
| `documentation/website/cross-app-sync-poc.md` + `_extract_cross_app_sync_wp.py` | POC narrative synced to live WP page (separate certification) |

---

## 2. Django container (`8b455f4`)

| Deliverable | Purpose |
|-------------|---------|
| **`Dockerfile.django`** | Builds **Django DOSE** app: `mysite`, `dose`, `parameters`, `alerts`, `static`, `templates`, `manage.py`, `test_decompression_view.py` |
| **`mysite/settings_railway.py`** | `DATABASE_URL` or discrete DB; `CELERY_BROKER_URL`; `ALLOWED_HOSTS` / `CSRF_TRUSTED_ORIGINS`; DB-backed sessions; Whitenoise; stdout logging; proxy TLS headers |
| **`scripts/railway-entrypoint.sh`** | `collectstatic`; optional `RUN_MIGRATIONS=1`; then `exec` Gunicorn |
| **`requirements.txt`** | Added `gunicorn`, `whitenoise`, `pika` |
| **`dose/views.py`** | Stripe: **`STRIPE_SECRET_KEY` only**; **503** if unset (removed hardcoded test key) |

**Verified:** `python -m py_compile` on `settings_railway.py` and `views.py`; `pip install` of new deps in venv succeeded.

**Operator checklist on Railway:** Set **`DJANGO_SECRET_KEY`** before any boot (base `settings.py` requires it). Dockerfile sets **`DJANGO_SETTINGS_MODULE=mysite.settings_railway`**. Point service **Dockerfile path** to **`Dockerfile.django`**.

---

## 3. Repo hygiene notes

- Root **`Dockerfile`** / **`docker-compose.yml`** remain the **FastAPI** stub — **do not** use them for DOSE Django; use **`Dockerfile.django`**.
- Unstaged local edits may still exist (`dose/oauth.py`, `oauth2_registration.py`, `go.ps1`) from optional **`oauth2_provider`**-off laptop work — **not** part of this bingo unless committed separately.

---

## BINGO — certification

- [x] Railway plan + compose stack documented and pushed  
- [x] Django `Dockerfile.django` + `settings_railway` + entrypoint + Gunicorn/Whitenoise/pika  
- [x] Stripe secret removed from `dose/views.py`  
- [x] Syntax check passed; dependencies install  
- [x] `git pull` → `git commit` → `git push origin main` for this bingo doc  
- [ ] **You:** Create Railway services, set env vars, first deploy smoke test  
- [ ] **You:** Daily backup / `.\go` per machine when done  

**BINGO — this documentation commit certifies the listed deliverables as implemented in repo; production cutover is confirmed when Railway smoke test passes.**
