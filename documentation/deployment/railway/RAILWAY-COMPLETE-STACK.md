# PolySaaS Complete Stack Deployment — Railway

## Overview

This guide explains how to deploy **all PolySaaS services** (core infrastructure + 3 bundled applications) to a **single Railway project**.

**Services included:**
- ✅ PostgreSQL (DOSE core database)
- ✅ RabbitMQ (Celery broker)
- ✅ Elasticsearch (search/analytics)
- ✅ Grafana (dashboards)
- ✅ MonitorLogger (OpenObserve — logs/metrics)
- ✅ **Django (PolySaaS/DOSE core)**
- ✅ Celery worker + beat
- ✅ **Mattermost** (chat platform)
- ✅ **Nextcloud** (file sharing)
- ✅ **Liferay** (portal engine)
- ⚪ Polysysmon (optional, commented out by default)

---

## Architecture

All services run on a **single Docker network** (`polysaas-network`) managed by Railway.

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
│  Nextcloud ↔ Nextcloud-DB (MariaDB)        │
│  Liferay ↔ Liferay-DB (MySQL)              │
└─────────────────────────────────────────────┘
```

**Key constraint:** All services share one Docker network. No port forwarding needed internally; services communicate via hostname (e.g., `postgres:5432`, `mattermost:8065`).

---

## Option 1: Deploy via Railway UI (Recommended for first-time)

### Step 1: Create Railway Project & Link Repo

1. Go to **https://railway.app**
2. Click **+ New Project**
3. Select **Deploy from GitHub**
4. Authorize & select `mikeoliveraz2/PolySaaS`
5. Click **Deploy** (it will detect the main `Dockerfile.django` first)

### Step 2: Switch to Docker Compose

1. In Railway project, click **Settings** (top right)
2. Under **Build**, change **Build Command** to:
   ```bash
   docker compose -f docker-compose.railway.yml up -d
   ```
3. Under **Start Command**, change to:
   ```bash
   docker compose -f docker-compose.railway.yml up -d
   ```
4. **Optional:** Delete the auto-created Django service; Railway will use the compose file instead

### Step 3: Add Environment Variables

Railway → **Variables** tab → Add the following:

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
ALLOWED_HOSTS=polysaas-prod.up.railway.app,production.polysaas.online
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

### Step 4: Deploy

1. Commit & push changes to repo (if modifying compose etc.)
   ```bash
   git add docker-compose.railway.yml
   git commit -m "Add complete PolySaaS stack for Railway deployment"
   git push origin main
   ```
2. Railway will auto-redeploy on push, **or** manually trigger via Railway UI

### Step 5: Monitor Services

1. Railway → **View Logs** — watch all services boot
2. Expected order:
   - Postgres, RabbitMQ start first
   - Elasticsearch, Grafana, MonitorLogger start
   - Django migrations run automatically (via `Dockerfile.django` entrypoint)
   - Celery worker + beat attach to RabbitMQ
   - Mattermost, Nextcloud, Liferay boot in parallel
3. Once all show **Online**, test endpoints

---

## Option 2: Deploy via Railway CLI

If you prefer command-line (faster iteration):

```bash
# Install Railway CLI
npm install -g @railway/cli

# Login
railway login

# Create project
railway init

# Deploy with docker-compose.railway.yml
railway up --config docker-compose.railway.yml

# Open Railway dashboard
railway open
```

---

## Option 3: Deploy via `railway.toml`

Create `railway.toml` in repo root:

```toml
[build]
builder = "docker"
dockerfile = "docker-compose.railway.yml"

[deploy]
startCommand = "docker compose -f docker-compose.railway.yml up -d"
healthchecks = {cmd = "docker ps"}

[env]
DJANGO_SETTINGS_MODULE = "mysite.settings"
DEBUG = "false"
```

Then:
```bash
railway up
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

### 5. Grafana
```bash
curl https://production.polysaas.online:3000/api/health
# Expected: {"database":"ok", ...}
```

### 6. Celery Worker Status
In Django admin → Celery Tasks, or:
```bash
celery -A mysite inspect active
```

---

## Updating Endpoint URLs in Django Admin

Once all services are live on Railway, update the **PassThroughEndpoint** records in Django admin:

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

**Option A: Internal networking** (recommended)
- Set endpoint URLs to internal hostnames: `http://mattermost:8065`, `http://nextcloud`, etc.
- All services communicate via Docker network (fast, no external routing)

**Option B: External access**
- Set endpoint URLs to Railway public domain + port:
  ```
  https://production.polysaas.online:8065  (Mattermost)
  https://production.polysaas.online:8888  (Nextcloud)
  https://production.polysaas.online:8181  (Liferay)
  ```
- Add port mappings in `docker-compose.railway.yml` if they're not there

---

## Size & Cost Estimates

**On Railway's free/starter tier (~$5/month):**
- Core services (Postgres 256MB, RabbitMQ, ES, Grafana, MonitorLogger) = ~$3–4/month
- Django + Celery workers = ~$1–2/month
- Mattermost, Nextcloud, Liferay = ~$4–6/month (depends on image size)
- **Total:** ~$8–12/month for a basic production setup

**If you need more capacity:**
- Upgrade individual services to larger plans
- Add multiple Celery workers (separate Railway services)
- Use external databases (Railway PostgreSQL plugin) to separate load

---

## Troubleshooting

### Services stuck in "Deploying"
- Check logs: Railway → **View Logs** → scroll to bottom
- Look for OOM (out of memory) — container too small, increase Railway plan
- Check for missing env vars — verify all `${VAR}` substitutions in compose file

### Mattermost/Nextcloud/Liferay not reachable
- Verify services are running: `docker ps` or Railway UI → **Services**
- Check health checks: look for failed health check logs
- Verify port mappings: all ports exposed in compose file?
- Check DNS: `nslookup production.polysaas.online` from test terminal

### Django can't connect to PostgreSQL
- Verify PostgreSQL pod is healthy: Railway UI → Services → postgres → Logs
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
- **Google Cloud Run** — container-to-service mesh (similar to Railway)
- **Google Kubernetes Engine (GKE)** — convert compose to Kubernetes manifests (`kompose convert docker-compose.railway.yml`)
- **Cloud SQL + Compute Engine** — traditional VMs with docker-compose

We'll document the GCP path once Railway is stable. The docker-compose approach makes it easy to move between cloud providers.

---

## Deployment Checklist

- [ ] Repo linked to Railway (GitHub auth)
- [ ] `docker-compose.railway.yml` committed & pushed
- [ ] All environment variables set in Railway UI
- [ ] Services booting (check logs for errors)
- [ ] Django migrations ran successfully
- [ ] Mattermost/Nextcloud/Liferay health checks passing
- [ ] Test endpoints reachable from curl
- [ ] PassThroughEndpoint URLs updated in admin
- [ ] Sidebar links to bundled apps now working
- [ ] Backup plan in place (Railway snapshots, DB backups)

---

## Support & Questions

For issues, check:
- Railway logs: `railway logs`
- Docker compose syntax: `docker compose -f docker-compose.railway.yml config` (validates YAML)
- Health checks: `docker ps --format "{{.Names}}\t{{.RunningFor}}\t{{.Status}}"`
