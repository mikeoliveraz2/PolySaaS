#!/bin/sh
# PolySaaS Django container entrypoint (Hostinger / hosted).
# Usage: CMD web | consumer | shell | migrate
set -e

MODE="${1:-web}"
shift || true

export DJANGO_SETTINGS_MODULE="${DJANGO_SETTINGS_MODULE:-mysite.settings_hosted}"

case "$MODE" in
  web)
    exec python -m gunicorn \
      --bind "0.0.0.0:${PORT:-8000}" \
      --workers "${GUNICORN_WORKERS:-2}" \
      --threads "${GUNICORN_THREADS:-4}" \
      --timeout "${GUNICORN_TIMEOUT:-60}" \
      --access-logfile - \
      --error-logfile - \
      mysite.wsgi:application
    ;;
  consumer)
    exec python manage.py start_mailbox_consumer \
      --poll-interval "${MAILBOX_POLL_INTERVAL:-1.0}" \
      --batch-size "${MAILBOX_BATCH_SIZE:-10}"
    ;;
  migrate)
    exec python manage.py migrate "$@"
    ;;
  shell)
    exec python manage.py shell "$@"
    ;;
  *)
    exec "$MODE" "$@"
    ;;
esac
