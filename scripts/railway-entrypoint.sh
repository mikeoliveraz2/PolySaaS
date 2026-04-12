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

echo "[railway-entrypoint] Starting entrypoint script at $(date)" >&2

# Optional: run migrations on boot (multi-tenant redirect lives in manage.py)
if [ "${RUN_MIGRATIONS:-0}" = "1" ]; then
  echo "[railway-entrypoint] Running migrations..." >&2
  python manage.py migrate --noinput
fi

if [ -n "${BOOTSTRAP_ADMIN_PASSWORD:-}" ] || [ -n "${BOOTSTRAP_GOOGLE_CLIENT_ID:-}" ]; then
  echo "[railway-entrypoint] Running auth bootstrap..." >&2
  python manage.py bootstrap_auth
fi

echo "[railway-entrypoint] Running collectstatic..." >&2
python manage.py collectstatic --noinput

echo "[railway-entrypoint] Starting gunicorn at $(date)" >&2
exec "$@"
