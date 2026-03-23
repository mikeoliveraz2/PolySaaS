#!/bin/sh
# Same image as web (Dockerfile.django); Railway: set Start Command to this script
# or: celery -A mysite worker -l INFO --concurrency 2
set -e
cd /app

if [ "${RUN_MIGRATIONS:-0}" = "1" ]; then
  python manage.py migrate --noinput
fi

exec celery -A mysite worker \
  -l "${CELERY_LOG_LEVEL:-INFO}" \
  --concurrency "${CELERY_CONCURRENCY:-2}"
