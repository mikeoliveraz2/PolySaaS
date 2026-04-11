#!/bin/sh
set -e
cd /app

require_env() {
  var_name="$1"
  eval var_value="\${$var_name:-}"
  if [ -z "$var_value" ]; then
    echo "[railway-entrypoint] Missing required environment variable: $var_name" >&2
    exit 1
  fi
}

require_env DJANGO_SECRET_KEY

# Optional: run migrations on boot (multi-tenant redirect lives in manage.py)
if [ "${RUN_MIGRATIONS:-0}" = "1" ]; then
  python manage.py migrate --noinput
fi

python manage.py collectstatic --noinput

exec "$@"
