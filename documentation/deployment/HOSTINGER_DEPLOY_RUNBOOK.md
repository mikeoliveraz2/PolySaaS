# Hostinger VPS + Dokploy Deploy Runbook — PolySaaS core stack

**Date:** 2026-09-12  
**Scope:** Django + core Postgres + Redis (mailbox queue) + Mattermost (+ DB) + Odoo (+ DB)  
**Orchestrator:** **Dokploy** (built-in Traefik / Let’s Encrypt)  
**VPS IP:** `187.53.138.235`  
**Domain:** `prod-polysaas.cloud`  
**Hostnames:** `app.prod-polysaas.cloud`, `mm.prod-polysaas.cloud`, `odoo.prod-polysaas.cloud`  
**Apex `polysaas.online`:** remains WordPress (phase 1)

Repo paths:

- Compose: [`deploy/hostinger/docker-compose.yml`](../../deploy/hostinger/docker-compose.yml)
- Env template: [`deploy/hostinger/.env.example`](../../deploy/hostinger/.env.example)
- Scripts: [`deploy/hostinger/scripts/`](../../deploy/hostinger/scripts/)

---

## Estimated cost

| Item | Intro (approx) | Renewal (approx) |
|------|----------------|------------------|
| Hostinger KVM 4 | ~$13/mo | ~$29/mo |
| Dokploy / TLS / weekly backups | Included / $0 | Included / $0 |

Budget ongoing **~$30/mo**.

---

## Architecture note (Dokploy)

- Dokploy Traefik terminates TLS on the host.
- Compose attaches public apps to external network **`dokploy-network`**.
- Internal DBs/Redis stay on private network **`polysaas-hostinger`**.
- No `container_name` (Dokploy logs/metrics).
- Local [`traefik.yml`](../../deploy/hostinger/traefik.yml) is **not used**.

```
Internet → Dokploy Traefik (:80/:443)
         → django (app.prod-polysaas.cloud)
         → mattermost (mm.prod-polysaas.cloud)
         → odoo (odoo.prod-polysaas.cloud)
django → core-postgres, redis (internal)
```

---

## 1. DNS

```bash
bash deploy/hostinger/scripts/dns-checklist.sh 187.53.138.235
```

| Name | Type | Value |
|------|------|-------|
| `app.prod-polysaas.cloud` | A | `187.53.138.235` |
| `mm.prod-polysaas.cloud` | A | `187.53.138.235` |
| `odoo.prod-polysaas.cloud` | A | `187.53.138.235` |

---

## 2. Secrets

Copy `.env.example` → `.env` (Dokploy env UI or file on VPS). Set strong passwords and `DJANGO_SECRET_KEY`.

---

## 3. Deploy via Dokploy (preferred)

1. Dokploy → **Compose** application.
2. Connect GitHub `mikeoliveraz2/PolySaaS` (or upload compose).
3. Compose path: `deploy/hostinger/docker-compose.yml`.
4. Paste env vars from `.env.example` (filled).
5. Deploy. Confirm services join `dokploy-network`.
6. Domains tab (optional): can also bind domains in UI; labels in compose already set Host rules.

SSH alternative (after key auth works):

```bash
cd /opt/polysaas   # or clone path
cp deploy/hostinger/.env.example deploy/hostinger/.env
nano deploy/hostinger/.env
bash deploy/hostinger/scripts/bringup.sh
```

Laptop SSH key to authorize:

```
ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIH1slI825aF3O21Tg14ymOZwFfAFHWsxJcH24lYSA+W9 polysaas-hostinger@DESKTOP-VNV4SUD
```

---

## 4. Post-deploy

```bash
# migrate already in bringup.sh; superuser:
docker compose -f deploy/hostinger/docker-compose.yml --env-file deploy/hostinger/.env \
  run --rm --entrypoint "" django python manage.py createsuperuser

curl -fsS https://app.prod-polysaas.cloud/health/
```

1. Mattermost first admin at `https://mm.prod-polysaas.cloud`
2. Odoo DB at `https://odoo.prod-polysaas.cloud`
3. PassThroughEndpoint URLs: MM `http://mattermost:8065`, Odoo `http://odoo:8069`
4. MM webhook `newpolysaascontact` → `http://django:8000/hooks/mattermost/events/`

---

## 5. Data migration + webhooks

```bash
bash deploy/hostinger/scripts/dump-local-for-restore.sh
scp deploy/hostinger/restore/*.sql.gz root@187.53.138.235:/opt/polysaas/deploy/hostinger/restore/
# on VPS:
bash deploy/hostinger/scripts/migrate-data.sh
bash deploy/hostinger/scripts/retarget-endpoints.sh
```

- HubSpot → `https://app.prod-polysaas.cloud/dose/webhook/hubspot/polysaasonline/`
- Slack → `https://app.prod-polysaas.cloud/hooks/slack/events/`

---

## 6. Smoke

```bash
bash deploy/hostinger/scripts/smoke-test.sh
```

---

## Rollback

1. Leave `polysaas.online` WordPress alone.
2. Remove/repoint `app`/`mm`/`odoo` under `prod-polysaas.cloud`.
3. Keep VPS/Dokploy 72h before cancel.
4. Local BINGO ZIPs remain gold for laptop demo.
