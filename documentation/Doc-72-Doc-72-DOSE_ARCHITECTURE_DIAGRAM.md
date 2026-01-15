# DOSE Multi-Tenant SaaS Platform - Complete Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                          DOSE - Dynamic Orchestration Service                        │
│                         Multi-Tenant Django SaaS Platform                           │
└─────────────────────────────────────────────────────────────────────────────────────┘

═══════════════════════════════════════════════════════════════════════════════════════
                            🌐 CLIENT LAYER (Browser)
═══════════════════════════════════════════════════════════════════════════════════════

┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐
│  Public Login   │  │  Admin Panel    │  │ User Dashboard  │  │ External OAuth  │
│                 │  │   (Jazzmin)     │  │  (AdminLTE)     │  │  (Google Auth)  │
│  /accounts/     │  │   /admin/       │  │ /user-dashboard/│  │                 │
│  login/         │  │                 │  │                 │  │                 │
└────────┬────────┘  └────────┬────────┘  └────────┬────────┘  └────────┬────────┘
         │                    │                    │                    │
         └────────────────────┴────────────────────┴────────────────────┘
                                        │
                                        ▼
═══════════════════════════════════════════════════════════════════════════════════════
                         🔒 AUTHENTICATION & AUTHORIZATION
═══════════════════════════════════════════════════════════════════════════════════════

┌───────────────────────────────────────────────────────────────────────────────────┐
│                          Django Allauth OAuth2 System                              │
├───────────────────────────────────────────────────────────────────────────────────┤
│                                                                                     │
│  ┌─────────────────┐    ┌─────────────────┐    ┌──────────────────┐             │
│  │ Google OAuth2   │    │ GitHub OAuth2   │    │ Email/Password   │             │
│  │ ✓ openid        │    │ ✓ user          │    │ ✓ Django Auth    │             │
│  │ ✓ profile       │    │ ✓ repo          │    │ ✓ Allauth        │             │
│  │ ✓ email         │    │                 │    │                  │             │
│  │ ◯ gmail.readonly│    │                 │    │                  │             │
│  │ ◯ gmail.send    │    │                 │    │                  │             │
│  └─────────────────┘    └─────────────────┘    └──────────────────┘             │
│                                                                                     │
│  ✓ = Active  ◯ = Disabled (pending test users)                                   │
└───────────────────────────────────────────────────────────────────────────────────┘
                                        │
                                        ▼
                            ┌────────────────────┐
                            │  Smart Landing     │
                            │  Redirect Logic    │
                            ├────────────────────┤
                            │ is_staff?          │
                            │   ✓ → /admin/      │
                            │   ✗ → /user-dash/  │
                            └────────────────────┘
                                        │
                                        ▼
═══════════════════════════════════════════════════════════════════════════════════════
                    🔄 MIDDLEWARE PIPELINE (Request → Response)
═══════════════════════════════════════════════════════════════════════════════════════

┌───────────────────────────────────────────────────────────────────────────────────┐
│                              REQUEST FLOW ↓                                        │
├───────────────────────────────────────────────────────────────────────────────────┤
│                                                                                     │
│  1. SecurityMiddleware                  - HTTPS redirect, security headers        │
│  2. DebugSessionMiddleware              - Session debugging/logging               │
│  3. CommonMiddleware                    - URL normalization                       │
│  4. CsrfViewMiddleware                  - CSRF protection                         │
│  5. SessionMiddleware                   - Session management                      │
│  6. AuthenticationMiddleware            - User authentication                     │
│  7. UserRequestTrackingMiddleware       - Track user requests                     │
│  8. DebugRequestMiddleware              - Debug request logging                   │
│  9. AdminUnauthorizedMiddleware         - Admin access control                    │
│ 10. AdminTenantSessionMiddleware        - Admin tenant switching                  │
│ 11. SessionTenantMiddleware             - SESSION-BASED MULTI-TENANCY ⭐          │
│ 12. MessagesMiddleware                  - Flash messages                          │
│ 13. AccountMiddleware (Allauth)         - OAuth account handling                  │
│ 14. DoseRequestController               - Request interception/logging ⭐         │
│ 15. ExternalPassthroughMiddleware       - External service proxy (NO IFRAME) ⭐   │
│ 16. JazzminTenantThemeMiddleware        - Per-tenant theme injection              │
│ 17. DoseResponseController              - Response manipulation/logging ⭐        │
│ 18. XFrameOptionsMiddleware             - Clickjacking protection                 │
│                                                                                     │
├───────────────────────────────────────────────────────────────────────────────────┤
│                              RESPONSE FLOW ↑                                       │
└───────────────────────────────────────────────────────────────────────────────────┘

═══════════════════════════════════════════════════════════════════════════════════════
                           🎯 URL ROUTING & VIEWS LAYER
═══════════════════════════════════════════════════════════════════════════════════════

┌─────────────────────────────────────────────────────────────────────────────────────┐
│                                  mysite/urls.py                                      │
├─────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                       │
│  /                          → redirect to dose:landing_page                          │
│  /subscribe/                → subscribe_view (subscription form)                     │
│  /admin/                    → Django Admin (Jazzmin themed)                          │
│  /admin/select-theme/       → Theme selector view                                    │
│  /admin/set-theme/          → Theme update API                                       │
│  /admin/gmail/              → GmailAdminView (Gmail API interface)                   │
│  /admin/osticket/           → osticket_admin_view (OSTicket proxy - NO IFRAME) ⭐    │
│  /admin/osticket/<path>     → osticket_admin_view with subpaths                      │
│  /accounts/login/           → CustomLoginView (enhanced login page)                  │
│  /accounts/                 → Django Allauth URLs (OAuth, password reset, etc)       │
│  /profile/                  → profile_view (user profile page)                       │
│  /dose/                     → dose.urls (main app)                                   │
│  /parameters/               → parameters.urls (atomic service parameters)            │
│  /swagger/                  → API documentation (drf-yasg)                           │
│  /redoc/                    → API documentation (alternative view)                   │
│                                                                                       │
└─────────────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────────────┐
│                                  dose/urls.py                                        │
├─────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                       │
│  /dose/                     → landing_page (smart redirect)                          │
│  /dose/user-dashboard/      → user_dashboard (AdminLTE dashboard for users) ⭐       │
│  /dose/gmail/               → GmailAdminView (user Gmail interface)                  │
│  /dose/gmail-send/          → gmail_send_view (send email via Gmail API)             │
│  /dose/api/*                → DRF API endpoints for subscription management          │
│                                                                                       │
└─────────────────────────────────────────────────────────────────────────────────────┘

═══════════════════════════════════════════════════════════════════════════════════════
                        💾 DATA LAYER - PostgreSQL Database
═══════════════════════════════════════════════════════════════════════════════════════

┌─────────────────────────────────────────────────────────────────────────────────────┐
│                     PostgreSQL (localhost:5433 - dosedbsaas)                         │
├─────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                       │
│  ┌──────────────────────────────────────────────────────────────────────────────┐  │
│  │                        SESSION-BASED MULTI-TENANCY                            │  │
│  │  All data in single database with tenant_id foreign keys                     │  │
│  │  Tenant isolation via SessionTenantMiddleware filtering                      │  │
│  └──────────────────────────────────────────────────────────────────────────────┘  │
│                                                                                       │
│  ┌───────────────────────┐  ┌───────────────────────┐  ┌──────────────────────┐   │
│  │   Core Models         │  │  Tenant Models        │  │  OAuth & Auth        │   │
│  ├───────────────────────┤  ├───────────────────────┤  ├──────────────────────┤   │
│  │ • User                │  │ • Tenant              │  │ • SocialApp          │   │
│  │ • UserProfile         │  │ • Domain              │  │ • SocialAccount      │   │
│  │   - light_theme       │  │ • TenantUser          │  │ • SocialToken        │   │
│  │   - dark_theme        │  │ • TenantTheme         │  │ • Site               │   │
│  │   - use_system_pref   │  │                       │  │                      │   │
│  │ • Group               │  │                       │  │                      │   │
│  │ • Permission          │  │                       │  │                      │   │
│  └───────────────────────┘  └───────────────────────┘  └──────────────────────┘   │
│                                                                                       │
│  ┌───────────────────────┐  ┌───────────────────────┐  ┌──────────────────────┐   │
│  │  Service Integration  │  │  Parameters/Services  │  │  Subscription        │   │
│  ├───────────────────────┤  ├───────────────────────┤  ├──────────────────────┤   │
│  │ • PassthroughEndpoint │  │ • AtomicService       │  │ • Subscription       │   │
│  │   - trigger_path      │  │ • ServiceParameter    │  │ • SubscriptionPlan   │   │
│  │   - endpoint_url      │  │ • ParameterValue      │  │ • Customer           │   │
│  │   - is_enabled        │  │                       │  │                      │   │
│  │   - show_in_menu ⭐   │  │                       │  │                      │   │
│  │   - menu_title        │  │                       │  │                      │   │
│  │ • GmailToken          │  │                       │  │                      │   │
│  └───────────────────────┘  └───────────────────────┘  └──────────────────────┘   │
│                                                                                       │
└─────────────────────────────────────────────────────────────────────────────────────┘

═══════════════════════════════════════════════════════════════════════════════════════
                    🔌 EXTERNAL SERVICE INTEGRATION (NO IFRAMES!)
═══════════════════════════════════════════════════════════════════════════════════════

┌─────────────────────────────────────────────────────────────────────────────────────┐
│              ExternalPassthroughMiddleware - Middleware-Based Proxy                  │
├─────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                       │
│  HOW IT WORKS:                                                                       │
│  1. Browser → /admin/osticket/login.php                                             │
│  2. Middleware intercepts request (matches PassthroughEndpoint.trigger_path)        │
│  3. Forwards to external URL with proper headers & cookies                          │
│  4. External service responds with HTML                                             │
│  5. Middleware rewrites URLs in HTML (forms, links, scripts, CSS)                   │
│  6. Browser receives modified HTML as if native Django page                         │
│                                                                                       │
│  URL REWRITING EXAMPLES:                                                            │
│  • https://osticket.example.com/scp/login.php → /admin/osticket/scp/login.php      │
│  • /scp/tickets.php → /admin/osticket/scp/tickets.php                              │
│  • <form action="login.php"> → <form action="/admin/osticket/scp/login.php">       │
│                                                                                       │
│  SESSION PERSISTENCE:                                                               │
│  • Cookies forwarded with credentials:'include'                                     │
│  • Session maintained across requests                                               │
│  • CSRF tokens passed through                                                       │
│                                                                                       │
│  ⚠️ CRITICAL: NO IFRAMES - FULL PAGE CONTENT ONLY                                   │
│                                                                                       │
└─────────────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────────────┐
│                         Current External Service Integrations                        │
├─────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                       │
│  ┌──────────────────┐     ┌──────────────────┐     ┌─────────────────────┐         │
│  │   OSTicket       │     │   Gmail API      │     │   Echo Service      │         │
│  │                  │     │                  │     │   (Test/Demo)       │         │
│  │ Trigger:         │     │ Trigger:         │     │                     │         │
│  │ /admin/osticket/ │     │ /admin/gmail/    │     │ Trigger:            │         │
│  │                  │     │ /dose/gmail/     │     │ /test-echo/         │         │
│  │ Target:          │     │                  │     │                     │         │
│  │ http://          │     │ API: Gmail REST  │     │ Target:             │         │
│  │ localhost:8080   │     │ OAuth2 Scopes:   │     │ http://             │         │
│  │                  │     │ • gmail.readonly │     │ localhost:5000      │         │
│  │ Features:        │     │ • gmail.send     │     │                     │         │
│  │ ✓ Login          │     │   (disabled)     │     │ Features:           │         │
│  │ ✓ Tickets        │     │                  │     │ ✓ Request echo      │         │
│  │ ✓ Search         │     │ Features:        │     │ ✓ Header display    │         │
│  │ ✓ Settings       │     │ ✓ Read emails    │     │                     │         │
│  │ ✓ Users          │     │ ✓ Send emails    │     │                     │         │
│  │ ✓ Session sync   │     │ ✓ Token refresh  │     │                     │         │
│  └──────────────────┘     └──────────────────┘     └─────────────────────┘         │
│                                                                                       │
└─────────────────────────────────────────────────────────────────────────────────────┘

═══════════════════════════════════════════════════════════════════════════════════════
                          🎨 FRONTEND & UI FRAMEWORKS
═══════════════════════════════════════════════════════════════════════════════════════

┌─────────────────────────────────────────────────────────────────────────────────────┐
│                               Admin Interface (Staff)                                │
├─────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                       │
│  Framework: Django Jazzmin (Bootstrap 5 based)                                       │
│  Theme System: Per-user customizable (light/dark themes)                            │
│  Location: /admin/                                                                   │
│                                                                                       │
│  Features:                                                                           │
│  • Dashboard widgets (custom cards, charts)                                          │
│  • Dynamic top menu (passthrough endpoints injected)                                │
│  • Sidebar navigation with icons                                                     │
│  • User menu with profile, settings, theme toggle                                   │
│  • Tenant selector dropdown                                                          │
│  • Per-tenant branding/theming                                                       │
│                                                                                       │
│  Components:                                                                         │
│  • AdminLTE 3.2 CSS/JS                                                              │
│  • Bootstrap 5                                                                       │
│  • FontAwesome 5 icons                                                              │
│  • jQuery                                                                            │
│                                                                                       │
└─────────────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────────────┐
│                             User Dashboard (Non-Staff)                               │
├─────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                       │
│  Framework: AdminLTE 3.2 (matching admin interface design)                          │
│  Location: /user-dashboard/                                                          │
│  Template: dose/templates/dose/user_dashboard.html                                   │
│                                                                                       │
│  Features:                                                                           │
│  • Dashboard widgets (Messages, Tickets, Team, Notifications)                       │
│  • Top navbar with user menu                                                         │
│  • Sidebar navigation                                                                │
│  • Dynamic passthrough endpoints in 4 locations: ⭐                                  │
│    1. Top navbar menu                                                                │
│    2. Tenant banner                                                                  │
│    3. Sidebar navigation                                                             │
│    4. Quick actions buttons                                                          │
│  • User profile section                                                              │
│  • Quick action cards                                                                │
│                                                                                       │
│  Components:                                                                         │
│  • AdminLTE 3.2 CSS/JS                                                              │
│  • Bootstrap 4                                                                       │
│  • FontAwesome icons                                                                │
│  • jQuery                                                                            │
│                                                                                       │
└─────────────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────────────┐
│                               Login Pages (Enhanced)                                 │
├─────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                       │
│  Templates:                                                                          │
│  • templates/account/login.html (Allauth login)                                     │
│  • dose/templates/dose/login.html (Dose custom login)                               │
│  • templates/admin/login.html (Admin login)                                         │
│                                                                                       │
│  Features: ⭐                                                                         │
│  • Google OAuth "Sign in with Google" button                                        │
│  • GitHub OAuth option                                                              │
│  • Username/Email + Password form                                                    │
│  • "Forgot Password" link → /accounts/password/reset/                              │
│  • "Subscribe" link → /subscribe/                                                   │
│  • Clean, modern design                                                              │
│                                                                                       │
└─────────────────────────────────────────────────────────────────────────────────────┘

═══════════════════════════════════════════════════════════════════════════════════════
                        📦 DJANGO APPS & MODULES STRUCTURE
═══════════════════════════════════════════════════════════════════════════════════════

┌─────────────────────────────────────────────────────────────────────────────────────┐
│                                 INSTALLED_APPS                                       │
├─────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                       │
│  Core Django:                                                                        │
│  • django.contrib.admin          - Django admin interface                           │
│  • django.contrib.auth           - User authentication                              │
│  • django.contrib.contenttypes   - Content type framework                           │
│  • django.contrib.sessions       - Session management                               │
│  • django.contrib.messages       - Flash messages                                   │
│  • django.contrib.staticfiles    - Static file serving                              │
│  • django.contrib.sites          - Multi-site support (for Allauth)                │
│                                                                                       │
│  Third-Party:                                                                        │
│  • jazzmin                       - Admin theme (MUST BE FIRST!)                     │
│  • allauth                       - OAuth2 & social authentication                   │
│  • allauth.account               - Account management                               │
│  • allauth.socialaccount         - Social account integration                       │
│  • allauth.socialaccount.providers.github  - GitHub OAuth                           │
│  • allauth.socialaccount.providers.google  - Google OAuth ⭐                        │
│  • rest_framework                - Django REST Framework (API)                      │
│  • drf_yasg                      - Swagger/OpenAPI documentation                    │
│  • easy_thumbnails               - Image thumbnail generation                       │
│  • corsheaders                   - CORS middleware                                  │
│  • django_extensions             - Development utilities                            │
│                                                                                       │
│  Custom Apps:                                                                        │
│  • dose                          - Main application ⭐                               │
│  • parameters                    - Atomic service parameters ⭐                      │
│  • alerts                        - Alert/notification system                        │
│  • active_urls                   - Active URL tracking                              │
│                                                                                       │
└─────────────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────────────┐
│                          dose/ - Main Application Structure                          │
├─────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                       │
│  dose/                                                                               │
│  ├── models.py                   - Core models (Tenant, Domain, UserProfile, etc)   │
│  ├── views.py                    - Main views (landing_page, user_dashboard) ⭐     │
│  ├── views_custom_login.py       - Custom login view                                │
│  ├── subscription_views.py       - Subscription API views                           │
│  ├── admin.py                    - Django admin customization                       │
│  ├── admin_views.py              - Custom admin views (theme selector)              │
│  ├── gmail.py                    - Gmail API integration                            │
│  ├── osticket_admin.py           - OSTicket proxy view ⭐                           │
│  ├── urls.py                     - URL routing                                      │
│  ├── doserequestcontroller.py   - Request middleware ⭐                             │
│  ├── doseresponsecontroller.py  - Response middleware ⭐                            │
│  ├── context_processors.py      - Template context processors                       │
│  ├── middleware/                 - Custom middleware modules                        │
│  │   ├── admin_unauthorized.py   - Admin access control                            │
│  │   └── jazzmin_tenant_theme.py - Tenant theme injection                          │
│  ├── templates/                  - Templates                                        │
│  │   ├── dose/                                                                      │
│  │   │   ├── login.html                                                             │
│  │   │   └── user_dashboard.html  - User dashboard ⭐                               │
│  │   ├── account/                                                                   │
│  │   │   └── login.html           - Enhanced Allauth login ⭐                       │
│  │   └── admin/                                                                     │
│  │       ├── login.html                                                             │
│  │       └── select_theme.html    - Theme selector                                 │
│  └── static/                     - Static files (CSS, JS, images)                  │
│                                                                                       │
└─────────────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────────────┐
│                        mysite/ - Project Configuration                               │
├─────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                       │
│  mysite/                                                                             │
│  ├── settings.py                 - Django settings (all configuration)              │
│  ├── urls.py                     - Root URL routing                                 │
│  ├── wsgi.py                     - WSGI application                                 │
│  ├── asgi.py                     - ASGI application                                 │
│  ├── session_tenant_middleware.py         - Session-based multi-tenancy ⭐          │
│  ├── admin_tenant_session_middleware.py   - Admin tenant switching                 │
│  ├── external_passthrough_middleware.py   - External service proxy ⭐              │
│  ├── debug_session_middleware.py          - Session debugging                      │
│  ├── context_processors.py                - Global context processors              │
│  └── custom_context_processors.py         - Custom context data                    │
│                                                                                       │
└─────────────────────────────────────────────────────────────────────────────────────┘

═══════════════════════════════════════════════════════════════════════════════════════
                      🔧 CONFIGURATION & ENVIRONMENT
═══════════════════════════════════════════════════════════════════════════════════════

┌─────────────────────────────────────────────────────────────────────────────────────┐
│                            Environment Variables (.env)                              │
├─────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                       │
│  DJANGO_SECRET_KEY              - Django secret key                                  │
│  DOSE_DB_PASSWORD               - PostgreSQL password                                │
│  STRIPE_SECRET_KEY              - Stripe API secret                                  │
│  STRIPE_PUBLISHABLE_KEY         - Stripe public key                                  │
│  STRIPE_PRICE_ID                - Subscription price ID                              │
│                                                                                       │
└─────────────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────────────┐
│                              Database Configuration                                  │
├─────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                       │
│  Engine:    PostgreSQL                                                               │
│  Host:      localhost                                                                │
│  Port:      5433                                                                     │
│  Database:  dosedbsaas                                                               │
│  User:      dosedbadmin                                                              │
│                                                                                       │
│  Migration Strategy:                                                                 │
│  • run_migrations.py - Custom multi-schema migration script                         │
│  • Supports session-based tenant isolation                                          │
│                                                                                       │
└─────────────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────────────┐
│                              Static & Media Files                                    │
├─────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                       │
│  Static Files:                                                                       │
│  • /static/ - Collected static files                                                │
│  • STATICFILES_DIRS - Development static directories                                │
│  • STATIC_URL = '/static/'                                                          │
│                                                                                       │
│  Media Files:                                                                        │
│  • /media/ - User uploaded files                                                    │
│  • MEDIA_URL = '/media/'                                                            │
│                                                                                       │
└─────────────────────────────────────────────────────────────────────────────────────┘

═══════════════════════════════════════════════════════════════════════════════════════
                         🚀 DEPLOYMENT & SERVICE MANAGEMENT
═══════════════════════════════════════════════════════════════════════════════════════

┌─────────────────────────────────────────────────────────────────────────────────────┐
│                              Service Start Scripts                                   │
├─────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                       │
│  start_services.bat / start_services.ps1                                            │
│  ├── Start Django (port 8000)          - Main application                          │
│  └── Start Echo Service (port 5000)    - Test external service                     │
│                                                                                       │
│  Individual Scripts:                                                                 │
│  • start_server.bat / start_server.ps1 - Django only                                │
│  • django_cmd.bat / django_cmd.ps1     - Django management commands                 │
│  • go.ps1                               - Quick start script                        │
│                                                                                       │
└─────────────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────────────┐
│                           Development Workflow Tools                                 │
├─────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                       │
│  Setup & Configuration:                                                              │
│  • setup_google_oauth.py          - Interactive Google OAuth setup ⭐               │
│  • setup_osticket_endpoint.py     - Configure OSTicket integration                  │
│  • create_superuser.py            - Create admin user                               │
│  • create_tenant.py               - Create new tenant                               │
│  • run_migrations.py              - Run database migrations                         │
│                                                                                       │
│  Diagnostic Tools:                                                                   │
│  • check_oauth_config.py          - Verify OAuth configuration                      │
│  • check_tenant_setup.py          - Verify tenant setup                             │
│  • check_db.py                    - Database connectivity check                     │
│  • show_oauth_redirect_uris.py    - Display required OAuth URIs ⭐                  │
│                                                                                       │
│  Testing Scripts:                                                                    │
│  • test_*.py                      - Various integration tests                       │
│                                                                                       │
└─────────────────────────────────────────────────────────────────────────────────────┘

═══════════════════════════════════════════════════════════════════════════════════════
                          🎯 KEY ARCHITECTURAL PATTERNS
═══════════════════════════════════════════════════════════════════════════════════════

┌─────────────────────────────────────────────────────────────────────────────────────┐
│  1. SESSION-BASED MULTI-TENANCY (Primary Pattern)                                   │
├─────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                       │
│  • Middleware: SessionTenantMiddleware                                              │
│  • Mechanism: Tenant ID stored in session, applied to all DB queries               │
│  • Isolation: Foreign key filtering at ORM level                                    │
│  • Switching: Admin can switch tenants via dropdown                                 │
│  • Benefits: Single database, easy to maintain, flexible                            │
│                                                                                       │
└─────────────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────────────┐
│  2. MIDDLEWARE PASSTHROUGH (NO IFRAMES - Critical!)                                 │
├─────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                       │
│  • Middleware: ExternalPassthroughMiddleware                                        │
│  • Pattern: Intercept → Forward → Rewrite → Return                                 │
│  • URL Rewriting: All links, forms, scripts rewritten to proxy paths               │
│  • Session Sync: Cookies forwarded with credentials:'include'                      │
│  • Use Cases: OSTicket, external admin panels, legacy systems                      │
│  • ⚠️ RULE: NO IFRAMES IN DOSE - EVER                                              │
│                                                                                       │
└─────────────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────────────┐
│  3. DYNAMIC MENU INJECTION                                                           │
├─────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                       │
│  • Database: PassthroughEndpoint model (show_in_menu=True)                          │
│  • Context Processor: admin_active_urls, tenant_context                             │
│  • Middleware: JazzminTenantThemeMiddleware                                         │
│  • Injection Points: Admin top menu, user dashboard (4 locations)                  │
│  • Benefits: No code changes to add new services                                    │
│                                                                                       │
└─────────────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────────────┐
│  4. SMART AUTHENTICATION REDIRECT                                                    │
├─────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                       │
│  • View: landing_page() in dose/views.py                                            │
│  • Logic: Check user.is_staff or user.is_superuser                                  │
│  • Staff: Redirect to /admin/ (Jazzmin interface)                                  │
│  • Users: Redirect to /user-dashboard/ (AdminLTE interface)                        │
│  • OAuth: Works seamlessly with Google/GitHub login                                │
│                                                                                       │
└─────────────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────────────┐
│  5. PER-USER THEME CUSTOMIZATION                                                     │
├─────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                       │
│  • Model: UserProfile (light_theme, dark_theme, use_system_pref)                   │
│  • Signal: post_save creates UserProfile automatically                             │
│  • View: select_theme view + template                                               │
│  • Context Processor: jazzmin_ui_tweaks                                             │
│  • UI: Theme selector in admin top menu                                             │
│                                                                                       │
└─────────────────────────────────────────────────────────────────────────────────────┘

═══════════════════════════════════════════════════════════════════════════════════════
                            📊 REQUEST/RESPONSE FLOW
═══════════════════════════════════════════════════════════════════════════════════════

EXAMPLE: User logs in via Google and accesses OSTicket

1. Browser: GET /accounts/google/login/
   ↓
2. Allauth: Redirect to Google OAuth consent screen
   ↓
3. Google: User authorizes, redirect to /accounts/google/login/callback/?code=...
   ↓
4. Allauth: Exchange code for token, create/login user
   ↓
5. Django: landing_page() checks user.is_staff
   ↓
6. Redirect: /admin/ (if staff) or /user-dashboard/ (if not)
   ↓
7. User clicks: OSTicket link in admin menu
   ↓
8. Browser: GET /admin/osticket/
   ↓
9. ExternalPassthroughMiddleware:
   - Matches trigger_path="/admin/osticket/"
   - Forwards to endpoint_url="http://localhost:8080/"
   - Includes session cookies
   ↓
10. OSTicket: Returns login page HTML
    ↓
11. Middleware: Rewrites all URLs in HTML
    - /scp/login.php → /admin/osticket/scp/login.php
    - <link href="/css/style.css"> → <link href="/admin/osticket/css/style.css">
    ↓
12. Browser: Receives modified HTML, displays as native page
    ↓
13. User submits: POST /admin/osticket/scp/login.php (username/password)
    ↓
14. Middleware: Forwards POST to http://localhost:8080/scp/login.php
    ↓
15. OSTicket: Sets session cookie, redirects to dashboard
    ↓
16. Middleware: Rewrites redirect URL, passes cookie
    ↓
17. Browser: Logged into OSTicket, all navigation continues through proxy

═══════════════════════════════════════════════════════════════════════════════════════
                                🔒 SECURITY FEATURES
═══════════════════════════════════════════════════════════════════════════════════════

• CSRF Protection (CsrfViewMiddleware)
• XSS Protection (Django template auto-escaping)
• Clickjacking Protection (XFrameOptionsMiddleware)
• SQL Injection Protection (ORM parameterized queries)
• Session Security (secure cookies in production)
• OAuth2 Token Storage (encrypted in database)
• Password Hashing (PBKDF2 SHA256)
• Admin Access Control (AdminUnauthorizedMiddleware)
• Tenant Isolation (SessionTenantMiddleware filtering)
• HTTPS Redirect (SecurityMiddleware in production)

═══════════════════════════════════════════════════════════════════════════════════════
                              📝 RECENT ENHANCEMENTS
═══════════════════════════════════════════════════════════════════════════════════════

✅ Google OAuth2 Login (openid, profile, email)
✅ Unified Login Page with Smart Redirect
✅ User Dashboard (AdminLTE design matching admin interface)
✅ Dynamic Passthrough Endpoints in User Dashboard (4 locations)
✅ Subscribe Link on Login Pages
✅ Forgot Password Link on Login Pages
✅ OSTicket Integration (full session persistence, no iframe)
✅ Gmail API Integration (OAuth2 scopes ready)
✅ Interactive OAuth Setup Script (setup_google_oauth.py)

═══════════════════════════════════════════════════════════════════════════════════════

Legend:
⭐ = Critical/Key Component
✓ = Active/Enabled
◯ = Disabled/Pending
↓ = Data Flow Direction

```

---

## Architecture Philosophy

**DOSE** is built on three core principles:

1. **NO IFRAMES** - All external services integrated via middleware passthrough
2. **SESSION-BASED TENANCY** - Simple, flexible multi-tenant architecture
3. **DYNAMIC CONFIGURATION** - Services added via database, no code changes needed

This architecture provides a scalable, maintainable SaaS platform that can integrate any external service while maintaining security and user experience.
