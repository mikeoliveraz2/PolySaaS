# DigitalOcean Deploy Runbook — PolySaaS core stack

**Date:** 2026-09-10  
**Scope:** Django + core Postgres + Redis + Mattermost (+ DB) + Odoo (+ DB)  
**Hostnames:** `app.polysaas.online`, `mm.polysaas.online`, `odoo.polysaas.online`  
**Apex `polysaas.online`:** remains WordPress (phase 1)

Repo paths:

- Compose: [`deploy/digitalocean/docker-compose.yml`](../../deploy/digitalocean/docker-compose.yml)
- Env template: [`deploy/digitalocean/.env.example`](../../deploy/digitalocean/.env.example)
- Scripts: [`deploy/digitalocean/scripts/`](../../deploy/digitalocean/scripts/)

---

## 0. Prerequisites

1. DigitalOcean account + billing.
2. SSH key uploaded to DO (`doctl compute ssh-key list`).
3. DNS control for `polysaas.online`.
4. On laptop: `doctl` + `DIGITALOCEAN_ACCESS_TOKEN`.
5. Local DB dumps when ready to migrate demo data (`scripts/dump-local-for-restore.sh`).

---

## 1. Provision Droplet

```powershell
$env:DIGITALOCEAN_ACCESS_TOKEN = "dop_v1_..."
$env:DO_SSH_KEY_FINGERPRINT = "xx:xx:..."   # from doctl compute ssh-key list
$env:DO_REGION = "sgp1"                     # or nyc1 / etc.
$env:DO_SIZE = "s-4vcpu-8gb"                # prefer s-8vcpu-16gb if budget allows
.\deploy\digitalocean\scripts\provision-droplet.ps1
```

Script creates Ubuntu 24.04 droplet, floating IP, and firewall (22/80/443).

Note floating IP printed at the end.

---

## 2. Bootstrap Docker on the droplet

```bash
ssh root@<FLOATING_IP>
curl -fsSL https://raw.githubusercontent.com/mikeoliveraz2/PolySaaS/main/deploy/digitalocean/scripts/bootstrap-droplet.sh | bash
# Or after git clone already present:
bash /opt/polysaas/deploy/digitalocean/scripts/bootstrap-droplet.sh
```

Edit secrets:

```bash
nano /opt/polysaas/deploy/digitalocean/.env
chmod 600 /opt/polysaas/deploy/digitalocean/.env
```

---

## 3. DNS (before HTTPS works)

```bash
bash /opt/polysaas/deploy/digitalocean/scripts/dns-checklist.sh <FLOATING_IP>
```

Create A records:

| Name | Type | Value |
|------|------|-------|
| `app` | A | floating IP |
| `mm` | A | floating IP |
| `odoo` | A | floating IP |

Wait for `dig +short app.polysaas.online` to return the floating IP.

---

## 4. Bring-up

```bash
sudo -u deploy bash /opt/polysaas/deploy/digitalocean/scripts/bringup.sh
```

Creates containers, migrates Django, prints next steps.

Superuser:

```bash
cd /opt/polysaas
docker compose -f deploy/digitalocean/docker-compose.yml --env-file deploy/digitalocean/.env \
  run --rm --entrypoint "" django python manage.py createsuperuser
```

Verify:

```bash
curl -fsS https://app.polysaas.online/health/
```

---

## 5. Bootstrap Mattermost & Odoo (empty stack)

1. Open `https://mm.polysaas.online` — create first admin + team.
2. Open `https://odoo.polysaas.online` — create database / master password.
3. In Django admin / tenant schema: set PassThroughEndpoint `endpoint_url` values:
   - Mattermost: prefer `http://mattermost:8065` for server-side proxy
   - Odoo: prefer `http://odoo:8069`
4. Mattermost System Console → Allowed untrusted internal connections: include `django`.
5. Recreate outgoing webhook trigger `newpolysaascontact` → callback `http://django:8000/hooks/mattermost/events/`.

---

## 6. Migrate demo data (optional)

On laptop (with local compose up):

```bash
bash deploy/digitalocean/scripts/dump-local-for-restore.sh
scp deploy/digitalocean/restore/*.sql.gz root@<FLOATING_IP>:/opt/polysaas/deploy/digitalocean/restore/
```

On droplet:

```bash
bash /opt/polysaas/deploy/digitalocean/scripts/migrate-data.sh
```

Then retarget webhooks:

- HubSpot FlowLink → `https://app.polysaas.online/dose/webhook/hubspot/polysaasonline/`
- Slack Events → `https://app.polysaas.online/hooks/slack/events/`

---

## 7. Smoke tests

```bash
bash /opt/polysaas/deploy/digitalocean/scripts/smoke-test.sh
```

Manual:

1. Login `https://app.polysaas.online`
2. Passthrough Odoo + Mattermost
3. Post `newpolysaascontact Test DO, test.do@acme.com, Acme` in Mattermost → Odoo contact
4. HubSpot create contact → Odoo

---

## 8. Ops

- Snapshots: DigitalOcean Droplet weekly snapshot (+ before risky upgrades).
- SSH: key-only; `fail2ban` installed by bootstrap.
- Logs: `docker compose -f deploy/digitalocean/docker-compose.yml logs -f django traefik`
- Update code:

```bash
cd /opt/polysaas && sudo -u deploy git pull origin main
docker compose -f deploy/digitalocean/docker-compose.yml --env-file deploy/digitalocean/.env up -d --build
```

---

## Rollback

1. Leave WordPress apex unchanged.
2. Remove or point `app`/`mm`/`odoo` A records away from the droplet.
3. Power off (do not destroy) droplet for 72h.
4. Local BINGO ZIPs remain the gold restore for laptop demo.

---

## Architecture reminder

```
Internet → Traefik (:80/:443)
         → django (app.polysaas.online)
         → mattermost (mm.polysaas.online)
         → odoo (odoo.polysaas.online)
django → core-postgres, redis
django → mattermost:8065 / odoo:8069 (passthrough)
mailbox-consumer → core-postgres (WebhookMailbox poll)
```
