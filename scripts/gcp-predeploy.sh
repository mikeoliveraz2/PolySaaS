#!/bin/sh
# Cloud Build pre-deploy / migration job — all tenant schemas.
set -ex
cd /app
echo "[gcp-predeploy] $(date -u) starting as $(whoami)" >&2
echo "[gcp-predeploy] migrate_all_schemas..." >&2
python manage.py migrate_all_schemas --noinput
echo "[gcp-predeploy] bootstrap_auth..." >&2
python manage.py bootstrap_auth
echo "[gcp-predeploy] $(date -u) finished OK" >&2
