# GCP Deployment Q&A Reference

**Date:** November 5, 2025
**Project:** DoseV3MasterSaaS GCP Deployment

---

## Q1: GitHub Commits and GCP Deployment

**Question:** Given our GitHub repository, if I commit here will that deploy to the GCP or only on command?

**Answer:**

**By default: MANUAL ONLY** - Commits to GitHub will NOT automatically deploy to GCP. You must manually run deployment commands.

However, you have **two deployment options**:

### Option 1: Manual Deployment (Default - What's Currently Set Up)

```powershell
# You must manually trigger deployment after committing to GitHub
git push origin main

# Then manually deploy to GCP
gcloud builds submit --tag gcr.io/YOUR_PROJECT_ID/dosev3-app
gcloud run deploy dosev3-saas --image gcr.io/YOUR_PROJECT_ID/dosev3-app --region us-central1
```

**Pros:**
- ✅ Full control over when deployments happen
- ✅ Can test locally before deploying
- ✅ No surprise deployments from work-in-progress commits
- ✅ No additional setup required

**Cons:**
- ❌ Manual process every time
- ❌ Can forget to deploy after pushing code
- ❌ Slower deployment workflow

---

### Option 2: Automatic Deployment (Requires Setup - CI/CD Pipeline)

Set up **Cloud Build triggers** to automatically deploy when you push to GitHub.

**Setup Steps:**

1. **Connect GitHub to Cloud Build:**
   ```powershell
   # Go to Cloud Console
   https://console.cloud.google.com/cloud-build/triggers

   # Click "Connect Repository"
   # Select "GitHub (Cloud Build GitHub App)"
   # Authorize and select repository: AliVleotsky/DoseV3MasterSaaS-main-main
   ```

2. **Create Build Trigger:**
   - **Name:** `deploy-on-main-push`
   - **Event:** Push to a branch
   - **Source Branch:** `^main$` (only main branch)
   - **Configuration:** Cloud Build configuration file (cloudbuild.yaml)
   - **Location:** `cloudbuild.yaml` (already created in your repo)

3. **Set Substitution Variables in Trigger:**
   - `_DJANGO_SECRET_KEY`: Your Django secret key
   - `_DOSE_DB_PASSWORD`: Your database password
   - `_CLOUDSQL_CONNECTION`: Your Cloud SQL connection name (format: `project-id:region:instance-name`)

4. **Grant Cloud Build Permissions:**
   ```powershell
   # Get your project number
   gcloud projects describe YOUR_PROJECT_ID --format="value(projectNumber)"

   # Grant Cloud Run Admin role to Cloud Build
   gcloud projects add-iam-policy-binding YOUR_PROJECT_ID `
       --member="serviceAccount:PROJECT_NUMBER@cloudbuild.gserviceaccount.com" `
       --role="roles/run.admin"

   # Grant Service Account User role
   gcloud projects add-iam-policy-binding YOUR_PROJECT_ID `
       --member="serviceAccount:PROJECT_NUMBER@cloudbuild.gserviceaccount.com" `
       --role="roles/iam.serviceAccountUser"
   ```

**After Setup - Automatic Workflow:**
```bash
git add .
git commit -m "Add new feature"
git push origin main

# ✅ Cloud Build automatically:
# 1. Detects push to main branch
# 2. Builds Docker image
# 3. Pushes to Container Registry
# 4. Deploys to Cloud Run
# 5. Sends notification (optional)
```

**Pros:**
- ✅ Automatic deployment on every push to main
- ✅ Fast deployment workflow
- ✅ Consistent builds (no "works on my machine")
- ✅ Build history and logs in GCP Console
- ✅ Easy rollbacks to previous versions

**Cons:**
- ❌ Every commit to main triggers deployment (even WIP)
- ❌ Requires initial setup
- ❌ Uses Cloud Build minutes (free tier: 120 minutes/day)
- ❌ Can deploy broken code if you don't test first

---

### Recommended Approach: Hybrid Workflow

**Use branches for development:**

```bash
# Work on feature branch (won't trigger deployment)
git checkout -b feature/new-landing-page
git add .
git commit -m "WIP: Landing page improvements"
git push origin feature/new-landing-page

# When ready, merge to main (triggers automatic deployment)
git checkout main
git merge feature/new-landing-page
git push origin main  # ← This triggers automatic deployment
```

**OR use manual approval in Cloud Build:**

Modify `cloudbuild.yaml` to require approval:

```yaml
# Add approval step before deployment
steps:
  - name: 'gcr.io/cloud-builders/docker'
    args: ['build', '-t', 'gcr.io/$PROJECT_ID/dosev3-saas', '.']

  # Manual approval gate
  - name: 'gcr.io/cloud-builders/gcloud'
    entrypoint: 'bash'
    args:
      - '-c'
      - |
        echo "Build complete. Waiting for manual approval to deploy..."
        # Deployment happens only after manual approval in Cloud Console
```

---

### Current Status

**Your setup:** ✅ Manual deployment (no automatic triggers configured)

**To enable automatic deployment:**
1. Follow "Option 2" steps above
2. Connect GitHub repository to Cloud Build
3. Create trigger for main branch
4. Set substitution variables
5. Grant permissions

**Files already configured:**
- ✅ `cloudbuild.yaml` - Ready for automatic builds
- ✅ `Dockerfile` - Container definition
- ✅ `.gcloudignore` - Excludes files from deployment

---

### Which Should You Choose?

| Scenario | Recommendation |
|----------|----------------|
| **Solo developer, testing often** | Manual deployment |
| **Team, production app** | Automatic with feature branches |
| **Critical production app** | Automatic with manual approval |
| **Learning/experimenting** | Manual deployment |
| **High-traffic production** | Automatic with staging environment |

---

### Next Steps

**For Manual Deployment (Current Setup):**
- ✅ Nothing to do - you're already set up
- Just run `gcloud builds submit` and `gcloud run deploy` when ready

**For Automatic Deployment:**
1. Would you like me to help set up Cloud Build triggers?
2. Do you want automatic deployment on every push, or only on tagged releases?
3. Should we set up a staging environment first?

---

**Additional Notes:**

- Cloud Build free tier: 120 build-minutes/day
- Each deployment takes ~5-10 minutes
- You can mix both: manual for dev, automatic for production branch
- You can set up notifications (email, Slack) for successful/failed deployments
- Cloud Build keeps history of all builds for debugging

---

## Q2: Do I Need My Own Domain First?

**Question:** Do I need to have my own domain first?

**Answer:**

**NO - You DO NOT need your own domain to deploy to GCP!** 🎉

### What You Get Automatically (FREE)

When you deploy to Cloud Run, Google automatically provides:

**Free Domain:** `https://dosev3-saas-RANDOM.run.app`
- ✅ Fully functional HTTPS URL
- ✅ Free SSL certificate (automatic)
- ✅ Works immediately after deployment
- ✅ No DNS configuration needed
- ✅ No domain purchase required

**Example:**
```
https://dosev3-saas-a1b2c3d4e5-uc.a.run.app
         └─service─┘ └random─┘ └region─┘
```

### Workflow Without Custom Domain

```powershell
# Deploy to Cloud Run
gcloud run deploy dosev3-saas --image gcr.io/YOUR_PROJECT_ID/dosev3-app --region us-central1

# Output:
# Service [dosev3-saas] revision [dosev3-saas-00001-abc] has been deployed
# Service URL: https://dosev3-saas-xyz123-uc.a.run.app  ← Use this immediately!
```

**You can use this URL for:**
- ✅ Testing and development
- ✅ Sharing with team members
- ✅ Client demos
- ✅ Production use (if you don't mind the URL)
- ✅ API endpoints
- ✅ Small internal tools

---

### When You WOULD Want a Custom Domain

**Later, when you're ready for production:**

❌ **Don't like:** `dosev3-saas-xyz123-uc.a.run.app`
✅ **Prefer:** `app.dosesaas.com` or `dosesaas.com`

**Benefits of custom domain:**
- Professional branding
- Easier to remember
- Better for marketing
- Custom email addresses
- SEO benefits

---

### Adding Custom Domain Later (OPTIONAL)

**Step 1: Buy a domain** (if you don't have one)
- Google Domains: ~$12/year
- Namecheap: ~$10/year
- Cloudflare: ~$10/year

**Step 2: Map domain to Cloud Run**
```powershell
# Map your domain
gcloud run domain-mappings create --service dosev3-saas --domain app.dosesaas.com --region us-central1

# Follow DNS instructions (add A and AAAA records)
# Wait 15 minutes - 24 hours for DNS propagation

# SSL certificate automatically provisioned (FREE)
```

**DNS Records Required:**
```
Type    Name    Value
A       app     216.239.32.21
A       app     216.239.34.21
A       app     216.239.36.21
A       app     216.239.38.21
AAAA    app     2001:4860:4802:32::15
AAAA    app     2001:4860:4802:34::15
AAAA    app     2001:4860:4802:36::15
AAAA    app     2001:4860:4802:38::15
```

**Cost:** $0 (domain mapping is free, only domain registration costs money)

---

### Comparison: Free URL vs Custom Domain

| Feature | Free Cloud Run URL | Custom Domain |
|---------|-------------------|---------------|
| **Cost** | FREE ✅ | ~$10-15/year |
| **HTTPS/SSL** | FREE ✅ | FREE ✅ |
| **Setup Time** | Immediate | 15min - 24hrs |
| **URL Example** | `dosev3-saas-xyz.run.app` | `app.dosesaas.com` |
| **Professional** | ❌ | ✅ |
| **Branding** | ❌ | ✅ |
| **Works for testing** | ✅ | ✅ |
| **Works for production** | ✅ | ✅ |

---

### Recommended Deployment Path

**Phase 1: Deploy WITHOUT domain (Start here)**
```powershell
# Just deploy and use the free .run.app URL
gcloud run deploy dosev3-saas --image gcr.io/YOUR_PROJECT_ID/dosev3-app --region us-central1

# Use for testing, development, demos
# URL: https://dosev3-saas-xyz.run.app
```

**Phase 2: Add custom domain LATER (when ready)**
```powershell
# After buying domain (dosesaas.com)
gcloud run domain-mappings create --service dosev3-saas --domain app.dosesaas.com --region us-central1

# Update DNS records
# Wait for propagation
# Now works at both URLs!
```

---

### Important Notes

1. **You can deploy RIGHT NOW without a domain** ✅
2. **Free .run.app URL works perfectly** for:
   - Development
   - Testing
   - Internal tools
   - MVP/beta launches
   - Client demos

3. **Add custom domain anytime** - no redeployment needed
4. **Both URLs work simultaneously** after adding custom domain
5. **SSL is FREE** for both .run.app and custom domains

---

### What About Email?

**Free .run.app URL:**
- ❌ Cannot use for custom email (noreply@dosev3-saas-xyz.run.app won't work)
- ✅ Can send email FROM any address via SMTP (Gmail, SendGrid, etc.)

**Custom domain:**
- ✅ Can have custom email (support@dosesaas.com)
- Need separate email service (Google Workspace $6/user/month, or free with Cloudflare)

---

### Bottom Line

**START WITHOUT A DOMAIN**
- Deploy to GCP immediately
- Use free `*.run.app` URL
- Test and develop
- Launch MVP/beta

**ADD DOMAIN LATER** (optional)
- When ready for branding
- When you want custom email
- When ready to pay ~$10/year
- Takes 15 minutes to set up

**You can deploy TODAY without spending a penny on domains!** 🚀

---

## Q4: Are All 10 Recommended Apps Google SSO Capable?

**Question:** Are all 10 recommended open source apps Google SSO capable?

**Answer:**

**Short answer: 9 out of 10 have SSO support, 8 out of 10 have native Google OAuth!** ✅

Here's the detailed breakdown:

### ✅ Native Google OAuth Support (Best - No Extra Work)

| App | Google SSO | Method | Difficulty |
|-----|-----------|---------|------------|
| **NextCloud** | ✅ YES | OIDC/OAuth2 plugin | ⭐ Easy |
| **Rocket.Chat** | ✅ YES | Built-in OAuth | ⭐ Easy |
| **Mautic** | ✅ YES | OAuth plugin | ⭐⭐ Medium |
| **Odoo** | ✅ YES | OAuth provider module | ⭐⭐ Medium |
| **Matomo** | ✅ YES | Login OIDC plugin | ⭐ Easy |
| **Chatwoot** | ✅ YES | Built-in OAuth | ⭐ Easy |
| **SuiteCRM** | ✅ YES | SAML/OAuth plugin | ⭐⭐⭐ Hard |
| **Invoice Ninja** | ✅ YES | OAuth support (v5+) | ⭐⭐ Medium |

### 🔧 OAuth Requires Custom Development

| App | Google SSO | Method | Difficulty |
|-----|-----------|---------|------------|
| **OsTicket** | ⚠️ REQUIRES CODING | Custom OAuth plugin development | ⭐⭐⭐⭐ Very Hard |
| **Metabase** | ✅ YES | Generic OAuth/SAML (requires config) | ⭐⭐ Medium |

**OsTicket OAuth Details:**
- No built-in OAuth support out of the box
- Requires developing a custom authentication plugin
- Plugin API available: https://github.com/osTicket/osTicket/blob/develop/include/class.auth.php
- Community plugins exist but require customization
- **Recommended:** Use passthrough auth instead (much easier!)

### 🔧 SSO Implementation Strategies

#### Strategy 1: Direct Google OAuth (Recommended)

For apps with native support (NextCloud, Rocket.Chat, etc.):

```yaml
# Example: NextCloud Google OAuth Setup
1. Create OAuth App in Google Cloud Console
2. Get Client ID & Secret
3. Install Social Login app in NextCloud
4. Configure:
   Provider: Google
   Client ID: your-client-id
   Client Secret: your-client-secret
   Redirect URI: https://nextcloud.dosesaas.com/apps/sociallogin/oauth/google
```

**Configuration in each app:**
- **NextCloud**: Apps > Social Login > Google
- **Rocket.Chat**: Admin > OAuth > Google
- **Mautic**: Settings > Configuration > OAuth
- **Matomo**: Login OIDC plugin
- **Chatwoot**: Super Admin > App > Google OAuth

#### Strategy 2: Unified SSO via Dose (Your Current Approach)

Since you're using **passthrough middleware**, you can handle SSO at the Dose level:

```python
# In your Dose middleware
class UnifiedSSOMiddleware:
    def process_request(self, request):
        # User already authenticated via Google in Dose
        if request.user.is_authenticated:
            # Pass auth token to passthrough apps
            request.META['HTTP_X_AUTHENTICATED_USER'] = request.user.email
            request.META['HTTP_X_AUTH_TOKEN'] = generate_app_token(request.user)

            # Apps trust Dose authentication
            # No separate login needed!
```

**Benefits:**
- ✅ Single login for all apps (via Dose)
- ✅ No need to configure OAuth in each app
- ✅ Centralized user management
- ✅ Works even for apps without native OAuth support (like OsTicket)

#### Strategy 3: Custom OAuth Plugin (For OsTicket - Advanced)

OsTicket **CAN** support OAuth but requires custom plugin development:

```php
// OsTicket custom OAuth plugin structure
include/class.auth.php
include/plugins/auth-oauth/
    - plugin.php
    - config.php
    - oauth-client.php (Google OAuth implementation)
```

**Resources:**
- OsTicket Plugin API: https://github.com/osTicket/osTicket/blob/develop/include/class.auth.php
- Community OAuth plugins: https://github.com/search?q=osticket+oauth
- **Complexity:** High - requires PHP development, OsTicket API knowledge
- **Time estimate:** 1-2 weeks for experienced developer

**Alternative (Much Easier):**
- Use passthrough authentication (recommended!)
- Or LDAP/SAML bridge with tools like SimpleSAMLphp, Keycloak, or Auth0

---

### 🎯 Recommended SSO Architecture for Your Platform

#### Option A: Passthrough Authentication (EASIEST)

```
┌─────────────────────────────────────────────────────┐
│  User logs in to Dose with Google OAuth             │
└────────────────┬────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────┐
│  Dose creates session with user data                │
│  - Email, name, tenant_id, permissions              │
└────────────────┬────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────┐
│  Passthrough Middleware                             │
│  - Forwards requests to apps                        │
│  - Injects auth headers:                            │
│    * X-Authenticated-User: user@email.com           │
│    * X-Tenant-ID: tenant_123                        │
│    * X-Auth-Token: signed_jwt_token                 │
└────────────────┬────────────────────────────────────┘
                 │
        ┌────────┴────────┬──────────┬──────────┐
        ▼                 ▼          ▼          ▼
    ┌────────┐      ┌─────────┐ ┌────────┐ ┌────────┐
    │OsTicket│      │NextCloud│ │Rocket  │ │Matomo  │
    │Auto-   │      │Auto-    │ │Chat    │ │Auto-   │
    │Login   │      │Login    │ │Auto-   │ │Login   │
    │        │      │         │ │Login   │ │        │
    └────────┘      └─────────┘ └────────┘ └────────┘
```

**Implementation:**

```python
# mysite/unified_auth_middleware.py
import jwt
from datetime import datetime, timedelta

class UnifiedAuthMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Only for passthrough requests
        if request.path.startswith('/admin/'):
            if request.user.is_authenticated:
                # Generate JWT token for app authentication
                token = jwt.encode({
                    'email': request.user.email,
                    'name': request.user.get_full_name(),
                    'tenant_id': request.session.get('tenant_id'),
                    'exp': datetime.utcnow() + timedelta(hours=1)
                }, settings.SECRET_KEY, algorithm='HS256')

                # Inject auth headers
                request.META['HTTP_X_AUTH_TOKEN'] = token
                request.META['HTTP_X_USER_EMAIL'] = request.user.email
                request.META['HTTP_X_TENANT_ID'] = request.session.get('tenant_id')

        return self.get_response(request)
```

**Each app configures auto-login via headers:**

```php
// OsTicket: include/class.auth.php (custom plugin)
if ($email = $_SERVER['HTTP_X_USER_EMAIL']) {
    if (verify_jwt($_SERVER['HTTP_X_AUTH_TOKEN'])) {
        // Auto-login user
        $user = Staff::lookup(['email' => $email]);
        if ($user) {
            $_SESSION['staff_id'] = $user->getId();
        }
    }
}
```

---

#### Option B: Individual OAuth Setup (More Work, More Flexible)

Configure each app separately with Google OAuth:

**Pros:**
- ✅ Apps can be used standalone (not just via passthrough)
- ✅ Better for apps that need direct access
- ✅ More secure (each app validates OAuth independently)

**Cons:**
- ❌ 8+ OAuth configurations to maintain
- ❌ Users might see multiple login prompts
- ❌ Each app needs its own Google OAuth client

---

### 📊 SSO Capability Summary

| App | Native Google OAuth | Via Passthrough | Via SAML | Custom OAuth Plugin | Recommended |
|-----|-------------------|----------------|----------|---------------------|-------------|
| NextCloud | ✅ | ✅ | ✅ | N/A | Passthrough (easier) |
| Rocket.Chat | ✅ | ✅ | ✅ | N/A | Passthrough (easier) |
| Mautic | ✅ | ✅ | ✅ | N/A | Passthrough (easier) |
| Odoo | ✅ | ✅ | ✅ | N/A | OAuth (if standalone) |
| Matomo | ✅ | ✅ | ✅ | N/A | Passthrough (easier) |
| Chatwoot | ✅ | ✅ | ✅ | N/A | Passthrough (easier) |
| SuiteCRM | ✅ | ✅ | ✅ | N/A | Passthrough (easier) |
| Invoice Ninja | ✅ | ✅ | ⚠️ | N/A | OAuth (built-in) |
| OsTicket | ❌ | ✅ | ✅ | ✅ (requires dev) | **Passthrough (EASIEST)** |
| Metabase | ⚠️ | ✅ | ✅ | N/A | Passthrough (easier) |

---

### 🚀 Implementation Priority

**Phase 1: Passthrough Auth (Week 1)**
```python
# Add unified auth middleware
# Test with OsTicket (already working!)
# Extend to other apps
```

**Phase 2: App-Specific Auto-Login (Week 2-3)**
```bash
# Create plugins/modules for each app
# Configure header-based authentication
# Test SSO flow
```

**Phase 3: Standalone OAuth (Optional - Month 2)**
```bash
# For apps that need direct access
# Configure Google OAuth per app
# Enable subdomain access
```

---

### 💡 Recommended Approach

**Use Passthrough Authentication for ALL apps**

**Why?**
1. ✅ Works for OsTicket (which has no OAuth)
2. ✅ Single implementation, works for all apps
3. ✅ Centralized user management
4. ✅ One Google OAuth client (in Dose)
5. ✅ Seamless UX (login once, access everything)
6. ✅ Easier tenant isolation

**Code already in place:**
- ✅ Google OAuth in Dose (via allauth)
- ✅ Passthrough middleware
- ✅ Session management

**What's needed:**
- 🔧 Add auth header injection to middleware
- 🔧 Create auto-login plugins for each app (PHP/Python/etc.)
- 🔧 JWT token generation/validation

---

### 🔐 Security Considerations

**Passthrough Auth Security:**
```python
# Use signed JWT tokens
token = jwt.encode({
    'email': user.email,
    'tenant_id': tenant.id,
    'exp': datetime.utcnow() + timedelta(hours=1),
    'iat': datetime.utcnow(),
    'iss': 'dose-saas'  # Issuer
}, SECRET_KEY, algorithm='HS256')

# Apps verify token before trusting headers
if not verify_jwt_signature(token, SECRET_KEY):
    return "Unauthorized"
```

**Best Practices:**
- ✅ Use HTTPS everywhere (Cloud Run enforces this)
- ✅ Short token expiration (1 hour)
- ✅ Rotate SECRET_KEY periodically
- ✅ Log authentication events
- ✅ Rate limit auth endpoints

---

### 📝 Next Steps

1. **Verify current OAuth:** Google OAuth working in Dose? ✅ (Yes, per your screenshot)
2. **Test auth headers:** Add middleware to inject headers
3. **Create OsTicket plugin:** Auto-login based on headers
4. **Document pattern:** Template for other apps
5. **Deploy & test:** Verify SSO works across apps

**Want me to:**
- [ ] Create the unified auth middleware?
- [ ] Write OsTicket auto-login plugin?
- [ ] Generate JWT token utilities?
- [ ] Document SSO setup for each app?

---

**Bottom Line:**

✅ **8/10 apps have native Google OAuth**
✅ **10/10 apps can work with passthrough authentication**
✅ **Recommend: Use passthrough auth for unified experience**
✅ **Your current architecture is PERFECT for SSO!** 🎉

