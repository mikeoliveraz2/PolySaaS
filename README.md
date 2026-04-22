# PolySaaS

PolySaaS is the product formerly code-named DOSE. In this repository, the live application is a Django project rooted at `manage.py` and `mysite/`, with tenant-aware admin, landing-page portal behavior, passthrough integrations, Celery, and Stripe wiring.

## Runtime

- Web app: Django / Gunicorn via `mysite.wsgi:application` (there is no FastAPI or alternate `src/` web app in this repo; use `Dockerfile.django` for containers)
- Main settings: `mysite.settings`
- Render/container settings: `mysite.settings_render`
- Health endpoints: `/health/` and `/health/ready/`

## Local Development

```bash
pip install -r requirements.txt
python manage.py runserver
```

The project expects PostgreSQL and, for async work, RabbitMQ. There are multiple local compose files in the repo for supporting services.

## Render deploy

This repository uses **Render** as the primary managed hosting path (see root `render.yaml`):

- Blueprint: `render.yaml`
- Image: `Dockerfile.django`
- Entry point: `scripts/render-entrypoint.sh`
- Settings: `mysite.settings_render`

Recommended web service environment:

```text
DJANGO_SETTINGS_MODULE=mysite.settings_render
DJANGO_SECRET_KEY=<secret>
DEBUG=False
DATABASE_URL=<render postgres url>
ALLOWED_HOSTS=<your onrender.com host>
CSRF_TRUSTED_ORIGINS=https://<your onrender.com host>
RUN_MIGRATIONS=0
GUNICORN_WORKERS=1
GUNICORN_THREADS=2
GUNICORN_TIMEOUT=30
```

Optional worker environment:

```text
CELERY_BROKER_URL=<render rabbitmq or amqp url>
```

See `documentation/deployment/render/RENDER-DEPLOYMENT-PLAN.md` for the fuller operator checklist.
