# PolySaaS — Railway-first deployment (internal stack)

**Goal:** Run **PostgreSQL**, **RabbitMQ**, **Elasticsearch**, **Grafana**, **OpenObserve**, and the **Django (DOSE)** app **inside one Railway project** (all containerized / self-defined), with **Stripe** wired for `subscribe_view`, webhooks, and future OpenAPI-exposed payment flows.

**Status:** Planning + local parity compose. **Not yet:** production `settings_railway.py` or a committed Django `Dockerfile` (see gaps below).

---

## 1. Repo reality check (important)

| Item | What the repo has today |
|------|-------------------------|
| **App runtime** | **Django** — `manage.py`, `mysite/wsgi.py`, `DJANGO_SETTINGS_MODULE=mysite.settings` |
| **Root `Dockerfile`** | Builds **`uvicorn polysaas.main:app`** from `src/` — **FastAPI stub**, **not** the Django app |
| **Root `docker-compose.yml`** | Wires that FastAPI image + Postgres + Redis — **not** DOSE Django |
| **Database** | `mysite/settings.py` → PostgreSQL `dosedbsaas` on `localhost:5433` + `DOSE_DB_PASSWORD` |
| **Celery / broker** | `CELERY_BROKER_URL = amqp://guest:guest@localhost` — expects **RabbitMQ** on localhost |
| **MQ in app** | `dose/mq/adapters/rabbitmq_adapter.py` — **pika**, host/port/user/pass from **MQConfig** (DB) |
| **Stripe** | `STRIPE_*` in `settings.py`; `dose/subscription_views.py`, `dose/views/stripe_webhook.py` → `/dose/webhook/stripe/` |
| **Elasticsearch / Grafana / OpenObserve** | **No app integration** in code yet — infra-only for now |

**Action before Railway:** Add a **Django-oriented Dockerfile** (e.g. `Dockerfile.django` or replace strategy) and point Railway’s **web service** build at it. Gunicorn (or waitress on Windows-only dev) + `mysite.wsgi:application` is the usual pattern.

---

## 2. Target services (all “internal” to the project)

Deploy each as its **own Railway service** (or one compose-based deployment if you use Railway’s Docker Compose path). Use **private networking** and **reference variables** so secrets never hit the repo.

| # | Service | Image / build | Default ports | Role |
|---|---------|---------------|---------------|------|
| 1 | **PostgreSQL** | `postgres:16-alpine` (or 15) | 5432 | Django + Celery results (`django-db` backend) |
| 2 | **RabbitMQ** | `rabbitmq:3-management-alpine` | 5672 (AMQP), 15672 (mgmt UI) | Celery broker + cross-app MQ (`pika`) |
| 3 | **Elasticsearch** | `docker.elastic.co/elasticsearch/elasticsearch:8.11.0` | 9200, 9300 | Search / analytics (single-node for phase 1) |
| 4 | **Grafana** | `grafana/grafana:10.4.3` | 3000 | Dashboards (add Prometheus/Loki/ES datasources later) |
| 5 | **OpenObserve** | `public.ecr.aws/zinclabs/openobserve:latest` (or `openobserve/openobserve:latest`) | 5080 | Logs / traces / metrics ingestion |
| 6 | **Django (PolySaaS)** | **Your Dockerfile** | 8000 (internal) → Railway HTTPS | Web + API + admin |

**Memory:** ES + OpenObserve + Grafana together are heavy. On Railway, set **explicit plan limits**; consider **phase 1** = Postgres + RabbitMQ + Django + **one** of {OpenObserve, Grafana}, then add Elasticsearch when search is wired.

---

## 3. Boot / dependency order

1. **PostgreSQL** (health: `pg_isready`)  
2. **RabbitMQ** (health: `rabbitmq-diagnostics ping`)  
3. **Elasticsearch** (health: `/_cluster/health` — optional until app uses it)  
4. **OpenObserve** / **Grafana** (parallel; no hard dependency for Django v1)  
5. **Django** — `migrate`, `collectstatic` (if not using object storage), then **gunicorn**

Celery worker / beat: **separate Railway services** (same image as web, different `command`), `depends_on` RabbitMQ + Postgres.

---

## 4. Environment variables (Django web / worker)

Use Railway **variables**; mirror names in `.env.railway.example` (this folder).

**Core**

- `DJANGO_SETTINGS_MODULE` — e.g. `mysite.settings` until `settings_railway.py` exists  
- `DJANGO_SECRET_KEY`  
- `DEBUG=False`  
- `ALLOWED_HOSTS` — your Railway domain + custom domain  

**PostgreSQL**

- Prefer a single `DATABASE_URL` and parse in settings, **or** mirror `settings_production.py` style:  
  `DB_NAME`, `DB_USER`, `DOSE_DB_PASSWORD`, `DB_HOST`, `DB_PORT`

**RabbitMQ / Celery**

- `CELERY_BROKER_URL=amqp://USER:PASS@rabbitmq.railway.internal:5672//`  
- Align **MQConfig** rows in Django admin with the same host/user/pass for `RabbitMQAdapter`.

**Stripe**

- `STRIPE_SECRET_KEY`  
- `STRIPE_PUBLISHABLE_KEY`  
- `STRIPE_WEBHOOK_SECRET`  
- `STRIPE_PRICE_ID` / populate `STRIPE_PRICE_IDS` for tiers  
- **Webhook URL (production):** `https://<your-domain>/dose/webhook/stripe/`  
- Register endpoint in **Stripe Dashboard**; use signing secret above.

**Security cleanup (recommended)**

- `dose/views.py` contains a **fallback Stripe test key** in code — remove and use **only** `settings.STRIPE_SECRET_KEY` before production.

**HTTPS / CSRF**

- Set `CSRF_TRUSTED_ORIGINS=https://yourapp.up.railway.app,https://polysaas.online` (example).

**Elasticsearch / observability (when integrated)**

- `ELASTICSEARCH_URL=http://elasticsearch.railway.internal:9200`  
- OpenObserve / OTEL endpoints — add when Django logging or APM is wired.

---

## 5. Stripe + OpenAPI / Swagger

Today: **drf-yasg / swagger** at `/swagger/` (staff-gated per `urls.py` patterns).

**Plan**

1. Document **subscription** and **webhook** flows in OpenAPI descriptions (tags, summaries, `STRIPE_PUBLISHABLE_KEY` usage on client).  
2. For “charges in Dynamic Orchestration” — define **atomic services** or **REST endpoints** that call Stripe with **server-side** secret only; never expose `STRIPE_SECRET_KEY` to browsers.  
3. WordPress: **separate** Stripe keys or same Stripe account with **metadata** / **Connect** later — document in integration guide.

---

## 6. Local parity

From repo root:

```bash
docker compose -f docker-compose.railway-stack.yml up -d
```

Brings up Postgres, RabbitMQ, Elasticsearch, Grafana, OpenObserve for integration testing. **Does not** start Django (run `manage.py` on host or add an app service later).

---

## 7. Next implementation tasks (suggested order)

1. ~~**Django Dockerfile**~~ — **`Dockerfile.django`** + **`scripts/railway-entrypoint.sh`** (`collectstatic` on boot; set `RUN_MIGRATIONS=1` to migrate). **`gunicorn`** in `requirements.txt`.  
2. ~~**`mysite/settings_railway.py`**~~ — env-driven `DATABASE_URL` / discrete DB vars, `CELERY_BROKER_URL`, `ALLOWED_HOSTS`, **Whitenoise** static, DB sessions, stdout logging, proxy TLS headers. Set **`DJANGO_SETTINGS_MODULE=mysite.settings_railway`** (see `Dockerfile.django`).  
3. **Railway project** — create services, paste envs, connect private networking. **Build:** `docker build -f Dockerfile.django -t polysaas .`  
   - **`railway.toml`** — `dockerfilePath = Dockerfile.django`, `healthcheckPath = /health/`.  
   - **`PORT`** — Gunicorn binds `0.0.0.0:${PORT:-8000}` (Railway injects `PORT`).  
   - **Health:** `GET /health/` (liveness), `GET /health/ready/` (DB check, 503 if DB down).  
4. **Celery worker** — second Railway service, **same image**, start: `celery -A mysite worker -l INFO --concurrency 2` or **`/celery-worker.sh`**. Same env as web. **`mysite/celery.py`** defines the app; do not import Celery from `mysite/__init__.py` (avoids circular imports).  
5. **Celery beat** — third service (optional), **`/celery-beat.sh`** or `celery -A mysite beat -l INFO`. Requires **`django_celery_beat`** + **`django_celery_results`** in `INSTALLED_APPS` and **`python manage.py migrate`** for their tables (`CELERY_RESULT_BACKEND` uses `django-db`).  
6. **Stripe on Railway** — see **`STRIPE-RAILWAY.md`** (webhook URL, env vars, Swagger note).  
7. **Elasticsearch** client + indexes (when a feature needs search).  
8. **Grafana + OpenObserve** — scrape / OTLP from Django (optional phase 2).

---

## 8. References

- [Railway: Deployments](https://docs.railway.app/guides/deployments)  
- [Railway: Private networking](https://docs.railway.app/reference/private-networking)  
- [Stripe webhooks](https://stripe.com/docs/webhooks)  

*Document version: initial Railway plan aligned with repo scan.*
