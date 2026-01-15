# GCP Deployment Guide for DoseV3MasterSaaS

## Prerequisites

1. **Google Cloud Account**: Sign up at https://cloud.google.com/
2. **gcloud CLI**: Install from https://cloud.google.com/sdk/docs/install
3. **Docker**: Install from https://docs.docker.com/get-docker/
4. **Project billing enabled**: Required for Cloud Run and Cloud SQL

## Quick Start (Estimated time: 30-45 minutes)

### Step 1: Set Up GCP Project

```powershell
# Login to Google Cloud
gcloud auth login

# Create a new project (or use existing)
gcloud projects create dosev3-saas --name="DoseV3 SaaS"

# Set the project as active
gcloud config set project dosev3-saas

# Enable required APIs
gcloud services enable \
    run.googleapis.com \
    sql-component.googleapis.com \
    sqladmin.googleapis.com \
    cloudbuild.googleapis.com \
    containerregistry.googleapis.com \
    secretmanager.googleapis.com
```

### Step 2: Create Cloud SQL PostgreSQL Instance

```powershell
# Create PostgreSQL instance (this takes 5-10 minutes)
gcloud sql instances create dosev3-postgres `
    --database-version=POSTGRES_15 `
    --tier=db-f1-micro `
    --region=us-central1 `
    --root-password=YOUR_ROOT_PASSWORD_HERE

# Create the database
gcloud sql databases create dosedbsaas --instance=dosev3-postgres

# Create database user
gcloud sql users create dosedbadmin `
    --instance=dosev3-postgres `
    --password=YOUR_DB_PASSWORD_HERE

# Get connection name (save this - you'll need it)
gcloud sql instances describe dosev3-postgres --format="value(connectionName)"
# Output format: project-id:region:instance-name
```

### Step 3: Store Secrets in Secret Manager

```powershell
# Create secret for Django SECRET_KEY
echo "your-super-secret-django-key-here" | gcloud secrets create django-secret-key --data-file=-

# Create secret for database password
echo "YOUR_DB_PASSWORD_HERE" | gcloud secrets create dose-db-password --data-file=-

# Grant Cloud Run access to secrets
gcloud secrets add-iam-policy-binding django-secret-key `
    --member="serviceAccount:PROJECT_NUMBER-compute@developer.gserviceaccount.com" `
    --role="roles/secretmanager.secretAccessor"

gcloud secrets add-iam-policy-binding dose-db-password `
    --member="serviceAccount:PROJECT_NUMBER-compute@developer.gserviceaccount.com" `
    --role="roles/secretmanager.secretAccessor"
```

### Step 4: Build and Deploy

```powershell
# Build the container image
gcloud builds submit --tag gcr.io/dosev3-saas/dosev3-app

# Deploy to Cloud Run (first time)
gcloud run deploy dosev3-saas `
    --image gcr.io/dosev3-saas/dosev3-app `
    --platform managed `
    --region us-central1 `
    --allow-unauthenticated `
    --set-env-vars "DJANGO_SECRET_KEY=$(gcloud secrets versions access latest --secret=django-secret-key)" `
    --set-env-vars "DOSE_DB_PASSWORD=$(gcloud secrets versions access latest --secret=dose-db-password)" `
    --set-env-vars "DB_HOST=/cloudsql/PROJECT_ID:us-central1:dosev3-postgres" `
    --set-env-vars "DB_NAME=dosedbsaas" `
    --set-env-vars "DB_USER=dosedbadmin" `
    --set-env-vars "USE_CLOUD_SQL=True" `
    --add-cloudsql-instances PROJECT_ID:us-central1:dosev3-postgres `
    --memory 1Gi `
    --cpu 1 `
    --max-instances 10
```

### Step 5: Run Database Migrations

```powershell
# Connect to Cloud SQL via proxy (in a separate terminal)
cloud_sql_proxy -instances=PROJECT_ID:us-central1:dosev3-postgres=tcp:5433

# In your main terminal, run migrations
python manage.py migrate --settings=mysite.settings_production

# Create superuser
python manage.py createsuperuser --settings=mysite.settings_production
```

**OR** run migrations via Cloud Run job:

```powershell
# One-time migration job
gcloud run jobs create dosev3-migrate `
    --image gcr.io/dosev3-saas/dosev3-app `
    --region us-central1 `
    --set-env-vars "DJANGO_SECRET_KEY=$(gcloud secrets versions access latest --secret=django-secret-key)" `
    --set-env-vars "DOSE_DB_PASSWORD=$(gcloud secrets versions access latest --secret=dose-db-password)" `
    --set-cloudsql-instances PROJECT_ID:us-central1:dosev3-postgres `
    --command "python,manage.py,migrate,--noinput"

# Execute the job
gcloud run jobs execute dosev3-migrate --region us-central1
```

## Architecture Overview

```
┌─────────────────────────────────────────────────────────┐
│  Internet Users                                          │
└────────────────┬────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────┐
│  Cloud Load Balancer (HTTPS)                            │
└────────────────┬────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────┐
│  Cloud Run (Managed Container)                          │
│  ┌───────────────────────────────────────────────────┐  │
│  │  Django App (Gunicorn)                            │  │
│  │  - Auto-scaling (0-10 instances)                  │  │
│  │  - 1 vCPU, 1GB RAM per instance                   │  │
│  │  - Serves on port 8080                            │  │
│  └───────────────────────────────────────────────────┘  │
└────────────────┬────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────┐
│  Cloud SQL (PostgreSQL 15)                              │
│  - Private IP connection via Unix socket                │
│  - Automated backups                                    │
│  - High availability option available                   │
└─────────────────────────────────────────────────────────┘
```

## Configuration Files Created

1. **Dockerfile** - Container definition
2. **.dockerignore** - Exclude files from Docker build
3. **.gcloudignore** - Exclude files from GCP deployment
4. **cloudbuild.yaml** - Automated build configuration
5. **mysite/settings_production.py** - Production Django settings

## Environment Variables

Set these in Cloud Run:

| Variable | Description | Example |
|----------|-------------|---------|
| `DJANGO_SECRET_KEY` | Django secret key | From Secret Manager |
| `DOSE_DB_PASSWORD` | Database password | From Secret Manager |
| `DB_HOST` | Cloud SQL connection | `/cloudsql/project:region:instance` |
| `DB_NAME` | Database name | `dosedbsaas` |
| `DB_USER` | Database user | `dosedbadmin` |
| `USE_CLOUD_SQL` | Enable Cloud SQL | `True` |
| `ALLOWED_HOSTS` | Allowed domains | `dosev3-saas-xxx.run.app,yourdomain.com` |
| `DEBUG` | Debug mode | `False` (production) |

## Cost Estimation (Monthly)

**Free Tier Usage:**
- Cloud Run: 2 million requests free
- Cloud SQL: f1-micro not in free tier
- Cloud Storage: 5GB free
- Secret Manager: 6 secrets free

**Estimated Costs (Low Traffic):**
- Cloud Run: $0-5/month (with free tier)
- Cloud SQL f1-micro: ~$7-10/month
- Cloud Storage: $0-1/month
- **Total: ~$8-16/month for low traffic**

**Scaling (Medium Traffic - 100k requests/month):**
- Cloud Run: ~$10-20/month
- Cloud SQL db-n1-standard-1: ~$50/month
- **Total: ~$60-70/month**

## Custom Domain Setup

```powershell
# Map custom domain to Cloud Run
gcloud run domain-mappings create --service dosev3-saas --domain yourdomain.com --region us-central1

# Follow instructions to update DNS records
# Cloud Run will automatically provision SSL certificate
```

## Continuous Deployment with Cloud Build

### Option 1: GitHub Integration

1. Go to Cloud Build Triggers: https://console.cloud.google.com/cloud-build/triggers
2. Click "Connect Repository"
3. Select GitHub and authorize
4. Choose your repository
5. Create trigger:
   - Event: Push to branch
   - Branch: `^main$`
   - Build configuration: `cloudbuild.yaml`
6. Set substitution variables in trigger settings

### Option 2: Manual Deploy

```powershell
# Submit build manually
gcloud builds submit --config cloudbuild.yaml `
    --substitutions _DJANGO_SECRET_KEY="your-key",_DOSE_DB_PASSWORD="your-pass",_CLOUDSQL_CONNECTION="project:region:instance"
```

## Static Files with Cloud Storage (Optional)

```powershell
# Create Cloud Storage bucket
gsutil mb -l us-central1 gs://dosev3-static/

# Make bucket publicly readable
gsutil iam ch allUsers:objectViewer gs://dosev3-static/

# Install django-storages
pip install django-storages[google]

# Update environment variables
gcloud run services update dosev3-saas `
    --set-env-vars "USE_GCS_STATIC=True,GCS_BUCKET_NAME=dosev3-static,GCP_PROJECT_ID=dosev3-saas" `
    --region us-central1
```

## Monitoring and Logging

```powershell
# View logs
gcloud run services logs read dosev3-saas --region us-central1 --limit 50

# Real-time logs
gcloud run services logs tail dosev3-saas --region us-central1

# View in Cloud Console
https://console.cloud.google.com/run/detail/us-central1/dosev3-saas/logs
```

## Troubleshooting

### Issue: Container fails to start

```powershell
# Check logs
gcloud run services logs read dosev3-saas --region us-central1 --limit 100

# Common issues:
# 1. Missing environment variables
# 2. Database connection failure
# 3. collectstatic errors
```

### Issue: Database connection timeout

```powershell
# Verify Cloud SQL connection name
gcloud sql instances describe dosev3-postgres --format="value(connectionName)"

# Check Cloud Run has Cloud SQL access
gcloud run services describe dosev3-saas --region us-central1 --format="value(spec.template.spec.containers[0].env)"
```

### Issue: Static files not loading

```powershell
# Collect static files locally
python manage.py collectstatic --settings=mysite.settings_production

# Or rebuild container with static files
gcloud builds submit --tag gcr.io/dosev3-saas/dosev3-app
```

## Production Checklist

- [ ] Set `DEBUG=False` in production
- [ ] Configure `ALLOWED_HOSTS` with actual domains
- [ ] Use Secret Manager for sensitive data
- [ ] Enable Cloud SQL backups
- [ ] Set up custom domain with SSL
- [ ] Configure monitoring and alerting
- [ ] Set up Cloud Armor (DDoS protection) if needed
- [ ] Configure Cloud CDN for static files
- [ ] Set resource limits (CPU, memory, max instances)
- [ ] Enable Cloud SQL high availability (for production)
- [ ] Set up regular database backups
- [ ] Configure error reporting (Sentry, Cloud Error Reporting)

## Upgrading Deployment

```powershell
# Build new image
gcloud builds submit --tag gcr.io/dosev3-saas/dosev3-app

# Deploy with zero downtime
gcloud run deploy dosev3-saas `
    --image gcr.io/dosev3-saas/dosev3-app `
    --region us-central1

# Rollback if needed
gcloud run services update-traffic dosev3-saas --to-revisions PREVIOUS_REVISION=100 --region us-central1
```

## Alternative: App Engine Deployment

If you prefer App Engine Standard:

```powershell
# Create app.yaml
# Deploy
gcloud app deploy
```

See `app.yaml.example` for configuration.

## Support Resources

- **GCP Documentation**: https://cloud.google.com/run/docs
- **Cloud SQL Docs**: https://cloud.google.com/sql/docs
- **Django on GCP**: https://cloud.google.com/python/django
- **Cost Calculator**: https://cloud.google.com/products/calculator

## Next Steps

1. Complete Step 1-5 above
2. Test deployment at `https://dosev3-saas-xxx.run.app`
3. Set up custom domain
4. Configure monitoring
5. Enable continuous deployment
6. Set up production database backups
7. Configure email service (SendGrid, Mailgun)
8. Set up Celery with Cloud Tasks or Cloud Pub/Sub

---

**Questions or Issues?**
- Check Cloud Run logs
- Review Cloud Build history
- Verify environment variables
- Test database connectivity

**Estimated First Deployment Time:** 30-45 minutes
**Estimated Monthly Cost (Low Traffic):** $8-16
**Auto-scaling:** 0-10 instances (configurable)
