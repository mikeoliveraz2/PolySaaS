#!/bin/sh
# GCP Cloud Run entrypoint — same boot sequence as Render, GCP settings module.
set -e
cd /app

require_env() {
  var_name="$1"
  eval var_value="\${$var_name:-}"
  if [ -z "$var_value" ]; then
    echo "[gcp-entrypoint] Missing required environment variable: $var_name" >&2
    exit 1
  fi
}

require_env DJANGO_SECRET_KEY

echo "[gcp-entrypoint] Starting at $(date -u)" >&2

if [ "${RUN_MIGRATIONS:-0}" = "1" ]; then
  echo "[gcp-entrypoint] Running migrate_all_schemas..." >&2
  python manage.py migrate_all_schemas --noinput
fi

echo "[gcp-entrypoint] bootstrap_auth..." >&2
python manage.py bootstrap_auth

if [ "${USE_GCS_STATIC:-0}" != "1" ] && [ "${USE_GCS_STATIC:-}" != "true" ]; then
  echo "[gcp-entrypoint] collectstatic (Whitenoise)..." >&2
  python manage.py collectstatic --noinput
else
  echo "[gcp-entrypoint] Skipping collectstatic — USE_GCS_STATIC enabled" >&2
fi

echo "[gcp-entrypoint] Starting gunicorn at $(date -u)" >&2
exec "$@"
