# BINGO: Render-first deploy, Django container, internal stack, docs

**Date:** March 23, 2026  
**Status:** Complete and tested (syntax / deps); **Render project wiring** is operator follow-up on dashboard.  
**Branch:** `main` (commits include `a959456`, `8b455f4` and related doc commits)

---

## Summary

PolySaaS is **ready to deploy Django on Render** using a **dedicated Dockerfile** (not the legacy FastAPI root `Dockerfile`), **`mysite.settings_render`** (12-factor env), **Gunicorn + Whitenoise**, and **documented internal services** (Postgres, RabbitMQ, Elasticsearch, Grafana, **MonitorLogger**) via **`docker-compose.render-stack.yml`**. **Stripe** subscription path in `dose/views.py` no longer embeds a secret key.

**Backup:** Per project rules, daily source backup runs with **`.\go.ps1`** (after runserver exit) or your backup script; ensure `git push origin main` after this commit so both machines stay in sync.

---

## 1. Render deployment plan & local stack

| Deliverable | Purpose |
|-------------|---------|
| `documentation/deployment/render/RENDER-DEPLOYMENT-PLAN.md` | Service list, boot order, env vars, Stripe webhook path, Celery/MQ notes, GCP checklist cross-link |
| `docker-compose.render-stack.yml` | Local parity: Postgres (host `5433`), RabbitMQ + management UI, Elasticsearch (single-node), Grafana, **MonitorLogger** (compose service `monitorlogger`) |
| `documentation/deployment/render/.env.render.example` | Variable names for compose + Render UI |
| `documentation/website/.gitignore` | Ignore `_cross_app_sync_extract.txt` |
| `documentation/website/cross-app-sync-poc.md` + `_extract_cross_app_sync_wp.py` | POC narrative synced to live WP page (separate certification) |

---

## 2. Django container (`8b455f4`)

| Deliverable | Purpose |
|-------------|---------|
| **`Dockerfile.django`** | Builds **Django DOSE** app: `mysite`, `dose`, `parameters`, `alerts`, `static`, `templates`, `manage.py`, `test_decompression_view.py` |
| **`mysite/settings_render.py`** | `DATABASE_URL` or discrete DB; `CELERY_BROKER_URL`; `ALLOWED_HOSTS` / `CSRF_TRUSTED_ORIGINS`; DB-backed sessions; Whitenoise; stdout logging; proxy TLS headers |
| **`scripts/render-entrypoint.sh`** | `collectstatic`; optional `RUN_MIGRATIONS=1`; then `exec` Gunicorn |
| **`requirements.txt`** | Added `gunicorn`, `whitenoise`, `pika` |
| **`dose/views.py`** | Stripe: **`STRIPE_SECRET_KEY` only**; **503** if unset (removed hardcoded test key) |

**Verified:** `python -m py_compile` on `settings_render.py` and `views.py`; `pip install` of new deps in venv succeeded.

**Operator checklist on Render:** Set **`DJANGO_SECRET_KEY`** before any boot (base `settings.py` requires it). Dockerfile sets **`DJANGO_SETTINGS_MODULE=mysite.settings_render`**. Point service **Dockerfile path** to **`Dockerfile.django`**.

---

## 3. Repo hygiene notes

- Root **`Dockerfile`** refuses to build (points to **`Dockerfile.django`**); root **`docker-compose.yml`** is Postgres/Redis only — use **`Dockerfile.django`** for the Django image.
- Unstaged local edits may still exist (`dose/oauth.py`, `oauth2_registration.py`, `go.ps1`) from optional **`oauth2_provider`**-off laptop work — **not** part of this bingo unless committed separately.

---

## BINGO — certification

- [x] Render plan + compose stack documented and pushed  
- [x] Django `Dockerfile.django` + `settings_render` + entrypoint + Gunicorn/Whitenoise/pika  
- [x] Stripe secret removed from `dose/views.py`  
- [x] Syntax check passed; dependencies install  
- [x] `git pull` → `git commit` → `git push origin main` for this bingo doc  
- [ ] **You:** Create Render services, set env vars, first deploy smoke test  
- [ ] **You:** Daily backup / `.\go` per machine when done  

**BINGO — this documentation commit certifies the listed deliverables as implemented in repo; production cutover is confirmed when Render smoke test passes.**

---

## Update: April 12, 2026 (production incident closure)

### What was fixed

- Added missing `ml_studio` migrations to resolve deploy-time `InvalidBasesError` for proxy models.
- Confirmed and fixed root 500 caused by missing DB schema object (`dose_instruction`) by running migrations in Render.
- Rebound custom domain and validated DNS path for `production.polysaas.online`.
- Added Render startup auth bootstrap to recover admin and OAuth config without shell/job access:
	- New command: `dose/management/commands/bootstrap_auth.py`
	- Entrypoint integration: `scripts/render-entrypoint.sh`
	- Startup now enforces `admin` user as `is_staff=True` and `is_superuser=True` when present.

### Commit trail (latest incident work)

- `a984ca9` Add initial ml_studio proxy migrations
- `9dac262` Add Render auth bootstrap support
- `62e15a0` Always enforce admin superuser on Render boot

### Current verified state

- Default domain health endpoint: OK
- Default domain app login route: OK
- Custom domain `production.polysaas.online`: routing and app load OK
- Admin account access: restored and elevated through startup bootstrap

### Remaining operator actions

- Keep Google OAuth values set if Google login is required:
	- `BOOTSTRAP_GOOGLE_CLIENT_ID`
	- `BOOTSTRAP_GOOGLE_CLIENT_SECRET`
- Remove `BOOTSTRAP_ADMIN_PASSWORD` after validation and redeploy once, so password is not reapplied at each boot.
