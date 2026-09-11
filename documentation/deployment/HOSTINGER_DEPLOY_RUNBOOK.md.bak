# Hostinger VPS Deploy Runbook — PolySaaS core stack

**Date:** 2026-09-11  
**Scope:** Django + core Postgres + Redis (mailbox queue) + Mattermost (+ DB) + Odoo (+ DB)  
**Hostnames:** `app.polysaas.online`, `mm.polysaas.online`, `odoo.polysaas.online`  
**Apex `polysaas.online`:** remains WordPress (phase 1)  
**Platform:** Hostinger **KVM 4** VPS (4 vCPU / 16 GB / 200 GB NVMe) + Docker Compose + Traefik

Repo paths:

- Compose: [`deploy/hostinger/docker-compose.yml`](../../deploy/hostinger/docker-compose.yml)
- Env template: [`deploy/hostinger/.env.example`](../../deploy/hostinger/.env.example)
- Scripts: [`deploy/hostinger/scripts/`](../../deploy/hostinger/scripts/)

Historical (parked): [`deploy/digitalocean/`](../../deploy/digitalocean/) — do not use for new production bring-ups.

---

## Estimated cost (confirm at Hostinger checkout)

| Item | Intro (approx) | Renewal (approx) |
|------|----------------|------------------|
| KVM 4 VPS | ~$13/mo | ~$29/mo |
| Weekly backups + TLS | Included / $0 | Included / $0 |

Budget ongoing **~$30/mo** on renewal pricing.

---

## 0. Prerequisites

1. Hostinger account; billing ready.
2. SSH public key for hPanel.
3. DNS control for `polysaas.online`.
4. Local DB dumps when ready to migrate demo data.

---

## 1. Provision VPS (hPanel)

```powershell
.\deploy\hostinger\scripts\provision-vps.ps1
```

Order **KVM 4**, Ubuntu **Docker** template, note public IPv4. Firewall: **22 / 80 / 443**.

---

## 2. Bootstrap on the VPS

```bash
ssh root@<VPS_IP>
curl -fsSL https://raw.githubusercontent.com/mikeoliveraz2/PolySaaS/main/deploy/hostinger/scripts/bootstrap-vps.sh | bash
```

Edit secrets:

```bash
nano /opt/polysaas/deploy/hostinger/.env
chmod 600 /opt/polysaas/deploy/hostinger/.env
```

Generate strong passwords for `DOSE_DB_PASSWORD`, `MATTERMOST_DB_PASSWORD`, `ODOO_DB_PASSWORD`, and `DJANGO_SECRET_KEY`.

---

## 3. DNS (before HTTPS / Let’s Encrypt works)

```bash
bash /opt/polysaas/deploy/hostinger/scripts/dns-checklist.sh <VPS_IP>
```

| Name | Type | Value |
|------|------|-------|
| `app` | A | VPS public IP |
| `mm` | A | VPS public IP |
| `odoo` | A | VPS public IP |

Wait for `dig +short app.polysaas.online` to return the VPS IP.

Traefik uses **TLS-ALPN-01** (`tlsChallenge`) on port 443.

---

## 4. Bring-up

```bash
sudo -u deploy bash /opt/polysaas/deploy/hostinger/scripts/bringup.sh
```

Superuser:

```bash
cd /opt/polysaas
docker compose -f deploy/hostinger/docker-compose.yml --env-file deploy/hostinger/.env \
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
3. PassThroughEndpoint `endpoint_url` values:
   - Mattermost: `http://mattermost:8065`
   - Odoo: `http://odoo:8069`
4. Mattermost Allowed untrusted internal connections: include `django`.
5. Outgoing webhook trigger `newpolysaascontact` → `http://django:8000/hooks/mattermost/events/`.

---

## 6. Migrate demo data

On laptop:

```bash
bash deploy/hostinger/scripts/dump-local-for-restore.sh
scp deploy/hostinger/restore/*.sql.gz root@<VPS_IP>:/opt/polysaas/deploy/hostinger/restore/
```

On VPS:

```bash
bash /opt/polysaas/deploy/hostinger/scripts/migrate-data.sh
bash /opt/polysaas/deploy/hostinger/scripts/retarget-endpoints.sh
```

External webhooks:

- HubSpot FlowLink → `https://app.polysaas.online/dose/webhook/hubspot/polysaasonline/`
- Slack Events → `https://app.polysaas.online/hooks/slack/events/`

---

## 7. Smoke tests

```bash
bash /opt/polysaas/deploy/hostinger/scripts/smoke-test.sh
```

Manual:

1. Login `https://app.polysaas.online`
2. Passthrough Odoo + Mattermost
3. Post `newpolysaascontact Test Hostinger, test.host@acme.com, Acme` in Mattermost → Odoo
4. HubSpot create contact → Odoo

---

## 8. Ops

- Hostinger **weekly backups** + manual snapshot before risky upgrades.
- SSH key-only; `fail2ban` from bootstrap.
- Logs: `docker compose -f deploy/hostinger/docker-compose.yml --env-file deploy/hostinger/.env logs -f django traefik`
- Update code:

```bash
cd /opt/polysaas && sudo -u deploy git pull origin main
docker compose -f deploy/hostinger/docker-compose.yml --env-file deploy/hostinger/.env up -d --build
```

---

## Rollback

1. Leave WordPress apex unchanged.
2. Remove or repoint `app`/`mm`/`odoo` A records.
3. Keep VPS (or snapshot) 72h before cancel.
4. Local BINGO ZIPs remain gold for laptop demo.

---

## Architecture

```
Internet → Traefik (:80/:443)
         → django (app.polysaas.online)
         → mattermost (mm.polysaas.online)
         → odoo (odoo.polysaas.online)
django → core-postgres, redis
django → mattermost:8065 / odoo:8069 (passthrough)
mailbox-consumer → core-postgres (WebhookMailbox poll via Redis URL)
```
