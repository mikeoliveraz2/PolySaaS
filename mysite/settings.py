# Force import of AllauthCaseInsensitiveBackend to ensure module is loaded at startup (debugging)
# Debug logging for Allauth authentication troubleshooting
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'loggers': {
        'allauth': {
            'handlers': ['console'],
            'level': 'DEBUG',
            'propagate': True,
        },
        'django.security': {
            'handlers': ['console'],
            'level': 'DEBUG',
            'propagate': True,
        },
    },
}
# DO NOT MODIFY: Critical system file. Ask before making changes.
# Stripe price ID for subscriptions (replace with your actual Stripe price ID)

import environ
import importlib
import json
import os
import sys
from django.core.exceptions import ImproperlyConfigured
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
env = environ.Env()
env.read_env(os.path.join(BASE_DIR, '.env'), overwrite=False)

from dose.utils.secret_manager import sm

# Prefer env var for local development, fall back to GCP Secret Manager
SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY') or sm('DJANGO_SECRET_KEY', 'DJANGO_SECRET_KEY')
source = "env var" if os.environ.get('DJANGO_SECRET_KEY') else "Secret Manager"
print(f"Loaded DJANGO_SECRET_KEY: {'SET' if SECRET_KEY else 'NOT FOUND'} (from {source})", file=sys.stderr)
if not SECRET_KEY:
    raise ImproperlyConfigured("Set the DJANGO_SECRET_KEY secret in GCP Secret Manager or DJANGO_SECRET_KEY env var")
DEBUG = True

# Ensure all HTTP responses use UTF-8 encoding (prevents UnicodeEncodeError on Windows with cp1252)
DEFAULT_CHARSET = 'utf-8'

# Passthrough: log upstream + final HTML diagnostics to console (all endpoints). See dose/passthrough/stream_debug.py
POLYSNIFFER_PASSTHROUGH_DEBUG = env.bool("POLYSNIFFER_PASSTHROUGH_DEBUG", default=False)
# When True, append AdminIndexDiagMiddleware (logs one line per /admin/ index hit).
# Compare local vs Render: app_list length, template name, schema_name, user flags.
ADMIN_INDEX_DIAG = env.bool("ADMIN_INDEX_DIAG", default=False)
# Jazzmin admin theme settings (customize as needed)
JAZZMIN_SETTINGS = {
    "custom_links": {},
    "SITE_TITLE": "Dose Admin",
    "SITE_HEADER": '<img src="/static/img/PolySaaS-Industrial-Logo.png" style="height: 50px; margin-right: 10px; vertical-align: middle;" alt="PolySaaS"/> Dose Admin Portal',
    "SITE_BRAND": "PolySaaS",
    "WELCOME_SIGN": "Welcome to DoseSaaS Admin",
    "copyright": "DoseSaaS 2025",
    "show_ui_builder": False,
    "index_template": "jazzmin/admin/index.html",
    "site_logo": "img/PolySaaS-Industrial-Logo.png",
    # "site_icon": "img/favicon.ico",
    # Example: set a custom color theme
    "PRIMARY_COLOR": "#007bff",
    "SECONDARY_COLOR": "#6c757d",
     "topmenu_links": [
        # PolySaaS Logo icon - bigger with fa-lg
        {"name": "PolySaaS", "url": "/admin/", "permissions": ["auth.view_user"], "icon": "fas fa-gem fa-lg"},

        # Url that gets reversed (Permissions can be added)
        {"name": "Home",  "url": "/dose/", "permissions": ["auth.view_user"]},

        # external url that opens in a new window (Permissions can be added)
        {"name": "Support", "url": "https://github.com/farridav/django-jazzmin/issues", "new_window": True},

        {"name": "Toggle light/dark", "url": "/admin/select-theme/", "permissions": ["auth.view_user"]},

        {"name": "API Docs", "url": "/swagger/", "new_window": True, "icon": "fas fa-book"},
        {"name": "Platform help", "url": "/help/", "permissions": ["auth.view_user"], "icon": "fas fa-life-ring"},
    ],
    "usermenu_links": [
        {"name": "My Profile",  "url": "/profile/", "icon": "fas fa-user"},
        {"name": "Toggle Theme", "url": "javascript:void(0)", "icon": "fas fa-moon"},
        {"name": "Settings", "url": "/settings/", "icon": "fas fa-cog"},
        {"name": "Logout", "url": "/accounts/logout/", "icon": "fas fa-sign-out-alt"},
        {"name": "Help", "url": "/help/", "icon": "fas fa-question-circle"},

    ],
    "custom_css": "admin/css/theme-toggle.css",
    "custom_js": "admin/js/theme-toggle.js",
    # Removed "order" list to show all registered apps in sidebar
    "icons": {
        "alerts.notifications": "fas fa-bell",  # Notifications
        "parameters.parameter": "fas fa-sliders-h",  # Parameters
        "auth.user": "fas fa-user",  # Users
        "auth.group": "fas fa-users",  # Groups
        "dose.atomicservice": "fas fa-cogs",  # AtomicService
        "dose.deepseekprompt": "fas fa-robot",  # DeepSeekPrompt
        "dose.userprofile": "fas fa-id-badge",  # UserProfile
        "dose.task": "fas fa-tasks",  # Task
        "dose.instruction": "fas fa-book",  # Instruction
        "dose.callbackdata": "fas fa-sync",  # CallBackData
        "dose.mlengine": "fas fa-brain",  # MLEngine
        "dose.passthroughendpoint": "fas fa-share-square",  # PassThroughEndpoint
        "dose.dosemessage": "fas fa-envelope",  # DoseMessage
        "dose.requestlog": "fas fa-file-alt",  # RequestLog
        "dose.errorlog": "fas fa-exclamation-triangle",  # ErrorLog
        "dose.tenant": "fas fa-building",  # Tenant
        "dose.mltaxonomy": "fas fa-project-diagram",  # MLTaxonomy
        "dose.mldataset": "fas fa-database",  # MLDataset
        "dose.mlprompt": "fas fa-comment-dots",  # MLPrompt
        "dose.navigationpanel": "fas fa-th-large",  # NavigationPanel
        "dose.navigationitem": "fas fa-link",  # NavigationItem
    "dose.dashboardbutton": "fas fa-chart-line",  # DashboardButton (graph)
    "dose.ignorepath": "fas fa-ban",  # IgnorePath
    "sites.site": "fas fa-building",  # Sites
    "socialaccount.socialaccount": "fab fa-google",  # Social Accounts (Google)
    "socialaccount.socialtoken": "fas fa-cookie",  # Social Tokens (Cookie)
    "socialaccount.socialapp": "fab fa-facebook",  # Social Applications (Facebook)
    "account.emailaddress": "fas fa-envelope",  # Email Addresses
        # Machine Learning Studio icons
        "ml_studio.mlengineproxy": "fas fa-brain",
        "ml_studio.mltaxonomyproxy": "fas fa-project-diagram",
        "ml_studio.mldatasetproxy": "fas fa-database",
        "ml_studio.mlpromptproxy": "fas fa-robot",
    },
    # Hide original ML models from Dose app - they now appear in Machine Learning Studio
    "hide_models": [
        "dose.mlengine",
        "dose.mltaxonomy",
        "dose.mldataset",
        "dose.deepseekprompt",
        "dose.mlprompt",
    ],
    # Hide entire apps that should not be visible in the tenant admin interface
    "hide_apps": ["djstripe"],
}

# Jazzmin 3 reads this (not JAZZMIN_SETTINGS["ui_tweaks"] template strings).
JAZZMIN_UI_TWEAKS = {
    "theme": "flatly",
    "navbar": "navbar-white border-bottom",
    "accent": "accent-primary",
    "sidebar_nav_child_indent": True,
    "sidebar_nav_compact_style": True,
}

# --- STRIPE CONFIGURATION ---
STRIPE_SECRET_KEY = env('STRIPE_SECRET_KEY', default='')
STRIPE_PUBLISHABLE_KEY = env('STRIPE_PUBLISHABLE_KEY', default='')
STRIPE_WEBHOOK_SECRET = env('STRIPE_WEBHOOK_SECRET', default='')

STRIPE_PRICE_ID = env('STRIPE_PRICE_ID', default='')
STRIPE_TRIAL_PERIOD_DAYS = 14

STRIPE_PRICE_IDS = {
    'polysaas-1': env('STRIPE_PRICE_ID_POLYSAAS_1', default=STRIPE_PRICE_ID),
    'polysaas-3': env('STRIPE_PRICE_ID_POLYSAAS_3', default=''),
    'polysaas-unlimited': env('STRIPE_PRICE_ID_POLYSAAS_UNLIMITED', default=''),
}

# Per-user/month price for each plan (display only — actual billing is in Stripe)
PLAN_PRICES = {
    'polysaas-1': 26.00,
    'polysaas-3': 49.00,
    'polysaas-unlimited': 99.00,
}

# Max bundled or external applications per plan (counted in "slots" below)
PLAN_MAX_APPS = {
    'polysaas-1': 1,
    'polysaas-3': 3,
    'polysaas-unlimited': None,
}

# Subscribe form keys: WordPress & PolySysMon each consume 2 slots toward PLAN_MAX_APPS
PLAN_BUNDLED_APP_SLOTS = {
    'enable_wordpress': 2,
    'enable_polysysmon': 2,
}

# TenantApp.app_name values: same weights for in-product limits
TENANT_APP_BUNDLED_SLOTS = {
    'wordpress': 2,
    'polysysmon': 2,
}

# Usage-based storage pricing (NextCloud / WordPress) — metered in Stripe
STRIPE_PRICE_ID_STORAGE = env('STRIPE_PRICE_ID_STORAGE', default='')

SUBSCRIPTION_AMOUNT = 26.00

# --- dj-stripe configuration ---
STRIPE_LIVE_SECRET_KEY = env('STRIPE_LIVE_SECRET_KEY', default='')
STRIPE_TEST_SECRET_KEY = env('STRIPE_TEST_SECRET_KEY', default=STRIPE_SECRET_KEY)
STRIPE_LIVE_MODE = env.bool('STRIPE_LIVE_MODE', default=False)
DJSTRIPE_WEBHOOK_SECRET = env('STRIPE_WEBHOOK_SECRET', default='')
DJSTRIPE_USE_NATIVE_JSONFIELD = True
DJSTRIPE_FOREIGN_KEY_TO_FIELD = "id"

# When True, superusers must satisfy UserTenantMembership + role like normal users.
STRICT_TENANT_ENFORCEMENT = env.bool('STRICT_TENANT_ENFORCEMENT', default=False)

# --- AI as Peers (Mattermost bot integration) ---
MATTERMOST_URL = sm('mattermost-url', 'MATTERMOST_URL', 'http://localhost:8065')
MATTERMOST_ADMIN_TOKEN = sm('MATTERMOST_ADMIN_TOKEN', 'MATTERMOST_ADMIN_TOKEN') or sm('mattermost-admin-token', 'MATTERMOST_ADMIN_TOKEN')
POLYSAAS_APP_ADMIN_PASSWORD = sm('polysaas-app-admin-password', 'POLYSAAS_APP_ADMIN_PASSWORD', 'PolySaaS2026!')
MATTERMOST_PASSTHROUGH_SECRET = sm('mattermost-passthrough-secret', 'MATTERMOST_PASSTHROUGH_SECRET', '')

# --- Shared Odoo instance (used by odoo_tenant_provisioner, OdooCustomerSync, etc.) ---
ODOO_SHARED_URL = sm('odoo-shared-url', 'ODOO_SHARED_URL', 'https://polysaas-odoo2.onrender.com')
ODOO_SHARED_DB = sm('odoo-shared-db', 'ODOO_SHARED_DB', 'odoodb')
ODOO_SHARED_ADMIN_LOGIN = sm('odoo-shared-admin-login', 'ODOO_SHARED_ADMIN_LOGIN', 'odooAdmin')

# --- Shared Nextcloud instance (used by nextcloud_tenant_provisioner) ---
NEXTCLOUD_SHARED_URL = env('NEXTCLOUD_SHARED_URL', default='https://polysaas-nextcloud.onrender.com')
NEXTCLOUD_SHARED_ADMIN_LOGIN = env('NEXTCLOUD_SHARED_ADMIN_LOGIN', default='ncadmin')

# Optional Fernet key (ASCII, from Fernet.generate_key()) for parameters.Parameter.encrypted_payload.
# If unset, a key is derived from DJANGO_SECRET_KEY (rotating SECRET_KEY invalidates stored secrets).
PARAMETER_FERNET_KEY = env('PARAMETER_FERNET_KEY', default='')
ANTHROPIC_API_KEY = sm('anthropic-api-key', 'ANTHROPIC_API_KEY')
XAI_API_KEY = sm('XAI_API_KEY', 'XAI_API_KEY')
GEMINI_API_KEY = sm('GEMINI_API_KEY', 'GEMINI_API_KEY')
GITHUB_REPO = env('GITHUB_REPO', default='mikeoliveraz2/PolySaaS')
GITHUB_TOKEN = sm('github-token', 'GITHUB_TOKEN') or sm('GITHUB_API_TOKEN', 'GITHUB_API_TOKEN')
AI_PEER_PROVIDER_GITHUB = env('AI_PEER_PROVIDER_GITHUB', default='anthropic')
AI_PEER_PROVIDER_COPILOT = env('AI_PEER_PROVIDER_COPILOT', default='anthropic')
AI_PEER_PROVIDER_CURSOR = env('AI_PEER_PROVIDER_CURSOR', default='anthropic')
AI_PEER_PROVIDER_GROK = env('AI_PEER_PROVIDER_GROK', default='xai')
AI_PEER_PROVIDER_ROUTER = env('AI_PEER_PROVIDER_ROUTER', default='anthropic')
AI_PEER_PROVIDER_OPENCLAW = env('AI_PEER_PROVIDER_OPENCLAW', default='anthropic')
AI_PEER_PROVIDER_GEM = env('AI_PEER_PROVIDER_GEM', default='gemini')
BOT_TOKEN_GITHUB = sm('bot-token-github', 'BOT_TOKEN_GITHUB')
BOT_TOKEN_COPILOT = sm('bot-token-copilot', 'BOT_TOKEN_COPILOT')
BOT_TOKEN_CURSOR = sm('bot-token-cursor', 'BOT_TOKEN_CURSOR')
BOT_TOKEN_GROK = sm('bot-token-grok', 'BOT_TOKEN_GROK')
BOT_TOKEN_ROUTER = sm('bot-token-router', 'BOT_TOKEN_ROUTER')
BOT_TOKEN_OPENCLAW = sm('bot-token-openclaw', 'BOT_TOKEN_OPENCLAW')
BOT_TOKEN_CC = sm('bot-token-cc', 'BOT_TOKEN_CC')
BOT_TOKEN_SUPERGROK = sm('bot-token-supergrok', 'BOT_TOKEN_SUPERGROK')
BOT_TOKEN_GEM = sm('bot-token-gem', 'BOT_TOKEN_GEM')
BOT_TOKEN_GEMINI = sm('bot-token-gemini', 'BOT_TOKEN_GEMINI') or BOT_TOKEN_GEM
BOT_TOKEN_WINDSURF = sm('bot-token-windsurf', 'BOT_TOKEN_WINDSURF')
AI_PEERS_WEBHOOK_TOKEN = sm('ai-peers-webhook-token', 'AI_PEERS_WEBHOOK_TOKEN')
# Recent posts fetched for LLM context (Option 1). Pinned posts are merged into system prompt (Option 2).
AI_PEERS_CHANNEL_MESSAGE_LIMIT = env.int('AI_PEERS_CHANNEL_MESSAGE_LIMIT', default=75)

# --- LLM Router (OpenClaw-style in-process, Option 1) ---
# Used by orchestration, ML Studio, DoseAI, and Peers — classifies prompts and picks provider/model.
LLM_ROUTER_ENABLED = env.bool("LLM_ROUTER_ENABLED", default=True)
LLM_ROUTER_DEFAULT_USER_TIER = env("LLM_ROUTER_DEFAULT_USER_TIER", default="standard")
LLM_ROUTER_LOG_FULL_PROMPT = env.bool("LLM_ROUTER_LOG_FULL_PROMPT", default=False)
LLM_ROUTER_LOG_PROMPT_MAX_CHARS = env.int("LLM_ROUTER_LOG_PROMPT_MAX_CHARS", default=200)
LLM_ROUTER_LITE_PROVIDER = env("LLM_ROUTER_LITE_PROVIDER", default="anthropic")
LLM_ROUTER_LITE_MODEL = env("LLM_ROUTER_LITE_MODEL", default="claude-3-5-haiku-20241022")
LLM_ROUTER_STANDARD_PROVIDER = env("LLM_ROUTER_STANDARD_PROVIDER", default="anthropic")
LLM_ROUTER_STANDARD_MODEL = env("LLM_ROUTER_STANDARD_MODEL", default="claude-sonnet-4-6")
LLM_ROUTER_HEAVY_PROVIDER = env("LLM_ROUTER_HEAVY_PROVIDER", default="anthropic")
LLM_ROUTER_HEAVY_MODEL = env("LLM_ROUTER_HEAVY_MODEL", default="claude-sonnet-4-6")
# Phase 1: extra system text for staff PolySaaS AI admin chat (after platform link block).
LLM_ROUTER_ADMIN_BASE_SYSTEM_PROMPT = env.str("LLM_ROUTER_ADMIN_BASE_SYSTEM_PROMPT", default="").strip()
# Phase 2: tenant MLPrompt.key — refine (two-step LLM) or inject (single-call) for admin chat.
LLM_ROUTER_ML_STUDIO_REFINE_KEY = env("LLM_ROUTER_ML_STUDIO_REFINE_KEY", default="polysaas_admin_chat_refine")
LLM_ROUTER_ML_STUDIO_REFINE_USE_LLM = env.bool("LLM_ROUTER_ML_STUDIO_REFINE_USE_LLM", default=True)
# Optional JSON map for log hints only, e.g. {"anthropic:claude-3-5-haiku-20241022": 0.25}
_llm_cost_raw = env.str("LLM_ROUTER_COST_HINTS_USD_PER_1K", default="").strip()
if _llm_cost_raw:
    try:
        LLM_ROUTER_COST_HINTS_USD_PER_1K = json.loads(_llm_cost_raw)
        if not isinstance(LLM_ROUTER_COST_HINTS_USD_PER_1K, dict):
            LLM_ROUTER_COST_HINTS_USD_PER_1K = {}
    except json.JSONDecodeError:
        LLM_ROUTER_COST_HINTS_USD_PER_1K = {}
else:
    LLM_ROUTER_COST_HINTS_USD_PER_1K = {}

# --- SESSION SETTINGS ---
SESSION_ENGINE = 'django.contrib.sessions.backends.file'
SESSION_COOKIE_AGE = 86400  # 1 day in seconds
SESSION_SAVE_EVERY_REQUEST = False
SESSION_EXPIRE_AT_BROWSER_CLOSE = False
# Log session settings at startup
import logging
logging.info(f"SESSION_ENGINE: {SESSION_ENGINE}, SESSION_COOKIE_AGE: {SESSION_COOKIE_AGE}, SESSION_SAVE_EVERY_REQUEST: {SESSION_SAVE_EVERY_REQUEST}")


# settings.py
if DEBUG:                     # ← your .env probably sets DEBUG=True already
    ALLOWED_HOSTS = ['*']     # ← this is the missing line for dev
else:
    ALLOWED_HOSTS = [
        '127.0.0.1',
        'localhost',
        '.poly-saas.local',
        'production.polysaas.online',
        'polysaas-core.onrender.com',
        '.onrender.com',
        '.polysaas.online',
    ]

SITE_ID = 1

INSTALLED_APPS = [
    'jazzmin',  # Jazzmin admin theme
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django_celery_beat',
    'django_celery_results',
    'django.contrib.sites',  # Required for allauth
    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    'allauth.socialaccount.providers.github',
    'allauth.socialaccount.providers.google',  # PATCHED: Enable Google OAuth2
    'rest_framework',
    'dose.apps.DoseConfig',
    'llm_router.apps.LlmRouterConfig',  # In-process LLM routing (OpenClaw-style Option 1)
    'ml_studio',  # Machine Learning Studio - grouped ML models
    'parameters.apps.ParametersConfig',
    'alerts.apps.AlertsConfig',
    'drf_yasg',
    'easy_thumbnails',
    'corsheaders',
    'django_extensions',  # For ERD generation
    'oauth2_provider',    # Django OAuth Toolkit — OIDC provider for SSO
    'djstripe',           # dj-stripe — Stripe models, webhooks, sync
    'dose.polysniffer',   # PolySniffer — traffic capture for orchestration mapping
]

# Filter out apps that cannot be imported (helps when files are missing or
# OneDrive placeholders prevent file reads). This prevents Django from
# failing to start when some local apps are temporarily unavailable.
def _filter_installed_apps(apps):
    valid = []
    for a in apps:
        # import top-level module for the app entry
        module_name = a.split('.')[0]
        try:
            importlib.import_module(module_name)
            valid.append(a)
        except Exception:
            # don't raise here — just skip the missing app
            print(f"Skipping unavailable INSTALLED_APPS entry: {a}")
    return valid

INSTALLED_APPS = _filter_installed_apps(INSTALLED_APPS)
_oauth2_available = 'oauth2_provider' in INSTALLED_APPS

# `active_urls` removed from `INSTALLED_APPS` per user request.
# Django Allauth settings for OAuth2 SSO
SITE_ID = 1
AUTHENTICATION_BACKENDS = [
    'mysite.auth_backends_allauth.AllauthCaseInsensitiveBackend',
    'django.contrib.auth.backends.ModelBackend',
]

LOGIN_REDIRECT_URL = '/'
ACCOUNT_LOGOUT_REDIRECT_URL = '/'

# Staff default redirect: / would go to dose landing; CustomAccountAdapter sends staff to /admin/
ACCOUNT_ADAPTER = 'dose.account_adapter.CustomAccountAdapter'

# Comma-separated emails (e.g. you@domain.com): Google sign-in sets is_staff + is_superuser. Empty = off.
POLYSAAS_SUPERUSER_EMAILS = [
    x.strip().lower()
    for x in env('POLYSAAS_SUPERUSER_EMAILS', default='').split(',')
    if x.strip()
]

# Custom adapter to handle OAuth return URLs
SOCIALACCOUNT_ADAPTER = 'dose.adapters.CustomSocialAccountAdapter'

# Modern Allauth settings for email-only login and social signup
# Using new format instead of deprecated ACCOUNT_AUTHENTICATION_METHOD
ACCOUNT_USER_MODEL_USERNAME_FIELD = 'username'  # Django's default User model uses 'username'
ACCOUNT_LOGIN_METHODS = {'email', 'username'}
ACCOUNT_SIGNUP_FIELDS = ['email*']
ACCOUNT_EMAIL_VERIFICATION = "none"  # or "optional" if you want to allow immediate login
SOCIALACCOUNT_AUTO_SIGNUP = True
SOCIALACCOUNT_STORE_TOKENS = True  # Enable OAuth token storage for API access
SOCIALACCOUNT_EMAIL_AUTHENTICATION = True
SOCIALACCOUNT_EMAIL_AUTHENTICATION_AUTO_CONNECT = True


# Allow automatic linking of social accounts to existing users with same email
SOCIALACCOUNT_EMAIL_AUTHENTICATION = True
SOCIALACCOUNT_EMAIL_AUTHENTICATION_AUTO_CONNECT = True


# Ensure Allauth uses the custom login template
ACCOUNT_LOGIN_TEMPLATE = "account/login.html"

SOCIALACCOUNT_PROVIDERS = {
    'github': {
        'SCOPE': [
            'user',
            'repo',
        ],
        # Changed GitHub OAuth access_type from 'online' to 'offline'. This enables refresh tokens which should be securely stored and managed.
        # Ensure proper token lifecycle management is implemented.
        'AUTH_PARAMS': {'access_type': 'offline'},
    },
    'google': {
        'SCOPE': [
            'openid',
            'profile',
            'email',
            'https://www.googleapis.com/auth/gmail.readonly',
            # WARNING: The following scope allows sending emails on behalf of users.
            # Only request this if absolutely necessary and inform users explicitly.
            'https://www.googleapis.com/auth/gmail.send',
        ],

        'AUTH_PARAMS': {
            'access_type': 'offline',
            'prompt': 'consent'  # Force consent screen to ensure refresh token is returned
        },
    },
    # 'facebook': {
    #     'METHOD': 'oauth2',
    #     'SCOPE': ['email', 'public_profile'],
    #     'FIELDS': [
    #         'id',
    #         'email',
    #         'name',
    #         'first_name',
    #         'last_name',
    #         'picture',
    #     ],
    #     'AUTH_PARAMS': {'auth_type': 'rerequest'},
    # },
}

# --- OAuth2 / OIDC Provider (django-oauth-toolkit) ---
# PolySaaS acts as the central OIDC Identity Provider for Mattermost, Odoo, Nextcloud.
_oidc_key_path = os.path.join(BASE_DIR, 'oidc_rsa_key.pem')
_OIDC_RSA_PRIVATE_KEY = ''
if os.path.exists(_oidc_key_path):
    with open(_oidc_key_path, 'r') as _f:
        _OIDC_RSA_PRIVATE_KEY = _f.read()

OAUTH2_PROVIDER_APPLICATION_MODEL = 'oauth2_provider.Application'
OAUTH2_PROVIDER_ACCESS_TOKEN_MODEL = 'oauth2_provider.AccessToken'
OAUTH2_PROVIDER_REFRESH_TOKEN_MODEL = 'oauth2_provider.RefreshToken'
OAUTH2_PROVIDER_ID_TOKEN_MODEL = 'oauth2_provider.IDToken'
OAUTH2_PROVIDER_GRANT_MODEL = 'oauth2_provider.Grant'

OAUTH2_PROVIDER = {
    'OIDC_ENABLED': True,
    'OIDC_RSA_PRIVATE_KEY': _OIDC_RSA_PRIVATE_KEY,
    'OIDC_ISS_ENDPOINT': os.environ.get('OIDC_ISS_ENDPOINT', 'http://host.docker.internal:8000/o'),
    'SCOPES': {
        'openid': 'OpenID Connect',
        'email': 'Email address',
        'profile': 'User profile',
        'tenant': 'Tenant information',
    },
    'DEFAULT_SCOPES': ['openid', 'email', 'profile'],
    'OAUTH2_VALIDATOR_CLASS': 'dose.oauth.TenantAwareValidator',
    'ACCESS_TOKEN_EXPIRE_SECONDS': 3600,
    'REFRESH_TOKEN_EXPIRE_SECONDS': 86400,
    'PKCE_REQUIRED': False,
    'ALLOWED_REDIRECT_URI_SCHEMES': ['https', 'http'],
}

# --- Passthrough Auth (POL-2) ---
# 'header' = simple HTTP headers (REMOTE_USER, X-User-Email, etc.)
# 'jwt'    = signed JWT in Authorization: Bearer header (uses OIDC RSA key if available)
PASSTHROUGH_AUTH_MODE = 'header'
PASSTHROUGH_JWT_EXPIRY = 300  # seconds (5 minutes) — only used in jwt mode

# Django settings for mysite project.

# Generated by 'django-admin startproject' using Django 2.1.

# For more information on this file, see
# https://docs.djangoproject.com/en/2.1/topics/settings/

# For the full list of settings and their values, see
# https://docs.djangoproject.com/en/2.1/ref/settings/

import os

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'mysite.debug_session_middleware.DebugSessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'mysite.csrf_exemption_middleware.CSRFExemptionMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'mysite.middleware.user_request_tracking.UserRequestTrackingMiddleware',
    'dose.debug_middleware.DebugRequestMiddleware',
    'dose.middleware.admin_unauthorized.AdminUnauthorizedMiddleware',
    'mysite.admin_tenant_session_middleware.AdminTenantSessionMiddleware',
    'mysite.tenant_context_middleware.TenantContextMiddleware',
    'dose.polysniffer.middleware.PolySnifferMiddleware',
    'mysite.session_tenant_middleware.SessionTenantMiddleware',
    'dose.doserequestcontroller.DoseRequestController',
    'dose.middleware.jazzmin_tenant_theme.JazzminTenantThemeMiddleware',
    'dose.doseresponsecontroller.DoseResponseController',
    'dose.middleware.passthrough_auth.PassthroughAuthMiddleware',
    # CRITICAL: ExternalPassthroughMiddleware must run BEFORE CsrfViewMiddleware
    # so it can return a response before CSRF validation occurs
    'dose.passthrough.middleware.ExternalPassthroughMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'mysite.admin_status_banner_middleware.AdminStatusBannerMiddleware',
    'allauth.account.middleware.AccountMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]
if _oauth2_available:
    MIDDLEWARE.insert(
        MIDDLEWARE.index('django.contrib.auth.middleware.AuthenticationMiddleware') + 1,
        'oauth2_provider.middleware.OAuth2TokenMiddleware',
    )

if ADMIN_INDEX_DIAG:
    MIDDLEWARE.append("mysite.admin_index_diag.AdminIndexDiagMiddleware")

ROOT_URLCONF = 'mysite.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [
            os.path.join(BASE_DIR, 'dose', 'templates'),
            os.path.join(BASE_DIR, 'templates'),
        ],
        # NOTE: APP_DIRS is mutually exclusive with explicit `loaders` (below). We use explicit
        # uncached loaders to bypass Django's auto-applied cached.Loader (active when DEBUG=False).
        # The cached.Loader has been observed to mis-resolve {{ block.super }} on multi-level
        # template inheritance (model change_form -> jazzmin/change_form -> dose/base_site ->
        # jazzmin/base) on production, producing empty page_content output for change_form views
        # while change_list (simpler inheritance) renders fine. Same code works on dev because
        # dev runs with DEBUG=True which doesn't apply cached.Loader.
        'OPTIONS': {
            'loaders': [
                'django.template.loaders.filesystem.Loader',
                'django.template.loaders.app_directories.Loader',
            ],
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'mysite.custom_context_processors.tenant_theme_context',
                'dose.context_processors.tenant_context',
                'mysite.context_processors.unread_notifications_count',
                'dose.context_processors.jazzmin_theme',
                    'dose.context_processors.jazzmin_ui_tweaks',
                'dose.context_processors.admin_active_urls',
                'dose.context_processors.admin_navigation',
            ],
        },
    },
]

WSGI_APPLICATION = 'mysite.wsgi.application'
ASGI_APPLICATION = 'mysite.asgi.application'


# Database
# https://docs.djangoproject.com/en/2.1/ref/settings/#databases


DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': env('DB_NAME', default='dosedbsaas'),
        'USER': env('DB_USER', default='dosedbadmin'),
        'PASSWORD': env('DOSE_DB_PASSWORD', default='PolySaaS2026!'),
        'HOST': env('DB_HOST', default='localhost'),
        'PORT': env('DB_PORT', default='5433'),
    }
}


# Password validation
# https://docs.djangoproject.com/en/2.1/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Google OAuth2 settings
# Client ID and Client Secret should be set via environment variables for security.
# Example:
# GOOGLE_OAUTH2_CLIENT_ID = os.environ.get("GOOGLE_OAUTH2_CLIENT_ID")
# GOOGLE_OAUTH2_CLIENT_SECRET = os.environ.get("GOOGLE_OAUTH2_CLIENT_SECRET")
# GOOGLE_OAUTH2_CLIENT_ID = os.environ.get("GOOGLE_OAUTH2_CLIENT_ID")
# GOOGLE_OAUTH2_CLIENT_SECRET = os.environ.get("GOOGLE_OAUTH2_CLIENT_SECRET")

# Internationalization
# https://docs.djangoproject.com/en/2.1/topics/i18n/

# DEEPSEEK API KEY should be set via environment variable for security.
DEEPSEEK_API_KEY = os.environ.get("DEEPSEEK_API_KEY", "")
#DEEPSEEK API KEY:sk-f3130e89988f405c9937cd6ccc350851
DEEPSEEK_API_KEY = "sk-f3130e89988f405c9937cd6ccc350851"

# --- Mattermost AI Peers Bot ---
MATTERMOST_BOT_TOKEN = sm('mattermost-bot-token', 'MATTERMOST_BOT_TOKEN')

# Per-peer Mattermost bot account tokens (each bot posts under its own identity)
BOT_TOKEN_SUPERGROK = sm('bot-token-supergrok', 'BOT_TOKEN_SUPERGROK')  # @supergrok (Grok / xAI)
BOT_TOKEN_GEM = sm('bot-token-gem', 'BOT_TOKEN_GEM')                    # @gem (Gemini / Google)
BOT_TOKEN_CC = sm('bot-token-cc', 'BOT_TOKEN_CC')                       # @cc (Cursor Claude / Anthropic)
BOT_TOKEN_WSC = sm('bot-token-wsc', 'BOT_TOKEN_WSC')                    # @wsc (Windsurf Claude)
BOT_TOKEN_KIMI = sm('bot-token-kimi', 'BOT_TOKEN_KIMI')                 # @kimi (Moonshot Kimi)

# LLM API keys (deduplicated — primary assignments are above at line ~220)
WINDSURF_API_KEY = sm('windsurf-api-key', 'WINDSURF_API_KEY')
KIMI_API_KEY = sm('kimi-api-key', 'KIMI_API_KEY')

TIME_ZONE = 'Asia/Manila'

USE_I18N = True

USE_L10N = True

USE_TZ = True

CSRF_TRUSTED_ORIGINS = [
    "http://localhost:8000",
    "http://localhost:444",
    "https://production.polysaas.online",
    "https://polysaas-core.onrender.com",
]
#CSRF_COOKIE_DOMAIN = '.localhost'

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/2.1/howto/static-files/


STATIC_URL = '/static/'
STATIC_ROOT = 'var/static_root/'
STATICFILES_DIRS = ['static']

# Media files for tenant logos
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

CORS_ALLOW_ALL_ORIGINS = True

CORS_ALLOWED_ORIGINS = [
"http://localhost:8000",
"http://127.0.0.1:8000",
"http://localhost:444",
"http://127.0.0.1:444"
]

MESSAGE_STORAGE = 'django.contrib.messages.storage.cookie.CookieStorage'

DEFAULT_AUTO_FIELD = 'django.db.models.AutoField'

REST_FRAMEWORK = { 'DEFAULT_SCHEMA_CLASS': 'rest_framework.schemas.coreapi.AutoSchema' }



CELERY_BEAT_SCHEDULER = 'django_celery_beat.schedulers:DatabaseScheduler'

# Celery Broker - RabbitMQ
CELERY_BROKER_URL = 'amqp://guest:guest@localhost'
# Celery Configuration Options
CELERY_TASK_TRACK_STARTED = True
CELERY_TASK_TIME_LIMIT = 30 * 60
CELERY_CACHE_BACKEND = 'django-cache'
CELERY_ACCEPT_CONTENT = ['application/json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_RESULT_BACKEND = 'django-db'
CELERY_TIMEZONE = "Asia/Shanghai"
CELERY_BEAT_SCHEDULER = 'django_celery_beat.schedulers:DatabaseScheduler'

#notes  beat is started with celery -A mysite beat -l INFO
# celery is started with celery -A mysite worker -l INFO --pool=gevent -n worker4

# SMTP Settings
EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_USE_TLS = True
EMAIL_HOST = "smtp.gmail.com"
EMAIL_PORT = 587
EMAIL_HOST_USER ='mo.gsssol@gmail.com'
EMAIL_HOST_PASSWORD = os.environ.get("EMAIL_HOST_PASSWORD")
DEFAULT_FROM_EMAIL = 'Dose2 <mo.gsssol@gmail.com>'

# LOGGING configuration
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'mm_simple': {
            'format': '%(asctime)s %(message)s',
            'datefmt': '%H:%M:%S',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
        'file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': './debug.log',
        },
        'info_file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': './info.log',
        },
        'mm_debug_file': {
            'level': 'DEBUG',
            'class': 'logging.FileHandler',
            'filename': './mm_debug.log',
            'formatter': 'mm_simple',
        },
    },
    'loggers': {
        'mm_debug': {
            'handlers': ['mm_debug_file', 'console'],
            'level': 'DEBUG',
            'propagate': False,
        },
        'django': {
            'handlers': ['console', 'file', 'info_file'],
            'level': 'INFO',
            'propagate': True,
        },
        'dose': {
            'handlers': ['console', 'file', 'info_file'],
            'level': 'INFO',
            'propagate': True,
        },
        'django.contrib.auth': {
            'handlers': ['console'],
            'level': 'DEBUG',
        },
        'allauth.account': {
            'handlers': ['console'],
            'level': 'DEBUG',
        },
    },
    'root': {
        'handlers': ['console', 'file', 'info_file'],
        'level': 'INFO',
    },
}

# Only keep the first LOGGING config above, which defines all handlers and loggers.
# Custom user session settings

# =============================================
# SECURITY - PROXY SETTINGS (Traefik + Render)
# =============================================

# Critical when running behind Traefik / Render
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
USE_X_FORWARDED_HOST = True
USE_X_FORWARDED_PORT = True

# Let Traefik handle HTTPS redirects (disable Django redirect)
SECURE_SSL_REDIRECT = False
SECURE_REDIRECT_EXEMPT = [r'^.*']

# Disable HSTS while debugging the redirect loop
SECURE_HSTS_SECONDS = 0
SECURE_HSTS_INCLUDE_SUBDOMAINS = False
SECURE_HSTS_PRELOAD = False


