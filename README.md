# PolySaaS

PolySaaS is the product formerly code-named DOSE. In this repository, the live application is a Django project rooted at `manage.py` and `mysite/`, with tenant-aware admin, landing-page portal behavior, passthrough integrations, Celery, and Stripe wiring.

## Runtime

- Web app: Django / Gunicorn via `mysite.wsgi:application` (there is no FastAPI or alternate `src/` web app in this repo; use `Dockerfile.django` for containers)
- Main settings: `mysite.settings`
- Container/prod settings: `mysite.settings_hosted`
- Health endpoints: `/health/` and `/health/ready/`

## Local Development

```bash
pip install -r requirements.txt
docker compose --env-file .env -f docker-compose.local.yml up -d
python manage.py runserver
```

`docker-compose.local.yml` is the one local stack: Postgres, Redis, RabbitMQ, plus bundled-app containers (Mattermost, Nextcloud, Odoo, Dolibarr). See `documentation/LOCAL_STANDALONE_STACK.md` for first-run notes. Copy `.env.local.example` into `.env` (or merge the values in) before starting.

## Container/Hosted Deploy

This repository supports containerized deployment via `Dockerfile.django` and `mysite.settings_hosted`:

- Image: `Dockerfile.django`
- Entry point: `entrypoint.sh`
- Settings: `mysite.settings_hosted`

Recommended web service environment:

```text
DJANGO_SETTINGS_MODULE=mysite.settings_hosted
DJANGO_SECRET_KEY=<secret>
DEBUG=False
DATABASE_URL=<postgres url>
ALLOWED_HOSTS=<your host>
CSRF_TRUSTED_ORIGINS=https://<your host>
RUN_MIGRATIONS=0
GUNICORN_WORKERS=1
GUNICORN_THREADS=2
GUNICORN_TIMEOUT=30
```

Optional worker environment:

```text
CELERY_BROKER_URL=<rabbitmq/amqp url>
```

See deployment docs under `documentation/` for environment-specific operator checklists.
