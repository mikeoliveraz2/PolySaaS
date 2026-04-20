#!/bin/sh
# Render pre-deploy: single argv in render.yaml (no bare &&). Runs as django user, cwd /app.
set -ex
cd /app
echo "[render-predeploy] $(date -u) starting in $(pwd) as $(whoami)" >&2
echo "[render-predeploy] migrate_all_schemas..." >&2
python manage.py migrate_all_schemas --noinput
echo "[render-predeploy] bootstrap_auth..." >&2
python manage.py bootstrap_auth
echo "[render-predeploy] $(date -u) finished OK" >&2
