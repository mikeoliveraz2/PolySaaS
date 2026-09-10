#!/usr/bin/env bash
# Provision DigitalOcean Droplet for PolySaaS (run on laptop with doctl + token).
# Requires: doctl, DIGITALOCEAN_ACCESS_TOKEN, SSH key fingerprint.
set -euo pipefail

: "${DIGITALOCEAN_ACCESS_TOKEN:?Set DIGITALOCEAN_ACCESS_TOKEN}"
export DIGITALOCEAN_ACCESS_TOKEN

DO_REGION="${DO_REGION:-sgp1}"
DO_SIZE="${DO_SIZE:-s-4vcpu-8gb}"
DO_DROPLET_NAME="${DO_DROPLET_NAME:-polysaas-prod}"
DO_SSH_KEY_FINGERPRINT="${DO_SSH_KEY_FINGERPRINT:?Set DO_SSH_KEY_FINGERPRINT (doctl compute ssh-key list)}"
DO_IMAGE="${DO_IMAGE:-ubuntu-24-04-x64}"
DO_TAGS="${DO_TAGS:-polysaas,prod}"

echo "==> Authenticating doctl"
doctl auth init -t "$DIGITALOCEAN_ACCESS_TOKEN" >/dev/null 2>&1 || true
doctl account get

EXISTING=$(doctl compute droplet list --format ID,Name --no-header | awk -v n="$DO_DROPLET_NAME" '$2==n {print $1}')
if [[ -n "${EXISTING}" ]]; then
  echo "Droplet already exists: $DO_DROPLET_NAME ($EXISTING)"
  DROPLET_ID="$EXISTING"
else
  echo "==> Creating droplet $DO_DROPLET_NAME ($DO_SIZE @ $DO_REGION)"
  DROPLET_ID=$(doctl compute droplet create "$DO_DROPLET_NAME" \
    --region "$DO_REGION" \
    --size "$DO_SIZE" \
    --image "$DO_IMAGE" \
    --ssh-keys "$DO_SSH_KEY_FINGERPRINT" \
    --tag-names "$DO_TAGS" \
    --enable-monitoring \
    --wait \
    --format ID \
    --no-header)
  echo "Created droplet ID=$DROPLET_ID"
fi

IP=$(doctl compute droplet get "$DROPLET_ID" --format PublicIPv4 --no-header)
echo "Droplet public IP: $IP"

# Floating IP
FLOAT=$(doctl compute floating-ip list --format IP,DropletID --no-header | awk -v id="$DROPLET_ID" '$2==id {print $1}')
if [[ -z "${FLOAT}" ]]; then
  echo "==> Allocating floating IP in $DO_REGION"
  FLOAT=$(doctl compute floating-ip create --region "$DO_REGION" --format IP --no-header)
  echo "==> Assigning $FLOAT → droplet $DROPLET_ID"
  doctl compute floating-ip-action assign "$FLOAT" "$DROPLET_ID" >/dev/null
fi
echo "Floating IP: $FLOAT"

# Firewall
FW_NAME="polysaas-prod-fw"
FW_ID=$(doctl compute firewall list --format ID,Name --no-header | awk -v n="$FW_NAME" '$2==n {print $1}')
if [[ -z "${FW_ID}" ]]; then
  echo "==> Creating firewall $FW_NAME"
  doctl compute firewall create \
    --name "$FW_NAME" \
    --inbound-rules "protocol:tcp,ports:22,address:0.0.0.0/0,address:::/0 protocol:tcp,ports:80,address:0.0.0.0/0,address:::/0 protocol:tcp,ports:443,address:0.0.0.0/0,address:::/0" \
    --outbound-rules "protocol:tcp,ports:all,address:0.0.0.0/0,address:::/0 protocol:udp,ports:all,address:0.0.0.0/0,address:::/0 protocol:icmp,address:0.0.0.0/0,address:::/0" \
    --droplet-ids "$DROPLET_ID" >/dev/null
else
  echo "Firewall exists: $FW_ID — ensuring droplet attached"
  doctl compute firewall add-droplets "$FW_ID" --droplet-ids "$DROPLET_ID" >/dev/null || true
fi

echo ""
echo "=== Provision complete ==="
echo "SSH:          ssh root@$FLOAT"
echo "Next:         scp/bootstrap — see DIGITALOCEAN_DEPLOY_RUNBOOK.md"
echo "DNS A records (app/mm/odoo.polysaas.online) → $FLOAT"
echo "DROPLET_ID=$DROPLET_ID"
echo "FLOATING_IP=$FLOAT"
