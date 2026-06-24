# PolySaaS GCP Migration Runbook

Step-by-step operator guide for migrating from Render to GCP.

**Order:** Infrastructure → Odoo/Mattermost (Compute Engine) → local test → Django (Cloud Run) → CI/CD

---

## Prerequisites

| Tool | Purpose |
|------|---------|
| [gcloud CLI](https://cloud.google.com/sdk/docs/install) | GCP operations |
| Docker | Local image builds (optional) |
| `pg_dump` / `pg_restore` | Database migration |
| `gsutil` | File migration to GCS |

Existing Cloud SQL instance: `8.230.100.97:5432` (Django `dosedbsaas` already in use).

---

## Phase 1 — Infrastructure

```powershell
cd D:\PolySaaS
Copy-Item deploy\gcp\config.env.example deploy\gcp\config.env
# Edit config.env — project ID, Cloud SQL instance name, passwords
```

**Windows (via Git Bash):**
```powershell
.\deploy\gcp\setup-infrastructure.ps1
```

**Linux / Cloud Shell:**
```bash
bash deploy/gcp/setup-infrastructure.sh
```

Creates:
- GCS buckets: `polysaas-odoo-filestore`, `polysaas-mattermost-files`, `polysaas-django-static`, `polysaas-django-media`
- Cloud SQL databases: `odoo_prod`, `mattermost_prod`
- IAM service accounts: `polysaas-bundled-apps`, `polysaas-cloud-run`
- Artifact Registry repository

### Secret Manager (required before Cloud Run deploy)

```bash
echo -n "YOUR_DJANGO_SECRET" | gcloud secrets create django-secret-key --data-file=-
echo -n "YOUR_DB_PASSWORD"    | gcloud secrets create dose-db-password --data-file=-
```

---

## Phase 2 — Odoo + Mattermost on Compute Engine

```bash
bash deploy/gcp/provision-vm.sh
bash deploy/gcp/deploy-bundled-apps.sh
```

Files:
- [`docker-compose.gcp.yml`](docker-compose.gcp.yml) — Odoo + Mattermost against Cloud SQL
- Reuses proven Render images: [`deploy/odoo-render/`](../odoo-render/), [`deploy/mattermost-render/`](../mattermost-render/)

**Mattermost GCS (optional):** Create [HMAC keys](https://cloud.google.com/storage/docs/authentication/hmackeys) and set in `config.env`:
```
MM_FILESETTINGS_DRIVERNAME=amazons3
GCS_S3_ACCESS_KEY_ID=...
GCS_S3_SECRET_ACCESS_KEY=...
```

**DNS:** Point `odoo.polysaas.online` and `mm.polysaas.online` to the VM external IP (or add HTTPS load balancer).

---

## Phase 3 — Migrate data from Render

Put Render apps in maintenance mode, then:

```bash
# Fill RENDER_* vars in config.env
bash deploy/gcp/migrate-from-render.sh
# Or: --odoo-only / --mattermost-only
```

File exports:
```bash
gsutil -m rsync -r ./odoo-export gs://polysaas-odoo-filestore/
gsutil -m rsync -r ./mm-export   gs://polysaas-mattermost-files/
```

---

## Phase 4 — Local integration test

Merge [`deploy/gcp/.env.local-gcp.example`](.env.local-gcp.example) into repo-root `.env`:

```
ODOO_SHARED_URL=https://YOUR_GCE_IP:8069
MATTERMOST_URL=https://YOUR_GCE_IP:8065
```

```powershell
.\deploy\gcp\verify-integration.ps1
.\runall.ps1
```

Verify: passthrough sidebar, Mattermost SSO shim, Odoo orchestration (one CallBackData per path).

Update `PassThroughEndpoint` rows to point at GCP URLs when ready for cutover.

---

## Phase 5 — Django on Cloud Run

**Settings module:** `mysite.settings_gcp` (extends `settings_render` + Cloud SQL + optional GCS)

**Dockerfile:** [`Dockerfile.gcp`](../../Dockerfile.gcp)

First deploy:
```bash
bash deploy/gcp/deploy-cloud-run.sh
```

Manual smoke:
```bash
gcloud run services describe polysaas-core --region=us-central1 --format='value(status.url)'
curl -sS "$(gcloud run services describe polysaas-core --region=us-central1 --format='value(status.url)')/health/"
```

Map custom domain: Cloud Run → Domain mappings → `production.polysaas.online`

---

## Phase 6 — CI/CD (Cloud Build)

[`cloudbuild.yaml`](../../cloudbuild.yaml) at repo root:

1. Build `Dockerfile.gcp`
2. Push to Artifact Registry
3. Run `migrate_all_schemas` via Cloud SQL Auth Proxy
4. Deploy Cloud Run service

**Create trigger:**
```bash
gcloud builds triggers create github \
  --name=polysaas-main-deploy \
  --repo-name=PolySaaS \
  --repo-owner=mikeoliveraz2 \
  --branch-pattern='^main$' \
  --build-config=cloudbuild.yaml \
  --substitutions=_CLOUDSQL=PROJECT:REGION:INSTANCE
```

---

## Rollback

| Component | Rollback action |
|-----------|-----------------|
| Odoo / Mattermost | Repoint `PassThroughEndpoint` + `.env` URLs back to Render |
| Django | `gcloud run services update-traffic polysaas-core --to-revisions=PREVIOUS=100` |
| Database | Restore Cloud SQL backup taken before migration |

---

## File index

| Path | Role |
|------|------|
| `deploy/gcp/config.env.example` | Infrastructure variables template |
| `deploy/gcp/setup-infrastructure.sh` | Phase 1 gcloud script |
| `deploy/gcp/docker-compose.gcp.yml` | Bundled apps stack |
| `deploy/gcp/migrate-from-render.sh` | pg_dump/pg_restore |
| `deploy/gcp/.env.local-gcp.example` | Local desktop test overrides |
| `deploy/gcp/verify-integration.ps1` | Endpoint smoke test |
| `Dockerfile.gcp` | Django Cloud Run image |
| `mysite/settings_gcp.py` | GCP production settings |
| `cloudbuild.yaml` | CI/CD pipeline |
| `.gcloudignore` | Build upload exclusions |
