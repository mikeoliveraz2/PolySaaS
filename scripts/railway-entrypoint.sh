#!/bin/sh
set -e
cd /app

# Optional: run migrations on boot (multi-tenant redirect lives in manage.py)
if [ "${RUN_MIGRATIONS:-0}" = "1" ]; then
  python manage.py migrate --noinput
fi

python manage.py collectstatic --noinput

exec "$@"
