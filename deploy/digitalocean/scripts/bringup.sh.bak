#!/usr/bin/env bash
# Bring up PolySaaS DO stack (run on droplet from repo root or any cwd).
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
DO_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
REPO_ROOT="$(cd "$DO_DIR/../.." && pwd)"
ENV_FILE="$DO_DIR/.env"
COMPOSE=(docker compose -f "$DO_DIR/docker-compose.yml" --env-file "$ENV_FILE")

cd "$REPO_ROOT"

if [[ ! -f "$ENV_FILE" ]]; then
  echo "Missing $ENV_FILE — copy .env.example and fill secrets"
  exit 1
fi

# Ensure ACME file mode inside Traefik volume (first boot)
VOL_NAME=$(docker volume ls --format '{{.Name}}' | grep -E 'do_letsencrypt$' | head -n1 || true)
if [[ -z "${VOL_NAME}" ]]; then
  echo "==> Creating letsencrypt volume via compose config"
  "${COMPOSE[@]}" up -d traefik || true
  VOL_NAME=$(docker volume ls --format '{{.Name}}' | grep -E 'do_letsencrypt$' | head -n1 || true)
fi
if [[ -n "${VOL_NAME}" ]]; then
  docker run --rm -v "${VOL_NAME}:/letsencrypt" alpine:3.20 \
    sh -c 'touch /letsencrypt/acme.json && chmod 600 /letsencrypt/acme.json'
fi

echo "==> Building Django image"
"${COMPOSE[@]}" build django

echo "==> Starting stack"
"${COMPOSE[@]}" up -d

echo "==> Waiting for core-postgres"
for i in $(seq 1 60); do
  if "${COMPOSE[@]}" exec -T core-postgres pg_isready -U "${DB_USER:-dosedbadmin}" >/dev/null 2>&1; then
    break
  fi
  sleep 2
done

echo "==> Django migrate (all schemas via manage.py migrate)"
"${COMPOSE[@]}" run --rm --entrypoint "" django python manage.py migrate

echo "==> Status"
"${COMPOSE[@]}" ps

echo ""
echo "Next:"
echo "  1. Confirm DNS A records for app/mm/odoo → floating IP"
echo "  2. curl -fsS https://app.polysaas.online/health/"
echo "  3. Create superuser:  ${COMPOSE[*]} run --rm --entrypoint \"\" django python manage.py createsuperuser"
echo "  4. Bootstrap Mattermost admin in browser (mm.polysaas.online)"
echo "  5. Create/restore Odoo DB (odoo.polysaas.online)"
echo "  6. scripts/migrate-data.sh + scripts/smoke-test.sh"
