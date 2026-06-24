#!/usr/bin/env bash
# GCE startup script — installs Docker, gcsfuse, mounts Odoo filestore bucket.
set -euo pipefail

export DEBIAN_FRONTEND=noninteractive

apt-get update
apt-get install -y ca-certificates curl gnupg lsb-release fuse

# Docker
if ! command -v docker >/dev/null 2>&1; then
  install -m 0755 -d /etc/apt/keyrings
  curl -fsSL https://download.docker.com/linux/debian/gpg | gpg --dearmor -o /etc/apt/keyrings/docker.gpg
  echo \
    "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/debian \
    $(. /etc/os-release && echo "$VERSION_CODENAME") stable" \
    > /etc/apt/sources.list.d/docker.list
  apt-get update
  apt-get install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin
fi

# gcsfuse for Odoo filestore (bucket name injected via instance metadata)
GCS_BUCKET="$(curl -fsS -H "Metadata-Flavor: Google" \
  http://metadata.google.internal/computeMetadata/v1/instance/attributes/gcs-odoo-bucket 2>/dev/null || echo "")"

if [[ -n "$GCS_BUCKET" ]]; then
  if ! command -v gcsfuse >/dev/null 2>&1; then
    export GCSFUSE_REPO=gcsfuse-$(lsb_release -c -s)
    echo "deb https://packages.cloud.google.com/apt $GCSFUSE_REPO main" \
      | tee /etc/apt/sources.list.d/gcsfuse.list
    curl -fsSL https://packages.cloud.google.com/apt/doc/apt-key.gpg | apt-key add -
    apt-get update
    apt-get install -y gcsfuse
  fi
  mkdir -p /mnt/gcs/odoo-filestore
  if ! mountpoint -q /mnt/gcs/odoo-filestore; then
    gcsfuse --implicit-dirs "$GCS_BUCKET" /mnt/gcs/odoo-filestore || true
  fi
  grep -q odoo-filestore /etc/fstab || \
    echo "${GCS_BUCKET} /mnt/gcs/odoo-filestore gcsfuse rw,_netdev,allow_other,uid=101,gid=101 0 0" >> /etc/fstab
fi

mkdir -p /opt/polysaas
systemctl enable docker
systemctl start docker

echo "[vm-startup] Docker + gcsfuse ready. Deploy compose stack from /opt/polysaas."
