#!/usr/bin/env bash
# Run ON the DigitalOcean droplet as root (or sudo) after first SSH.
# Installs Docker, clones/updates PolySaaS, prepares compose env.
set -euo pipefail

REPO_URL="${REPO_URL:-https://github.com/mikeoliveraz2/PolySaaS.git}"
REPO_DIR="${REPO_DIR:-/opt/polysaas}"
DEPLOY_USER="${DEPLOY_USER:-deploy}"

export DEBIAN_FRONTEND=noninteractive
apt-get update -y
apt-get install -y ca-certificates curl gnupg git ufw fail2ban

# Docker Engine
if ! command -v docker >/dev/null 2>&1; then
  install -m 0755 -d /etc/apt/keyrings
  curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /etc/apt/keyrings/docker.gpg
  chmod a+r /etc/apt/keyrings/docker.gpg
  echo \
    "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
    $(. /etc/os-release && echo "$VERSION_CODENAME") stable" \
    > /etc/apt/sources.list.d/docker.list
  apt-get update -y
  apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
fi

# Deploy user
if ! id "$DEPLOY_USER" >/dev/null 2>&1; then
  adduser --disabled-password --gecos "" "$DEPLOY_USER"
fi
usermod -aG docker "$DEPLOY_USER"

# Firewall
ufw allow OpenSSH
ufw allow 80/tcp
ufw allow 443/tcp
ufw --force enable || true

# Repo
if [[ ! -d "$REPO_DIR/.git" ]]; then
  git clone "$REPO_URL" "$REPO_DIR"
else
  git -C "$REPO_DIR" fetch --all
  git -C "$REPO_DIR" checkout main
  git -C "$REPO_DIR" pull --ff-only origin main || true
fi
chown -R "$DEPLOY_USER:$DEPLOY_USER" "$REPO_DIR"

DO_DIR="$REPO_DIR/deploy/digitalocean"
chmod +x "$DO_DIR/entrypoint-django.sh" "$DO_DIR/scripts/"*.sh || true

# ACME storage permissions (Traefik requires 600)
mkdir -p /var/lib/polysaas-letsencrypt
touch /var/lib/polysaas-letsencrypt/acme.json
chmod 600 /var/lib/polysaas-letsencrypt/acme.json

if [[ ! -f "$DO_DIR/.env" ]]; then
  cp "$DO_DIR/.env.example" "$DO_DIR/.env"
  chmod 600 "$DO_DIR/.env"
  echo "Created $DO_DIR/.env — EDIT SECRETS before bring-up"
fi

echo ""
echo "=== Droplet bootstrap complete ==="
echo "1. Edit:  nano $DO_DIR/.env"
echo "2. Bring up: sudo -u $DEPLOY_USER bash $DO_DIR/scripts/bringup.sh"
echo "3. DNS: point app/mm/odoo.polysaas.online A records at this host floating IP"
