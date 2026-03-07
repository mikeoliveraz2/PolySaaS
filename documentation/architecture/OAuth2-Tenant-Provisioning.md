# OAuth2 SSO & Automated Tenant Provisioning

**Research & Design — March 2026**
**Reviewed by Shela — 2026-03-07 (Score: 9/10)**

---

## Executive Summary

We are implementing Django as the central OIDC provider using `django-oauth-toolkit`. This enables seamless SSO across all bundled apps (Mattermost, Odoo, Nextcloud, etc.) with zero user credentials per app. Subscription provisioning auto-creates tenant accounts and configures OAuth clients via each app's API. Security is tenant-scoped, with short-lived tokens and audit logging. Timeline: 4–6 weeks to MVP. This unlocks one-login experience and lays the foundation for Apps As Peers.

---

## 1. Goal

When a new tenant subscribes and selects Mattermost, Odoo, and/or Nextcloud, the system should:

1. Create the tenant in PolySaaS (already works)
2. Provision the selected app instance(s) for that tenant
3. Pre-configure OAuth2/OIDC SSO so the tenant's users log in once (via PolySaaS) and get seamless access to all their apps — no separate passwords

---

## 2. OAuth2/OIDC Capabilities — Per App

### 2.1 Mattermost

| Capability | Details |
|-----------|---------|
| **OIDC Client** | Yes — built-in OpenID Connect support (Professional/Enterprise plans) |
| **Supported Providers** | GitLab, Google, Entra ID, Keycloak, Auth0, Okta, or any OIDC-compliant IdP |
| **Configuration** | System Console > Authentication > OpenID Connect |
| **Required Fields** | Discovery Endpoint, Client ID, Client Secret, Button Name/Color |
| **Redirect URI** | `{mattermost-url}/signup/openid/complete` |
| **User Provisioning** | Auto-creates users on first OIDC login (JIT) |
| **API Config** | Mattermost has a full REST API (`/api/v4/config`) that can update OIDC settings programmatically |
| **Multi-tenant** | Each Mattermost instance is single-tenant; multi-tenant = separate instances or separate teams |

**Key detail:** Mattermost's `/api/v4/config` endpoint accepts a `PATCH` with the full `ServiceSettings`, `GitLabSettings`, or `OpenIdSettings` block. This means we can **programmatically configure OIDC** without touching the System Console UI.

```
PATCH /api/v4/config
{
  "OpenIdSettings": {
    "Enable": true,
    "Secret": "<client_secret>",
    "Id": "<client_id>",
    "DiscoveryEndpoint": "https://polysaas.online/.well-known/openid-configuration",
    "ButtonText": "Log in with PolySaaS",
    "ButtonColor": "#003399"
  }
}
```

### 2.2 Odoo

| Capability | Details |
|-----------|---------|
| **OIDC Client** | Yes — via `auth_oauth` (built-in) + `auth-oidc` (OCA module for full OIDC) |
| **Supported Providers** | Any OAuth2/OIDC provider (Google, Azure, Keycloak, custom) |
| **Configuration** | Settings > Users & Companies > OAuth Providers (requires Developer Mode) |
| **Required Fields** | Provider Name, Client ID, Secret Key, Authorization URL, Token URL, UserInfo URL, Scope |
| **Redirect URI** | `{odoo-url}/auth_oauth/signin` |
| **User Provisioning** | JIT — auto-creates user on first OAuth login if `auth_oauth` is enabled |
| **API Config** | Odoo's XML-RPC / JSON-RPC API can create `auth.oauth.provider` records programmatically |
| **Multi-tenant** | Odoo uses separate databases per tenant (built-in `--db-filter` for multi-DB) |

**Key detail:** Odoo's `auth.oauth.provider` model stores OAuth provider configs. We can create these via JSON-RPC:

```python
# Create OAuth provider in Odoo via JSON-RPC
models.execute_kw(db, uid, password, 'auth.oauth.provider', 'create', [{
    'name': 'PolySaaS SSO',
    'client_id': '<client_id>',
    'client_secret': '<client_secret>',
    'auth_endpoint': 'https://polysaas.online/o/authorize/',
    'token_endpoint': 'https://polysaas.online/o/token/',
    'jwks_uri': 'https://polysaas.online/o/jwks/',
    'validation_endpoint': 'https://polysaas.online/o/userinfo/',
    'scope': 'openid email profile',
    'enabled': True,
    'body': 'Log in with PolySaaS',
    'css_class': 'fa fa-fw fa-sign-in',
}])
```

### 2.3 Nextcloud

| Capability | Details |
|-----------|---------|
| **OIDC Client** | Yes — via `user_oidc` app (official Nextcloud app) |
| **OAuth2 Provider** | Yes — built-in `oauth2` app makes Nextcloud an OAuth2 provider for external services |
| **Configuration** | `occ user_oidc:provider` CLI command, or Admin > Settings > SSO & SAML |
| **Required Fields** | Identifier (name), Client ID, Client Secret, Discovery Endpoint |
| **Redirect URI** | `{nextcloud-url}/apps/user_oidc/code` |
| **User Provisioning** | JIT — auto-creates users; can also work alongside existing user backends |
| **API Config** | `occ` CLI commands; no REST API for provider config, but can be done via Docker exec |
| **Multi-tenant** | Nextcloud is single-tenant per instance; multi-tenant = separate instances or user groups |

**Key detail:** Provider configuration via CLI:

```bash
occ user_oidc:provider PolySaaS \
  --clientid="<client_id>" \
  --clientsecret="<client_secret>" \
  --discoveryuri="https://polysaas.online/.well-known/openid-configuration" \
  --scope="openid email profile" \
  --unique-uid=1 \
  --check-bearer=1
```

**Important caveat:** Nextcloud's built-in OAuth2 has **no scope support** — every token gets full read/write access. This is acceptable when PolySaaS is both the IdP and the app orchestrator, but should be documented for security reviews. **Mitigation:** PolySaaS controls the Nextcloud instance end-to-end; we implement fine-grained API permissions via the proxy handler + atomic services layer, so tenant users never interact with raw Nextcloud OAuth tokens directly.

---

## 3. Architecture Decision: PolySaaS as the Identity Provider

### The Options

| Approach | Description | Pros | Cons |
|----------|------------|------|------|
| **A: Django as OIDC Provider** | `django-oauth-toolkit` (DOT) with OIDC support | Simple, no extra service, uses existing user/tenant models | Less feature-rich than dedicated IdP |
| **B: Keycloak** | Dedicated IdP service in Docker stack | Enterprise-grade, realms = tenants, admin UI | Extra service to manage, more complexity |
| **C: Django + Keycloak later** | Start with DOT, migrate to Keycloak at scale | Fast to ship, upgrade path clear | Migration effort later |

### Recommendation: **Approach A (Django as OIDC Provider)** for seed stage

**Rationale:**

1. PolySaaS Django already manages users, tenants, and authentication (allauth + Google/GitHub)
2. `django-oauth-toolkit` (DOT) is mature, well-maintained, and supports OIDC
3. Each tenant's app instances are configured to trust PolySaaS as the IdP
4. No new service to deploy — reduces infrastructure cost during seed runway
5. Clear upgrade path to Keycloak if enterprise customers need SAML, MFA policies, or federation

**What DOT provides:**

- OAuth2 Authorization Server (Authorization Code, Client Credentials, Implicit, PKCE)
- OpenID Connect Provider (ID tokens, UserInfo endpoint, Discovery endpoint, JWKS)
- Application registration (each Mattermost/Odoo/Nextcloud instance = one OAuth2 Application)
- Token management (access tokens, refresh tokens, scoping)
- Tenant-aware: we can scope OAuth2 Applications to specific tenants

---

## 4. Current State vs. Target State

### Current Provisioning Flow

```
Subscription API (POST /dose/api/subscriptions/)
  ├── Create User (Django auth)
  ├── Create Tenant (schema_name → PostgreSQL schema)
  ├── Create UserProfile (user ↔ tenant)
  ├── Create Subscription (Stripe)
  └── For each enabled app:
      └── Celery task → provision_{app}_tenant()
          ├── POST to {app}.polysaas.online/api/tenants
          ├── Generate password
          └── Send welcome email with credentials
```

**Problem:** Each app gets its own password. Users must remember N passwords. No SSO.

### Target Provisioning Flow

```
Subscription API (POST /dose/api/subscriptions/)
  ├── Create User (Django auth)
  ├── Create Tenant (schema_name → PostgreSQL schema)
  ├── Create UserProfile (user ↔ tenant)
  ├── Create Subscription (Stripe)
  ├── Register OAuth2 Application in DOT (per tenant, per app)
  │     → client_id, client_secret generated
  └── For each enabled app:
      └── Celery task → provision_{app}_tenant()
          ├── POST to {app}.polysaas.online/api/tenants
          ├── Configure OAuth2/OIDC in the app:
          │     → Discovery: https://polysaas.online/.well-known/openid-configuration
          │     → Client ID / Secret from DOT registration
          │     → Redirect URI: {app-url}/oauth/callback
          └── Send welcome email (NO password — just "Log in with PolySaaS")
```

**Result:** User logs into PolySaaS once → OAuth2 tokens grant access to all their apps.

---

## 5. Implementation Plan

### Phase 1: Django as OIDC Provider (1–2 weeks)

**Install and configure `django-oauth-toolkit`:**

```
pip install django-oauth-toolkit
```

**settings.py additions:**

```python
INSTALLED_APPS = [
    ...
    'oauth2_provider',
    ...
]

OAUTH2_PROVIDER = {
    'OIDC_ENABLED': True,
    'OIDC_RSA_PRIVATE_KEY': '<generated RSA private key>',
    'SCOPES': {
        'openid': 'OpenID Connect',
        'email': 'Email address',
        'profile': 'User profile',
        'tenant': 'Tenant information',
    },
    'OAUTH2_VALIDATOR_CLASS': 'dose.oauth.TenantAwareValidator',
    'ACCESS_TOKEN_EXPIRE_SECONDS': 3600,
    'REFRESH_TOKEN_EXPIRE_SECONDS': 86400,
}
```

**URL configuration:**

```python
urlpatterns = [
    path('o/', include('oauth2_provider.urls', namespace='oauth2_provider')),
    # This exposes:
    #   /o/authorize/        — Authorization endpoint
    #   /o/token/            — Token endpoint
    #   /o/userinfo/         — OIDC UserInfo endpoint
    #   /o/.well-known/openid-configuration  — Discovery endpoint
    #   /o/jwks/             — JSON Web Key Set
]
```

**Custom OIDC claims (tenant-aware):**

```python
# dose/oauth.py
from oauth2_provider.views.mixins import OIDCOnlyMixin

class TenantAwareValidator(OIDCOnlyMixin):
    def get_additional_claims(self, request):
        """Include tenant info in OIDC ID tokens."""
        user = request.user
        profile = getattr(user, 'userprofile', None)
        return {
            'tenant_id': profile.tenant_id if profile else None,
            'tenant_name': profile.tenant.name if profile else None,
            'tenant_slug': profile.tenant.slug if profile else None,
        }
```

### Phase 2: App-Specific OAuth2 Configuration (1–2 weeks per app)

#### Mattermost Provisioner Enhancement

```python
@shared_task
def provision_mattermost_tenant(tenant_schema, tenant_name, admin_email, company_name, oauth_client_id, oauth_client_secret):
    """Provision Mattermost with OIDC SSO pre-configured."""

    # 1. Create Mattermost team/workspace for tenant
    mm_url = f"https://mm.polysaas.online"
    admin_token = get_mattermost_admin_token()

    # Create team
    team_resp = requests.post(f"{mm_url}/api/v4/teams", headers={"Authorization": f"Bearer {admin_token}"}, json={
        "name": tenant_schema,
        "display_name": tenant_name,
        "type": "I"  # Invite-only
    })
    team = team_resp.json()

    # 2. Configure OIDC via API
    requests.patch(f"{mm_url}/api/v4/config", headers={"Authorization": f"Bearer {admin_token}"}, json={
        "OpenIdSettings": {
            "Enable": True,
            "Secret": oauth_client_secret,
            "Id": oauth_client_id,
            "DiscoveryEndpoint": "https://polysaas.online/o/.well-known/openid-configuration",
            "ButtonText": "Log in with PolySaaS",
            "ButtonColor": "#003399"
        }
    })

    # 3. Create initial admin user via OIDC flow (or invite via email)
    # ...
```

#### Odoo Provisioner Enhancement

```python
@shared_task
def provision_odoo_tenant(tenant_schema, tenant_name, admin_email, company_name, oauth_client_id, oauth_client_secret):
    """Provision Odoo with OAuth2 SSO pre-configured."""

    # 1. Create Odoo database for tenant
    odoo_url = f"https://odoo.polysaas.online"
    # ... existing tenant creation ...

    # 2. Install auth_oauth module
    # Via JSON-RPC: models.execute_kw(db, uid, pwd, 'ir.module.module', 'button_immediate_install', [[module_id]])

    # 3. Create OAuth provider record
    # Via JSON-RPC: models.execute_kw(db, uid, pwd, 'auth.oauth.provider', 'create', [{...}])
    provider_data = {
        'name': 'PolySaaS SSO',
        'flow': 'id_token_code',  # Authorization Code flow
        'client_id': oauth_client_id,
        'client_secret': oauth_client_secret,
        'auth_endpoint': 'https://polysaas.online/o/authorize/',
        'token_endpoint': 'https://polysaas.online/o/token/',
        'jwks_uri': 'https://polysaas.online/o/jwks/',
        'validation_endpoint': 'https://polysaas.online/o/userinfo/',
        'scope': 'openid email profile',
        'enabled': True,
        'body': 'Log in with PolySaaS',
    }
```

#### Nextcloud Provisioner Enhancement

```python
@shared_task
def provision_nextcloud_tenant(tenant_schema, tenant_name, admin_email, company_name, oauth_client_id, oauth_client_secret):
    """Provision Nextcloud with OIDC SSO pre-configured."""

    # 1. Create Nextcloud user/group for tenant
    nc_url = f"https://nextcloud.polysaas.online"
    # ... existing tenant creation ...

    # 2. Install and configure user_oidc app via occ
    # Docker exec into Nextcloud container:
    docker_exec(f"occ app:enable user_oidc")
    docker_exec(f"occ user_oidc:provider PolySaaS "
                f"--clientid='{oauth_client_id}' "
                f"--clientsecret='{oauth_client_secret}' "
                f"--discoveryuri='https://polysaas.online/o/.well-known/openid-configuration' "
                f"--scope='openid email profile' "
                f"--unique-uid=1 "
                f"--check-bearer=1")
```

### Phase 3: Enhanced Subscription Flow (1 week)

Update `SubscriptionApiViewSet.create` to:

1. **Register an OAuth2 Application** in DOT for each enabled app:

```python
from oauth2_provider.models import Application

if data.get('enable_mattermost') or data.get('enable_odoo') or data.get('enable_nextcloud'):
    for app_name in ['mattermost', 'odoo', 'nextcloud']:
        if data.get(f'enable_{app_name}'):
            oauth_app = Application.objects.create(
                name=f"{tenant_name}-{app_name}",
                user=user_obj,
                client_type=Application.CLIENT_CONFIDENTIAL,
                authorization_grant_type=Application.GRANT_AUTHORIZATION_CODE,
                redirect_uris=get_redirect_uri(app_name, tenant_schema),
            )
            # Pass client_id and client_secret to provisioner
            provision_task.delay(
                tenant_schema=tenant_obj.schema_name,
                tenant_name=tenant_obj.name,
                admin_email=user_obj.email,
                company_name=tenant_obj.name,
                oauth_client_id=oauth_app.client_id,
                oauth_client_secret=oauth_app.client_secret,
            )
```

2. **Store OAuth2 app references** on the Tenant or Subscription model for management.

### Phase 4: Error Handling & Resilience (built into all phases)

**Celery retry policy for all provisioning tasks:**

```python
@shared_task(bind=True, max_retries=3, default_retry_delay=30)
def provision_mattermost_tenant(self, tenant_schema, ...):
    try:
        # ... provisioning logic ...
    except requests.exceptions.HTTPError as exc:
        if exc.response.status_code >= 500:
            raise self.retry(exc=exc, countdown=30 * (self.request.retries + 1))
        raise
    except Exception as exc:
        # Log to dead-letter queue / notify admin
        notify_admin_provisioning_failure(tenant_schema, 'mattermost', str(exc))
        TenantApp.objects.filter(tenant__schema_name=tenant_schema, app_name='mattermost').update(status='error')
        raise
```

**Dead-letter queue:** Failed provisioning tasks are logged with full context (tenant, app, error, retry count). Admin dashboard shows `TenantApp` entries with `status='error'` for manual intervention.

**Fallback:** Admin can manually trigger re-provisioning from the Django admin panel or via management command.

### Phase 5: User Consent Screen

DOT supports custom authorization views. We implement a branded consent screen:

```python
# dose/views/oauth_consent.py
from oauth2_provider.views import AuthorizationView

class TenantAwareAuthorizationView(AuthorizationView):
    template_name = 'dose/oauth/authorize.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['tenant_name'] = self.request.session.get('tenant_name', 'Your Organization')
        context['app_name'] = self.get_application_name()
        return context
```

**Auto-approve logic:** When the requesting OAuth2 application belongs to the same tenant as the logged-in user (via `TenantApp` lookup), skip the consent screen for frictionless SSO. Show explicit consent only for cross-tenant or third-party access.

---

## 6. Data Model Changes

### New: TenantApp Model

```python
class TenantApp(models.Model):
    """Tracks which apps are provisioned for each tenant, with their OAuth2 config."""
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name='apps')
    app_name = models.CharField(max_length=50)  # 'mattermost', 'odoo', 'nextcloud'
    app_url = models.URLField(blank=True)
    oauth_application = models.OneToOneField(
        'oauth2_provider.Application', on_delete=models.SET_NULL, null=True, blank=True
    )
    provisioned_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, default='provisioning',
                              choices=[('provisioning', 'Provisioning'),
                                       ('active', 'Active'),
                                       ('error', 'Error'),
                                       ('disabled', 'Disabled')])

    class Meta:
        unique_together = ('tenant', 'app_name')
```

---

## 7. User Login Flow (Post-Implementation)

```
1. User visits https://polysaas.online and logs in
   (via username/password, Google OAuth, or GitHub OAuth — allauth handles this)

2. User clicks "Open Mattermost" from their dashboard

3. PolySaaS redirects to Mattermost with OAuth2 authorization
   → Mattermost redirects to PolySaaS /o/authorize/
   → User is already logged in → auto-approve
   → PolySaaS issues authorization code
   → Mattermost exchanges code for tokens
   → User is logged into Mattermost (JIT user creation if first time)

4. Same flow for Odoo and Nextcloud — one login, all apps.
```

---

## 8. Security Considerations

| Concern | Mitigation |
|---------|-----------|
| Token leakage | Short-lived access tokens (1hr), refresh tokens (24hr), HTTPS everywhere |
| Cross-tenant access | OAuth2 Applications are scoped per tenant; OIDC claims include `tenant_id` |
| Nextcloud full-access tokens | PolySaaS controls Nextcloud instance; fine-grained permissions via proxy handler + atomic services; document for SOC 2 |
| Mattermost team isolation | Each tenant gets their own Mattermost team; OIDC auto-assigns to correct team |
| Odoo database isolation | Each tenant has a separate Odoo database; OAuth provider is per-database |
| PKCE support | DOT supports PKCE out of the box; enable for public clients (SPA dashboards) |
| Provisioning failure blocks onboarding | Celery retries (3x on 5xx) + dead-letter queue; fallback to manual provisioning in admin UI; per-app status dashboard via `TenantApp.status` |
| User consent / scope transparency | Custom DOT consent view shows tenant name and requested scopes; auto-approve for same-tenant apps; explicit consent for cross-tenant |

---

## 9. Dependencies

| Package | Purpose | Version |
|---------|---------|---------|
| `django-oauth-toolkit` | OAuth2/OIDC Provider for Django | Latest (2.x) |
| `cryptography` | RSA key generation for OIDC JWT signing | Already in requirements |
| `pyjwt` | JWT token handling | Already available via DOT |

---

## 10. Timeline Estimate

| Phase | Work | Duration |
|-------|------|----------|
| Phase 1 | Install DOT, configure OIDC provider, generate RSA keys, expose endpoints, consent view | 1–2 weeks |
| Phase 2a | Mattermost provisioner with OIDC config via `/api/v4/config` | 3–5 days |
| Phase 2b | Odoo provisioner with OAuth provider via JSON-RPC | 3–5 days |
| Phase 2c | Nextcloud provisioner with `user_oidc` via `occ` CLI | 3–5 days |
| Phase 3 | Subscription flow enhancement, TenantApp model, dashboard integration | 1 week |
| Phase 4 | Celery retry/DLQ, error handling, admin fallback UI | Built into Phases 2–3 |
| Phase 5 | Consent screen, auto-approve logic for same-tenant apps | 2–3 days |
| Testing | End-to-end SSO flow testing per app + failure cases (expired token, invalid client, retry recovery) | 1 week |
| **Total** | | **4–6 weeks** |

### Testing Coverage

End-to-end tests for each app SSO flow + failure cases:

- **Happy path:** Subscribe → provision → OIDC login → JIT user creation → app access
- **Token expiry:** Access token expires → refresh token flow → seamless re-auth
- **Invalid client:** Wrong client_secret → graceful error → user sees "contact admin"
- **Provisioning failure:** App API returns 500 → Celery retries 3x → DLQ → admin notified → `TenantApp.status='error'`
- **Cross-tenant:** User from Tenant A tries to access Tenant B's Mattermost → rejected by OIDC claim validation
- **De-provisioning:** Tenant disabled → OAuth2 applications revoked → all app tokens invalidated

### Infrastructure Cost Impact

Django OIDC overhead is negligible — token issuance and validation are lightweight cryptographic operations (<5% CPU impact on the existing Django service). No new service is required until a potential Keycloak migration for enterprise customers needing SAML, LDAP federation, or advanced MFA policies. RSA key storage uses a single private key in settings (or GCP Secret Manager in production).

---

## 11. What This Unlocks

- **For tenants:** One login for everything. No password management for individual apps.
- **For the business:** "Zero-friction onboarding" becomes real — subscribe, check your apps, log in once.
- **For the pitch:** "AI As Peers in your Mattermost channels" becomes seamless when Mattermost auth is already handled.
- **For security:** Centralized auth = centralized audit trail, MFA enforcement, and revocation.
- **For Apps As Peers (roadmap):** Service-to-service OAuth2 (Client Credentials grant) enables apps to call each other's APIs with proper authorization — the foundation for autonomous app collaboration.
