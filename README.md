# PolySaaS

PolySaaS is the product formerly code-named DOSE. In this repository, the live application is a Django project rooted at `manage.py` and `mysite/`, with tenant-aware admin, landing-page portal behavior, passthrough integrations, Celery, and Stripe wiring.

## Runtime

- Web app: Django / Gunicorn via `mysite.wsgi:application` (there is no FastAPI or alternate `src/` web app in this repo; use `Dockerfile.django` for containers)
- Main settings: `mysite.settings`
- Railway/container settings: `mysite.settings_railway`
- Health endpoints: `/health/` and `/health/ready/`

## Local Development

```bash
pip install -r requirements.txt
python manage.py runserver
```

The project expects PostgreSQL and, for async work, RabbitMQ. There are multiple local compose files in the repo for supporting services.

## Railway Deploy

This repository already contains a Railway-oriented deployment path:

- Config: `railway.toml`
- Image: `Dockerfile.django`
- Entry point: `scripts/railway-entrypoint.sh`
- Settings: `mysite.settings_railway`

Recommended web service environment:

```text
DJANGO_SETTINGS_MODULE=mysite.settings_railway
DJANGO_SECRET_KEY=<secret>
DEBUG=False
DATABASE_URL=<railway postgres url>
ALLOWED_HOSTS=<your railway host>
CSRF_TRUSTED_ORIGINS=https://<your railway host>
RUN_MIGRATIONS=0
GUNICORN_WORKERS=1
GUNICORN_THREADS=2
GUNICORN_TIMEOUT=180
```

Optional worker environment:

```text
CELERY_BROKER_URL=<railway rabbitmq url>
```

See `documentation/deployment/railway/RAILWAY-DEPLOYMENT-PLAN.md` for the fuller operator checklist.
