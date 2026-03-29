#!/bin/sh
# Celery Beat — same image as web (Dockerfile.django). Requires django_celery_beat in INSTALLED_APPS
# and DB migrations applied. Railway: third service, same env as worker.
set -e
cd /app

if [ "${RUN_MIGRATIONS:-0}" = "1" ]; then
  python manage.py migrate --noinput
fi

exec celery -A mysite beat -l "${CELERY_LOG_LEVEL:-INFO}"
