<!-- SUPERSEDED — see documentation/POLYSAAS_ENDPOINT_WORKSPACE_MODEL.md -->

> **SUPERSEDED (2026-09-01).** The iframe passthrough types described below were
> retired on 2026-08-13 (`BINGO_NEXTCLOUD_JAZZMIN_PANEL_NO_IFRAME_2026-08-13.md`).
> Iframes are prohibited by `.cursor/rules/passthrough-no-iframes.mdc`. For the
> current endpoint model see `POLYSAAS_ENDPOINT_WORKSPACE_MODEL.md`.
> Retained for historical context — do not implement from this document.

# PolySaaS Architecture Document

**Version:** 1.0
**Date:** March 2026
**Authors:** Desktop-CC, Michael Oliver

---

## 1. System Overview

PolySaaS is a multi-tenant, AI-powered SaaS orchestration platform built on Django 6.0 and deployed to Google Cloud Platform. It unifies multiple SaaS applications (Odoo, Nextcloud, Mattermost, WordPress, Liferay CE, Dolibarr) behind a single portal with event-driven orchestration, intelligent API sniffing, and AI collaboration.

### Core Principles
- **Multi-tenancy** — PostgreSQL schema isolation per tenant
- **Event-driven orchestration** — Middleware-based request/response interception with message queue routing
- **Zero-code integration** — PolySniffer auto-discovers endpoints; Atomic Services provide building blocks
- **AI As Peers** — AI agents participate as real teammates in Mattermost channels

---

## 2. High-Level Architecture

```
┌──────────────────────────────────────────────────────────────────────┐
│                        CLIENT TIER                                    │
│  ┌─────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐ │
│  │ Browser  │  │  PolySniffer │  │  Mattermost  │  │   REST API   │ │
│  │  (Admin) │  │  Chrome Ext  │  │   Clients    │  │   Consumers  │ │
│  └────┬─────┘  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘ │
└───────┼────────────────┼─────────────────┼─────────────────┼─────────┘
        │                │                 │                 │
┌───────┼────────────────┼─────────────────┼─────────────────┼─────────┐
│       ▼                ▼                 ▼                 ▼         │
│                    APPLICATION TIER                                   │
│  ┌────────────────────────────────────────────────────────────────┐  │
│  │                    Django 6.0 (DOSE)                            │  │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐ │  │
│  │  │  Middleware   │  │  Views/API   │  │  Admin (Jazzmin)     │ │  │
│  │  │  Pipeline     │  │  Endpoints   │  │  Portal Dashboard    │ │  │
│  │  └──────┬───────┘  └──────────────┘  └──────────────────────┘ │  │
│  │         │                                                       │  │
│  │  ┌──────▼───────┐  ┌──────────────┐  ┌──────────────────────┐ │  │
│  │  │  Request/     │  │  PolySniffer │  │  Passthrough Engine  │ │  │
│  │  │  Response     │  │  Capture &   │  │  (Proxy to SaaS     │ │  │
│  │  │  Controllers  │  │  Analysis    │  │   Applications)      │ │  │
│  │  └──────────────┘  └──────────────┘  └──────────────────────┘ │  │
│  └────────────────────────────────────────────────────────────────┘  │
│                                                                       │
│  ┌─────────┐  ┌──────────┐  ┌──────────┐  ┌────────────────────┐   │
│  │  Celery  │  │  Redis   │  │ RabbitMQ │  │  MQ Adapters       │   │
│  │  Worker  │  │  Cache   │  │  Broker  │  │  (Pub/Sub, SQS)    │   │
│  └─────────┘  └──────────┘  └──────────┘  └────────────────────┘   │
└──────────────────────────────────────────────────────────────────────┘
        │                                                    │
┌───────┼────────────────────────────────────────────────────┼─────────┐
│       ▼                DATA TIER                           ▼         │
│  ┌──────────────┐  ┌──────────────┐  ┌─────────────────────────┐   │
│  │  PostgreSQL   │  │  PostgreSQL  │  │  Google Cloud Platform   │   │
│  │  (DOSE DB)    │  │  (Tenants)   │  │  Cloud SQL / BigQuery    │   │
│  │  Port 5433    │  │  Schemas     │  │  Pub/Sub / GCS           │   │
│  └──────────────┘  └──────────────┘  └─────────────────────────┘   │
└──────────────────────────────────────────────────────────────────────┘
        │
┌───────┼──────────────────────────────────────────────────────────────┐
│       ▼            BUNDLED SAAS APPLICATIONS                          │
│  ┌────────┐ ┌───────────┐ ┌────────────┐ ┌─────────┐ ┌───────────┐ │
│  │  Odoo   │ │ Nextcloud  │ │ Mattermost │ │WordPress│ │ Liferay CE│ │
│  │  :8069  │ │   :8888    │ │   :8065    │ │  :8980  │ │   :8181   │ │
│  └────────┘ └───────────┘ └────────────┘ └─────────┘ └───────────┘ │
│  ┌─────────┐ ┌───────────┐ ┌────────────┐ ┌──────────────────────┐ │
│  │ Dolibarr │ │PolySysMon │ │ Focalboard │ │ AI As Peers          │ │
│  │  :8889   │ │   :9001   │ │   :8111    │ │ (Tomcat :8990)       │ │
│  └─────────┘ └───────────┘ └────────────┘ └──────────────────────┘ │
└──────────────────────────────────────────────────────────────────────┘
```

---

## 3. Component Architecture

### 3.1 Django DOSE Core

The main Django application (`dose` app) provides:

| Component | Purpose |
|-----------|---------|
| **Multi-Tenant Engine** | PostgreSQL schema-per-tenant isolation via `Tenant` model and `SessionTenantMiddleware` |
| **Admin Portal** | Jazzmin-themed admin with tenant-aware theming, navigation panels, and dashboard buttons |
| **Passthrough Engine** | `PassThroughEndpoint` model routes requests to bundled SaaS apps via iframe or proxy |
| **Orchestration** | `Instruction` model matches events to actions; `DoseRequestController`/`DoseResponseController` middleware intercepts all requests |
| **REST API** | Django REST Framework with 16+ ViewSets, Swagger/ReDoc documentation |
| **Authentication** | django-allauth with GitHub/Google social login, per-tenant user profiles |

### 3.2 Middleware Pipeline

Requests pass through 19 middleware classes in order:

| Order | Middleware | Role |
|-------|-----------|------|
| 1 | `SecurityMiddleware` | HTTPS enforcement, security headers |
| 2 | `DebugSessionMiddleware` | Session error handling |
| 3 | `CommonMiddleware` | URL normalization |
| 4 | `CSRFExemptionMiddleware` | Exempt passthrough paths from CSRF |
| 5 | `SessionMiddleware` | Session management |
| 6 | `AuthenticationMiddleware` | User authentication |
| 7 | `UserRequestTrackingMiddleware` | Log user requests to `UserRequestTracker` |
| 8 | `DebugRequestMiddleware` | Debug logging |
| 9 | `AdminUnauthorizedMiddleware` | Block non-staff from admin |
| 10 | `AdminTenantSessionMiddleware` | Set tenant context in admin |
| 11 | `SessionTenantMiddleware` | Set PostgreSQL `search_path` per tenant |
| 12 | **`DoseRequestController`** | **Core: match Instructions, route events** |
| 13 | `JazzminTenantThemeMiddleware` | Tenant-specific admin theme/menus |
| 14 | **`DoseResponseController`** | **Core: process responses, trigger callbacks** |
| 15 | `ExternalPassthroughMiddleware` | Proxy requests to `/pt/` endpoints |
| 16 | `CsrfViewMiddleware` | CSRF protection |
| 17 | `MessageMiddleware` | Django messages |
| 18 | `AccountMiddleware` | Allauth session |
| 19 | `XFrameOptionsMiddleware` | Clickjacking protection |

### 3.3 PolySniffer

Auto-discovers and captures API endpoints from bundled SaaS applications.

**Chrome Extension** (`polysniffer-chrome-extension/`):
- `background.js` — Service worker; captures HTTP traffic via `chrome.webRequest`, classifies Odoo JSON-RPC calls
- `content.js` — Intercepts `fetch`/`XHR` calls, captures form submissions, cookies, meta tags
- `popup.js` — UI for connecting to Django, selecting endpoints, sending batches
- Sends captures to Django via `/admin/polysniffer/silent-capture/<id>/`

**Django Backend** (`dose/polysniffer/`):
- `TrafficLog` model stores captured requests with HAR data
- Views for dashboard, live capture, proxy capture, AI analysis
- `ai_analyze_endpoint` / `ai_generate_handler` — AI-powered endpoint analysis and handler code generation
- Export to HAR format

### 3.4 Passthrough Engine

`PassThroughEndpoint` model defines how external SaaS applications are proxied:

| Field | Purpose |
|-------|---------|
| `provider` | Which SaaS app (odoo, nextcloud, mattermost, etc.) |
| `endpoint_url` | Target URL of the SaaS application |
| `passthrough_type` | iframe, proxy, or API |
| `integration_mode` | How to authenticate (api_key, basic_auth, etc.) |
| `inject_proxy_script` | Whether to inject PolySniffer capture script |
| `show_in_menu` | Display in admin sidebar navigation |

### 3.5 Message Queue Architecture

| Component | Technology | Purpose |
|-----------|-----------|---------|
| **Celery** | RabbitMQ broker, Django DB backend | Async task execution |
| **MQ Adapters** | RabbitMQ, Google Pub/Sub, AWS SQS | Event routing between services |
| **MQConfig** | Per-tenant MQ configuration | Tenant-specific queue setup |
| **MQInput/MQOutput** | Request path → queue mapping | Route requests to/from queues |

### 3.6 Multi-Tenant Architecture

```
PostgreSQL Instance (port 5433)
├── public schema (shared tables, default)
├── olient schema (tenant: Olient)
├── demo schema (tenant: Demo)
└── [per-tenant schemas created dynamically]
```

- `Tenant` model holds `schema_name`, branding (logo, colors), and configuration
- `TenantAwareModel` abstract base adds `tenant` FK to all tenant-scoped models
- `SessionTenantMiddleware` sets `SET search_path TO {schema},public` per request
- `UserProfile` links users to tenants with theme preferences
- `Subscription` model (Stripe integration) per tenant

---

## 4. Bundled SaaS Applications

All run as Docker containers, managed via separate docker-compose files:

| Application | Port | Docker Image | Database | docker-compose file |
|-------------|------|-------------|----------|-------------------|
| **Odoo 18** | 8069, 8072 | odoo:18.0 | PostgreSQL 16 | (runtime) |
| **Nextcloud** | 8888 | nextcloud:latest | (internal) | (runtime) |
| **Mattermost** | 8065 | mattermost-team-edition:latest | PostgreSQL 15-alpine | (runtime) |
| **WordPress** | 8980 | wordpress:latest | MySQL 8.0 | docker-compose.wordpress.yml |
| **Liferay CE** | 8181 | liferay/portal:7.4.3.120-ga120 | MySQL 8.0 | docker-compose.liferay.yml |
| **Dolibarr** | 8889 | tuxgasy/dolibarr:latest | MariaDB 10.11 | (runtime) |
| **PolySysMon** | 9001 | polysysmon-demo | (internal) | docker-compose.polysysmon-simple.yml |
| **Focalboard** | 8111 | mattermost/focalboard:latest | (internal) | (runtime) |
| **AI As Peers** | 8990 | tomcat:10.1-jre21 | — | (placeholder) |
| **Redis** | 6379 | redis:7-alpine | — | (runtime) |

---

## 5. REST API Endpoints

### Core API (`/dose/api/`)

| Endpoint | ViewSet | Operations |
|----------|---------|-----------|
| `/dose/api/tenants/` | TenantViewSet | CRUD |
| `/dose/api/userprofiles/` | UserProfileViewSet | CRUD |
| `/dose/api/instructions/` | InstructionViewSet | CRUD |
| `/dose/api/tasks/` | TaskViewSet | CRUD |
| `/dose/api/atomicservices/` | AtomicServiceViewSet | CRUD |
| `/dose/api/subscriptions/` | SubscriptionApiViewSet | CRUD |
| `/dose/api/passthroughendpoints/` | PassThroughEndpointViewSet | CRUD |
| `/dose/api/navigationpanels/` | NavigationPanelViewSet | CRUD |
| `/dose/api/navigationitems/` | NavigationItemViewSet | CRUD |
| `/dose/api/dashboardbuttons/` | DashboardButtonViewSet | CRUD |
| `/dose/api/requestlogs/` | RequestLogViewSet | CRUD |
| `/dose/api/errorlogs/` | ErrorLogViewSet | CRUD |
| `/dose/api/callbackdata/` | CallBackDataViewSet | CRUD |
| `/dose/api/mlengines/` | MLEngineViewSet | CRUD |
| `/dose/api/mltaxonomies/` | MLTaxonomyViewSet | CRUD |
| `/dose/api/mldatasets/` | MLDatasetViewSet | CRUD |
| `/dose/api/ignorepaths/` | IgnorePathViewSet | CRUD |

### PolySniffer API (`/admin/polysniffer/`)

| Endpoint | Purpose |
|----------|---------|
| `api/endpoints/` | List discovered endpoints |
| `api/csrf-token/` | Get CSRF token for extension |
| `silent-capture/<id>/` | Receive captures from Chrome extension |
| `ai-analyze/<id>/` | AI-powered endpoint analysis |
| `ai-generate-handler/<id>/` | Generate handler code from captures |
| `dashboard/` | Capture dashboard |
| `export/` | Export captures as HAR |

### Documentation
- **Swagger UI:** `/swagger/` and `/dose/swagger/`
- **ReDoc:** `/redoc/`
- **Schema JSON:** `/swagger.json`

---

## 6. Authentication & Authorization

| Method | Provider | Purpose |
|--------|----------|---------|
| Django session auth | Built-in | Admin portal, views |
| django-allauth | GitHub, Google | Social login |
| DRF Token/Session | REST Framework | API authentication |
| Stripe | Stripe API | Subscription billing |
| Per-tenant RBAC | Custom middleware | Tenant-scoped access |

---

## 7. Deployment Architecture

### Development (Local)
- `go.ps1` script handles: git sync → backup → venv activation → service startup → Django runserver
- Docker Desktop runs bundled SaaS containers
- PostgreSQL on localhost:5433
- All services on localhost with distinct ports

### Production (GCP)
- **Compute:** Google Cloud Run (containerized Django)
- **Database:** Cloud SQL (PostgreSQL 15)
- **Storage:** Google Cloud Storage (static/media files)
- **Secrets:** Google Secret Manager
- **Registry:** Google Container Registry (`gcr.io/dosev3-saas/dosev3-app`)
- **MQ:** Google Pub/Sub (production message queue)

---

## 8. Technology Stack

| Layer | Technology | Version |
|-------|-----------|---------|
| **Language** | Python | 3.13 |
| **Web Framework** | Django | 6.0.2 |
| **API** | Django REST Framework | latest |
| **Admin Theme** | Jazzmin | latest |
| **Auth** | django-allauth | latest |
| **Database** | PostgreSQL | 15/16 |
| **Cache/Broker** | Redis | 7 |
| **Task Queue** | Celery + RabbitMQ | latest |
| **API Docs** | drf-yasg (Swagger/ReDoc) | latest |
| **Frontend** | Bricks Builder (WordPress) | latest |
| **Containers** | Docker + Docker Compose | latest |
| **Cloud** | Google Cloud Platform | — |
| **CI/CD** | GitHub Actions (disabled) | — |
| **Version Control** | Git + GitHub | — |

---

## 9. Key Design Patterns

1. **Middleware Chain** — All request/response logic flows through a 19-layer middleware pipeline, enabling event interception without modifying application code
2. **Schema-per-Tenant** — PostgreSQL schemas provide hard data isolation between tenants
3. **Passthrough Proxy** — SaaS applications are accessed through Django, enabling sniffing, orchestration, and unified auth
4. **Event-Key Matching** — Instructions match events by `eventKey` to trigger automated workflows
5. **Capture-then-Generate** — PolySniffer captures real API traffic, then AI generates handler code from the captured patterns
6. **AI As Peers** — AI agents post as real users in Mattermost, participating in team conversations via REST API

---

*Document generated from codebase analysis, March 2026*
