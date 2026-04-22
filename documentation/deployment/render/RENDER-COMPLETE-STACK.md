# PolySaaS Complete Stack Deployment — Render

## Overview

This guide explains how to deploy **all PolySaaS services** (core infrastructure + 3 bundled applications) to a **single Render project**.

**Services included:**
- ✅ PostgreSQL (DOSE core database)
- ✅ RabbitMQ (Celery broker)
- ✅ Elasticsearch (search/analytics)
- ✅ Grafana (dashboards)
- ✅ MonitorLogger (OpenObserve — logs/metrics)
- ✅ **Django (PolySaaS/DOSE core)**
- ✅ Celery worker + beat
- ✅ **Mattermost** (chat platform)
- ✅ **Odoo** (ERP platform)
- ✅ **Nextcloud** (file sharing)
- ✅ **Liferay** (portal engine)
- ⚪ Polysysmon (optional, commented out by default)

---

## Architecture

All services run on a **single Docker network** (`polysaas-network`) managed by Render.

```
┌─────────────────────────────────────────────┐
│            Railroad Container Layer         │
├─────────────────────────────────────────────┤
│  Django (DOSE) ←→ PostgreSQL                │
│  ↓ (AMQP)                                   │
│  RabbitMQ ←→ Celery worker + beat           │
│  ↓                                          │
│  Elasticsearch ← Logs/metrics               │
│  ↓                                          │
│  Grafana (dashboards)                       │
│  MonitorLogger (ingestion)                  │
├─────────────────────────────────────────────┤
│  Mattermost ↔ Mattermost-DB (Postgres)      │
│  Odoo ↔ Odoo-DB (Postgres)                  │
│  Nextcloud ↔ Nextcloud-DB (MariaDB)        │
│  Liferay ↔ Liferay-DB (MySQL)              │
└─────────────────────────────────────────────┘
```

**Key constraint:** All services share one Docker network. No port forwarding needed internally; services communicate via hostname (e.g., `postgres:5432`, `mattermost:8065`).

---

## Option 1: Deploy via Render UI (Recommended for first-time)

### Step 1: Create Render Project & Link Repo

1. Go to **https://render.com**
2. Click **+ New Project**
3. Select **Deploy from GitHub**
4. Authorize & select `mikeoliveraz2/PolySaaS`
5. Click **Deploy** (it will detect the main `Dockerfile.django` first)

### Step 2: Switch to Docker Compose

1. In Render project, click **Settings** (top right)
2. Under **Build**, change **Build Command** to:
   ```bash
   docker compose -f docker-compose.Render.yml up -d
   ```
3. Under **Start Command**, change to:
   ```bash
   docker compose -f docker-compose.Render.yml up -d
   ```
4. **Optional:** Delete the auto-created Django service; Render will use the compose file instead

### Step 3: Add Environment Variables

Render → **Variables** tab → Add the following:

#### Core Infrastructure
```
DOSE_DB_USER=dosedbadmin
DOSE_DB_PASSWORD=<generate-strong-password>
DOSE_DB=dosedbsaas

RABBITMQ_USER=guest
RABBITMQ_PASS=<generate-strong-password>

GRAFANA_USER=admin
GRAFANA_PASS=<generate-strong-password>

MONITORLOGGER_ROOT_USER_EMAIL=admin@polysaas.online
MONITORLOGGER_ROOT_USER_PASSWORD=<generate-strong-password>
```

#### Django / DOSE
```
DJANGO_SETTINGS_MODULE=mysite.settings
DJANGO_SECRET_KEY=<generate-strong-secret-key>
DEBUG=false
ALLOWED_HOSTS=polysaas-prod.onrender.com,production.polysaas.online
DATABASE_URL=postgresql://dosedbadmin:<password>@postgres:5432/dosedbsaas
CELERY_BROKER_URL=amqp://guest:<password>@rabbitmq:5672//
ELASTICSEARCH_HOST=http://elasticsearch:9200
```

#### Mattermost
```
MATTERMOST_DB_USER=mattermost
MATTERMOST_DB_PASSWORD=<generate-strong-password>
MATTERMOST_DB=mattermost
MATTERMOST_SITE_URL=https://production.polysaas.online:8065
```

#### Nextcloud
```
NEXTCLOUD_ADMIN_USER=admin
NEXTCLOUD_ADMIN_PASSWORD=<generate-strong-password>
NEXTCLOUD_DB_USER=nextcloud
NEXTCLOUD_DB_PASSWORD=<generate-strong-password>
NEXTCLOUD_DB=nextcloud
NEXTCLOUD_TRUSTED_DOMAINS=localhost 127.0.0.1 production.polysaas.online
NEXTCLOUD_HOST=production.polysaas.online:8888
NEXTCLOUD_CLI_URL=https://production.polysaas.online:8888
NEXTCLOUD_PROTOCOL=https
```

#### Liferay
```
LIFERAY_DB_USER=liferay
LIFERAY_DB_PASSWORD=<generate-strong-password>
LIFERAY_DB=lportal
LIFERAY_MYSQL_ROOT_PASSWORD=<generate-strong-password>
```

#### Odoo
```
DB_HOST=${{Postgres.PGHOST}}
DB_PORT=${{Postgres.PGPORT}}
DB_USER=odoo_user
DB_PASSWORD=<set-in-postgres-and-match-exactly>
DB_NAME=odoo
```

### Step 4: Deploy

1. Commit & push changes to repo (if modifying compose etc.)
   ```bash
   git add docker-compose.Render.yml
   git commit -m "Add complete PolySaaS stack for Render deployment"
   git push origin main
   ```
2. Render will auto-redeploy on push, **or** manually trigger via Render UI

### Step 5: Monitor Services

1. Render → **View Logs** — watch all services boot
2. Expected order:
   - Postgres, RabbitMQ start first
   - Elasticsearch, Grafana, MonitorLogger start
   - Django migrations run automatically (via `Dockerfile.django` entrypoint)
   - Celery worker + beat attach to RabbitMQ
   - Mattermost, Nextcloud, Liferay boot in parallel
3. Once all show **Online**, test endpoints

---

## Option 2: Deploy via Render CLI

If you prefer command-line (faster iteration):

```bash
# Install Render CLI
npm install -g @Render/cli

# Login
Render login

# Create project
Render init

# Deploy with docker-compose.Render.yml
Render up --config docker-compose.Render.yml

# Open Render dashboard
Render open
```

---

## Option 3: Deploy via `Render.toml`

Create `Render.toml` in repo root:

```toml
[build]
builder = "docker"
dockerfile = "docker-compose.Render.yml"

[deploy]
startCommand = "docker compose -f docker-compose.Render.yml up -d"
healthchecks = {cmd = "docker ps"}

[env]
DJANGO_SETTINGS_MODULE = "mysite.settings"
DEBUG = "false"
```

Then:
```bash
Render up
```

---

## Testing After Deployment

### 1. Django Admin
```bash
curl -u admin:ChangeMeNow123! https://production.polysaas.online/admin/
```

### 2. Mattermost
```bash
curl https://production.polysaas.online:8065/api/v4/system/ping
# Expected: {"status":"OK"}
```

### 3. Nextcloud
```bash
curl https://production.polysaas.online:8888/status.php
# Expected: {"installed":true, ...}
```

### 4. Liferay
```bash
curl https://production.polysaas.online:8181/web/guest/home
# Should return HTML home page
```

### 5. Odoo
```bash
curl -I https://odoo-production-ed0e.onrender.com/web/login
# Expected: HTTP 200/303
```

### 6. Grafana
```bash
curl https://production.polysaas.online:3000/api/health
# Expected: {"database":"ok", ...}
```

### 7. Celery Worker Status
In Django admin → Celery Tasks, or:
```bash
celery -A mysite inspect active
```

---

## Updating Endpoint URLs in Django Admin

Once all services are live on Render, update the **PassThroughEndpoint** records in Django admin:

1. Go to **https://production.polysaas.online/admin/dose/passthroughendpoint/**
2. For **Mattermost**:
   - URL: `https://mattermost:8065`
   - or if external: `https://production.polysaas.online:8065`
3. For **Nextcloud**:
   - URL: `https://nextcloud:80` (or `:8080` depending on mapping)
   - or if external: `https://production.polysaas.online:8888`
4. For **Liferay**:
   - URL: `https://liferay:8080`
   - or if external: `https://production.polysaas.online:8181`
5. For **Odoo**:
   - URL: `http://odoo:8069`
   - or if external: `https://odoo-production-ed0e.onrender.com`

**Option A: Internal networking** (recommended)
- Set endpoint URLs to internal hostnames: `http://mattermost:8065`, `http://nextcloud`, etc.
- All services communicate via Docker network (fast, no external routing)

**Option B: External access**
- Set endpoint URLs to per-service Render public domains:
  ```
   https://<mattermost-service>.onrender.com  (Mattermost)
   https://<odoo-service>.onrender.com        (Odoo)
   https://<nextcloud-service>.onrender.com   (Nextcloud)
   https://<liferay-service>.onrender.com     (Liferay)
  ```
- Render routes public traffic to each service domain directly; avoid relying on custom port suffixes on a shared domain

---

## Size & Cost Estimates

**On Render's free/starter tier (~$5/month):**
- Core services (Postgres 256MB, RabbitMQ, ES, Grafana, MonitorLogger) = ~$3–4/month
- Django + Celery workers = ~$1–2/month
- Mattermost, Nextcloud, Liferay = ~$4–6/month (depends on image size)
- **Total:** ~$8–12/month for a basic production setup

**If you need more capacity:**
- Upgrade individual services to larger plans
- Add multiple Celery workers (separate Render services)
- Use external databases (Render PostgreSQL plugin) to separate load

---

## Troubleshooting

### Services stuck in "Deploying"
- Check logs: Render → **View Logs** → scroll to bottom
- Look for OOM (out of memory) — container too small, increase Render plan
- Check for missing env vars — verify all `${VAR}` substitutions in compose file

### Mattermost/Nextcloud/Liferay not reachable
- Verify services are running: `docker ps` or Render UI → **Services**
- Check health checks: look for failed health check logs
- Verify port mappings: all ports exposed in compose file?
- Check DNS: `nslookup production.polysaas.online` from test terminal

### Django can't connect to PostgreSQL
- Verify PostgreSQL pod is healthy: Render UI → Services → postgres → Logs

### Odoo: `password authentication failed for user "odoo_user"`
- Root cause: `DB_PASSWORD` in Odoo service does not match the password set for `odoo_user` in Postgres
- Verify/fix with a DB admin client (Adminer recommended in-project)
- In Postgres, run:
   ```sql
   ALTER ROLE odoo_user WITH LOGIN PASSWORD 'PolySaaS2026!';
   ALTER DATABASE odoo OWNER TO odoo_user;
   GRANT ALL PRIVILEGES ON DATABASE odoo TO odoo_user;
   ```
- In Odoo service variables, set exactly:
   ```
   DB_HOST=postgres.Render.internal
   DB_PORT=5432
   DB_USER=odoo_user
   DB_PASSWORD=PolySaaS2026!
   DB_NAME=odoo
   ```
- Remove conflicting vars on Odoo service: `USER`, `PASSWORD`, `HOST`, `PORT`, `DATABASE`, and any `PG*`

### Adminer quick setup (in Render project)
- Create service from image: `adminer:latest`
- Set `ADMINER_DEFAULT_SERVER=postgres.Render.internal`
- Login values:
   - System: `PostgreSQL`
   - Server: `postgres.Render.internal`
   - Username: `postgres`
   - Database: `postgres`
- Verify env var `DATABASE_URL` is set correctly
- Check network: are `django` and `postgres` on same Docker network? (Yes, both on `polysaas-network`)

### RabbitMQ not accepting Celery connections
- Check `CELERY_BROKER_URL` format: should be `amqp://USER:PASS@rabbitmq:5672//`
- Verify RabbitMQ is healthy: check logs for startup errors
- If custom user/pass, ensure both `RABBITMQ_USER` and `CELERY_BROKER_URL` match

### High memory usage
- Elasticsearch is heavy (~512MB); consider disabling if not needed
- Mattermost + Nextcloud combined can use 1GB+
- Optional: remove unused services commenting them out in compose file

---

## Next Steps (Future: GCP Deployment)

For GCP (Google Cloud), you can use:
- **Google Cloud Run** — container-to-service mesh (similar to Render)
- **Google Kubernetes Engine (GKE)** — convert compose to Kubernetes manifests (`kompose convert docker-compose.Render.yml`)
- **Cloud SQL + Compute Engine** — traditional VMs with docker-compose

We'll document the GCP path once Render is stable. The docker-compose approach makes it easy to move between cloud providers.

---

## Deployment Checklist

- [ ] Repo linked to Render (GitHub auth)
- [ ] `docker-compose.Render.yml` committed & pushed
- [ ] All environment variables set in Render UI
- [ ] Services booting (check logs for errors)
- [ ] Django migrations ran successfully
- [ ] Mattermost/Nextcloud/Liferay health checks passing
- [ ] Odoo is reachable at /web/login
- [ ] Test endpoints reachable from curl
- [ ] PassThroughEndpoint URLs updated in admin
- [ ] Sidebar links to bundled apps now working
- [ ] Backup plan in place (Render snapshots, DB backups)

---

## Support & Questions

For issues, check:
- Render logs: `Render logs`
- Docker compose syntax: `docker compose -f docker-compose.Render.yml config` (validates YAML)
- Health checks: `docker ps --format "{{.Names}}\t{{.RunningFor}}\t{{.Status}}"`
