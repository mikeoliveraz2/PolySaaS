# Multi-Application GCP Deployment Architecture

**Date:** November 5, 2025
**Project:** DoseV3MasterSaaS + 4-6 Open Source Multi-Tenant Applications

---

## Q3: Deploying Multiple Applications Alongside Dose

**Question:** I plan on deploying 4-6 open source multi-tenant applications alongside Dose, both for our subscribers but also for demo. Any suggestions?

**Answer:**

Excellent plan! Here's a comprehensive architecture recommendation for deploying multiple multi-tenant apps on GCP.

---

## 🏗️ Recommended Architecture

### Option 1: **Unified Platform with Passthrough** (RECOMMENDED for Dose)

Based on your existing passthrough implementation (OsTicket, Gmail), extend this pattern:

```
┌─────────────────────────────────────────────────────────────┐
│  Single Domain: app.dosesaas.com                            │
└────────────────┬────────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────────┐
│  Dose Landing Page (Cloud Run - Main App)                   │
│  ┌────────────────────────────────────────────────────┐     │
│  │  Navigation Bar (Passthrough Links):               │     │
│  │  - Gmail                  → /admin/gmail/          │     │
│  │  - OsTicket              → /admin/osticket/        │     │
│  │  - Odoo ERP              → /admin/odoo/            │     │
│  │  - Mautic Marketing      → /admin/mautic/          │     │
│  │  - NextCloud Files       → /admin/nextcloud/       │     │
│  │  - Matomo Analytics      → /admin/matomo/          │     │
│  │  - Rocket.Chat           → /admin/rocketchat/      │     │
│  └────────────────────────────────────────────────────┘     │
└────────────────┬────────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────────┐
│  External Passthrough Middleware                             │
│  Routes requests to appropriate Cloud Run services           │
└────────────────┬────────────────────────────────────────────┘
                 │
        ┌────────┴────────┬──────────┬──────────┬─────────┐
        ▼                 ▼          ▼          ▼         ▼
    ┌────────┐      ┌─────────┐ ┌─────────┐ ┌──────┐ ┌──────┐
    │OsTicket│      │  Odoo   │ │ Mautic  │ │NextC │ │Matomo│
    │Cloud   │      │ Cloud   │ │ Cloud   │ │Cloud │ │Cloud │
    │Run     │      │ Run     │ │ Run     │ │Run   │ │Run   │
    └────────┘      └─────────┘ └─────────┘ └──────┘ └──────┘
```

**Pros:**
- ✅ Single login for all apps (Dose handles auth)
- ✅ Unified UI/UX (your landing page)
- ✅ Easy tenant switching
- ✅ Consistent branding
- ✅ Single domain/SSL cert
- ✅ Centralized billing (Stripe in Dose)

**Cons:**
- ❌ More complex middleware
- ❌ All apps must support proxy/passthrough
- ❌ Dose becomes single point of failure

---

### Option 2: **Microservices with Subdomains**

Each app gets its own subdomain and Cloud Run service:

```
┌──────────────────────────────────────────────────────────┐
│  Main Platform                                            │
│  https://app.dosesaas.com         (Dose Django)          │
│  https://osticket.dosesaas.com    (OsTicket)             │
│  https://odoo.dosesaas.com        (Odoo ERP)             │
│  https://mautic.dosesaas.com      (Mautic Marketing)     │
│  https://nextcloud.dosesaas.com   (NextCloud Files)      │
│  https://matomo.dosesaas.com      (Matomo Analytics)     │
│  https://chat.dosesaas.com        (Rocket.Chat)          │
└──────────────────────────────────────────────────────────┘
         │              │              │              │
         ▼              ▼              ▼              ▼
    ┌────────┐    ┌─────────┐    ┌────────┐    ┌────────┐
    │Dose    │    │OsTicket │    │Odoo    │    │Mautic  │
    │Cloud   │    │Cloud    │    │Cloud   │    │Cloud   │
    │Run     │    │Run      │    │Run     │    │Run     │
    └────────┘    └─────────┘    └────────┘    └────────┘
         │              │              │              │
         └──────────────┴──────────────┴──────────────┘
                        │
                        ▼
            ┌────────────────────────┐
            │  Shared Cloud SQL      │
            │  (Multi-schema/DB)     │
            └────────────────────────┘
```

**Pros:**
- ✅ Apps are independent (one fails, others continue)
- ✅ Easier to scale individually
- ✅ Standard deployments (no custom middleware)
- ✅ Simpler to debug
- ✅ Can use different tech stacks

**Cons:**
- ❌ Multiple domains (more SSL certs - though free)
- ❌ User switches between apps (different UIs)
- ❌ Need SSO for unified login
- ❌ More Cloud Run services (more cost)

---

### Option 3: **Hybrid Approach** (BEST FOR YOUR USE CASE)

Combine both: Embedded apps via passthrough + standalone for heavy users

```
┌─────────────────────────────────────────────────────────┐
│  app.dosesaas.com (Main Dose App)                       │
│  ┌────────────────────────────────────────────────┐     │
│  │  Light Users: Passthrough (embedded)           │     │
│  │  - OsTicket     → /admin/osticket/             │     │
│  │  - Odoo Lite    → /admin/odoo/                 │     │
│  │  - Analytics    → /admin/matomo/               │     │
│  └────────────────────────────────────────────────┘     │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│  Heavy Users: Direct Access (standalone)                │
│  - odoo.dosesaas.com      (full Odoo experience)        │
│  - chat.dosesaas.com      (full Rocket.Chat)            │
│  - nextcloud.dosesaas.com (full file management)        │
└─────────────────────────────────────────────────────────┘
```

---

## 📋 Recommended Open Source Apps for Multi-Tenant SaaS

### Category: Customer Support
1. **OsTicket** ✅ (Already integrated!)
   - Support tickets
   - Customer service
   - Help desk

2. **Chatwoot**
   - Live chat
   - Customer messaging
   - Multi-channel support

### Category: CRM & Marketing
3. **Mautic**
   - Marketing automation
   - Email campaigns
   - Lead tracking

4. **SuiteCRM**
   - Customer relationship management
   - Sales pipeline
   - Contact management

### Category: Business Operations
5. **Odoo**
   - Full ERP system
   - Inventory, invoicing, HR
   - Project management

6. **Invoice Ninja**
   - Invoicing & billing
   - Time tracking
   - Client portal

### Category: Collaboration
7. **NextCloud**
   - File storage & sharing
   - Calendar & contacts
   - Office suite

8. **Rocket.Chat**
   - Team messaging
   - Video calls
   - Integrations

### Category: Analytics
9. **Matomo**
   - Web analytics (Google Analytics alternative)
   - Privacy-focused
   - Self-hosted

10. **Metabase**
    - Business intelligence
    - Data visualization
    - Custom dashboards

---

## 🚀 GCP Deployment Strategy

### Architecture Components

```yaml
GCP Project: dosev3-production
├── Cloud Run Services
│   ├── dosev3-main          (Your Django app)
│   ├── osticket             (Support tickets)
│   ├── odoo                 (ERP)
│   ├── mautic               (Marketing)
│   ├── nextcloud            (Files)
│   ├── rocketchat           (Chat)
│   └── matomo               (Analytics)
│
├── Cloud SQL Instances
│   ├── dose-postgres        (Main Dose DB)
│   ├── apps-postgres        (Shared DB for OSS apps)
│   └── (or separate DBs per app)
│
├── Cloud Storage Buckets
│   ├── dosev3-static        (Static files)
│   ├── dosev3-media         (User uploads)
│   ├── nextcloud-files      (NextCloud storage)
│   └── backups              (Database backups)
│
├── Cloud Load Balancer
│   ├── app.dosesaas.com     → dosev3-main
│   ├── osticket.*           → osticket
│   ├── odoo.*               → odoo
│   └── *.dosesaas.com       → route to services
│
└── Cloud Memorystore (Redis)
    └── Shared cache for all apps
```

---

## 💰 Cost Estimation (6 Applications)

### Monthly Costs (Low-Medium Traffic)

**Cloud Run (6 services):**
- Dose Main: $5-10/month
- OsTicket: $3-5/month
- 4 Other apps: $2-5/month each
- **Subtotal: $20-40/month**

**Cloud SQL:**
- Option A: 1 shared instance (db-n1-standard-1): $50/month
- Option B: 2 instances (1 for Dose, 1 shared): $70/month
- **Subtotal: $50-70/month**

**Cloud Storage:**
- Static files: $1-5/month
- User files: $5-20/month (depending on usage)
- **Subtotal: $6-25/month**

**Cloud Load Balancer:**
- $18/month + $0.008/GB
- **Subtotal: $20-30/month**

**Redis (Memorystore - optional):**
- Basic tier: $30/month
- **Subtotal: $30/month (optional)**

**Total Estimated Cost: $96-165/month**

With proper optimization and free tiers: **~$80-120/month**

---

## 🔧 Implementation Steps

### Phase 1: Infrastructure Setup (Week 1)

```powershell
# 1. Create shared Cloud SQL instance for OSS apps
gcloud sql instances create apps-postgres `
    --database-version=POSTGRES_15 `
    --tier=db-n1-standard-1 `
    --region=us-central1

# 2. Create databases for each app
gcloud sql databases create osticket_db --instance=apps-postgres
gcloud sql databases create odoo_db --instance=apps-postgres
gcloud sql databases create mautic_db --instance=apps-postgres
gcloud sql databases create nextcloud_db --instance=apps-postgres
gcloud sql databases create rocketchat_db --instance=apps-postgres
gcloud sql databases create matomo_db --instance=apps-postgres

# 3. Create storage buckets
gsutil mb -l us-central1 gs://dosev3-nextcloud-files/
gsutil mb -l us-central1 gs://dosev3-app-backups/
```

### Phase 2: Deploy First App (OsTicket) - Already Done! ✅

Your current passthrough implementation is perfect!

### Phase 3: Deploy Additional Apps (Weeks 2-4)

For each app, create:

**1. Dockerfile**
```dockerfile
# Example: Odoo Dockerfile
FROM odoo:16.0
COPY ./config/odoo.conf /etc/odoo/
```

**2. Deploy to Cloud Run**
```powershell
# Build and deploy Odoo
gcloud builds submit --tag gcr.io/dosev3-saas/odoo
gcloud run deploy odoo `
    --image gcr.io/dosev3-saas/odoo `
    --region us-central1 `
    --set-cloudsql-instances PROJECT_ID:us-central1:apps-postgres `
    --set-env-vars "DB_HOST=/cloudsql/...,DB_NAME=odoo_db"
```

**3. Add to Dose PassThroughEndpoint**
```python
PassThroughEndpoint.objects.create(
    name='Odoo ERP',
    trigger_path='/admin/odoo/',
    endpoint_url='https://odoo-xyz.run.app',
    is_enabled=True
)
```

**4. Add to Landing Page Navigation**
```html
<a href="javascript:void(0);"
   onclick="loadPassthroughContent('/admin/odoo/', 'Odoo ERP'); return false;">
    <i class="fas fa-briefcase"></i>
    <span class="sidebar-text">Odoo ERP</span>
</a>
```

---

## 🎯 Multi-Tenancy Strategy

### Approach 1: Shared Database with Schema per Tenant
```sql
-- PostgreSQL schemas for isolation
CREATE SCHEMA tenant_acme;
CREATE SCHEMA tenant_globex;
CREATE SCHEMA tenant_initech;

-- Each tenant's data in separate schema
SET search_path TO tenant_acme;
```

### Approach 2: Database per Tenant
```python
# Dynamic database routing based on tenant
DATABASES = {
    'tenant_acme': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'acme_db',
    },
    'tenant_globex': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'globex_db',
    }
}
```

### Approach 3: Hybrid (Recommended)
- **Shared apps** (analytics, chat): Schema-based tenancy
- **Isolated apps** (ERP, files): Database per tenant for premium customers

---

## 🔐 Security & Isolation

```python
# Tenant middleware for all apps
class UnifiedTenantMiddleware:
    def process_request(self, request):
        # Get tenant from Dose session
        tenant = request.session.get('tenant_id')

        # Set tenant context for all downstream apps
        request.tenant = Tenant.objects.get(id=tenant)

        # Each app uses this tenant for data isolation
        connection.set_schema(request.tenant.schema_name)
```

---

## 📊 Demo Environment Strategy

### Option A: Separate Demo Project
```powershell
# Create demo GCP project
gcloud projects create dosev3-demo

# Deploy same stack with:
# - Pre-populated data
# - Auto-reset daily
# - Limited resources (smaller instances)
```

### Option B: Demo Tenants in Production
```python
# Mark tenants as demo
class Tenant(models.Model):
    is_demo = models.BooleanField(default=False)
    reset_schedule = models.CharField()  # 'daily', 'weekly'

# Celery task to reset demo data
@app.task
def reset_demo_tenants():
    for tenant in Tenant.objects.filter(is_demo=True):
        # Reset to baseline data
        restore_demo_snapshot(tenant)
```

**Recommended: Option B** (demo tenants in production)
- Lower cost (same infrastructure)
- Same performance as production
- Easy to convert demo → paid

---

## 🎁 Suggested App Packages for Subscribers

### Starter Package ($29/month)
- Dose Core
- OsTicket (Support)
- Basic Analytics (Matomo)

### Business Package ($99/month)
- Everything in Starter
- Odoo ERP (Lite)
- Mautic Marketing
- NextCloud (50GB)

### Enterprise Package ($299/month)
- Everything in Business
- Full Odoo ERP
- Rocket.Chat
- NextCloud (Unlimited)
- Dedicated resources
- Priority support

---

## 🚦 Recommended Rollout Plan

**Month 1: Foundation**
- ✅ Dose deployed
- ✅ OsTicket (already done!)
- ✅ Basic multi-tenancy

**Month 2: Core Apps**
- Deploy Mautic (marketing)
- Deploy Matomo (analytics)
- Test passthrough integration

**Month 3: Collaboration**
- Deploy NextCloud (files)
- Deploy Rocket.Chat (messaging)
- SSO integration

**Month 4: Business Suite**
- Deploy Odoo (ERP)
- Premium tier launch
- Demo environment

**Month 5: Polish**
- Performance optimization
- Auto-scaling tuning
- Monitoring dashboards

**Month 6: Launch**
- Public beta
- Marketing campaign
- Customer onboarding

---

## 📝 Next Steps

1. **Choose your architecture:** Hybrid approach recommended
2. **Select 4-6 apps:** Based on your target market
3. **Deploy app #2:** Start with Mautic or Matomo (easier than Odoo)
4. **Test passthrough:** Ensure same UX as OsTicket
5. **Set up demo tenant:** With sample data
6. **Document:** API integration, user guides
7. **Plan pricing:** Package tiers based on app access

---

## 🤔 Questions to Consider

1. **Target audience?** (SMB, enterprise, specific industry?)
2. **Self-service or managed?** (Users deploy apps themselves or you provision?)
3. **Data residency?** (Multi-region deployment needed?)
4. **Customization?** (Users can modify apps or locked down?)
5. **Integration level?** (Apps work together or just bundled?)

---

**Want me to help with:**
- [ ] Dockerfile for specific app (Odoo, Mautic, etc.)?
- [ ] Multi-tenant database schema design?
- [ ] Demo environment setup scripts?
- [ ] Pricing calculator for different tiers?
- [ ] SSO integration guide?

Let me know which app you want to deploy next! 🚀
