#!/bin/sh
# Render pre-deploy: run as a single argv (no shell && in YAML — Render passes the whole string to
# the first command otherwise). Invoked from /app as django user.
set -e
cd /app
python manage.py migrate_all_schemas --noinput
python manage.py bootstrap_auth
