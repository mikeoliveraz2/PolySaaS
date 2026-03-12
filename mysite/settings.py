# DO NOT MODIFY: Critical system file. Ask before making changes.
# Stripe price ID for subscriptions (replace with your actual Stripe price ID)

import environ
import os
import importlib
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
env = environ.Env()
#environ.Env.read_env()  # This loads .env file
env.read_env(os.path.join(BASE_DIR, '.env'))
print("Loaded .env:", env('DJANGO_SECRET_KEY', default='NOT FOUND'))
SECRET_KEY = env('DJANGO_SECRET_KEY')
DEBUG = True
# Jazzmin admin theme settings (customize as needed)
JAZZMIN_SETTINGS = {
    "custom_links": {},
    "SITE_TITLE": "Dose Admin",
    "SITE_HEADER": '<img src="/static/img/PolySaaS-Industrial-Logo.png" style="height: 50px; margin-right: 10px; vertical-align: middle;" alt="PolySaaS"/> Dose Admin Portal',
    "SITE_BRAND": "PolySaaS",
    "WELCOME_SIGN": "Welcome to DoseSaaS Admin",
    "copyright": "DoseSaaS 2025",
    "show_ui_builder": True,
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

        # NOTE: OSTicket link dynamically added by JazzminTenantThemeMiddleware per tenant
        # DO NOT ADD STATIC OSTICKET LINK HERE

        # external url that opens in a new window (Permissions can be added)
        {"name": "Support", "url": "https://github.com/farridav/django-jazzmin/issues", "new_window": True},

        {"name": "Toggle light/dark", "url": "/admin/select-theme/", "permissions": ["auth.view_user"]},

        {"name": "API Docs", "url": "/swagger/", "new_window": True, "icon": "fas fa-book"},
    ],
    "usermenu_links": [
        {"name": "My Profile",  "url": "/profile/", "icon": "fas fa-user"},
        {"name": "Toggle Theme", "url": "javascript:void(0)", "icon": "fas fa-moon"},
        {"name": "Settings", "url": "/settings/", "icon": "fas fa-cog"},
        {"name": "Logout", "url": "/accounts/logout/", "icon": "fas fa-sign-out-alt"},
        {"name": "Help", "url": "/help/", "icon": "fas fa-question-circle"},

    ],
    "ui_tweaks": {
        "theme": "{{ JAZZMIN_UI_TWEAKS.theme }}",
        "dark_mode_theme": "{{ JAZZMIN_UI_TWEAKS.dark_mode_theme }}",
    },
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
        "dose.navigationpanel": "fas fa-th-large",  # NavigationPanel
        "dose.navigationitem": "fas fa-link",  # NavigationItem
    "dose.dashboardbutton": "fas fa-chart-line",  # DashboardButton (graph)
    "dose.ignorepath": "fas fa-ban",  # IgnorePath
    "sites.site": "fas fa-building",  # Sites
    "socialaccount.socialaccount": "fab fa-google",  # Social Accounts (Google)
    "socialaccount.socialtoken": "fas fa-cookie",  # Social Tokens (Cookie)
    "socialaccount.socialapp": "fab fa-facebook",  # Social Applications (Facebook)
    "account.emailaddress": "fas fa-envelope",  # Email Addresses
    },
}

STRIPE_PRICE_ID = 'price_1S5faDPQWnaGoDqywwIEPGUA'
# Subscription price in USD per month
SUBSCRIPTION_AMOUNT = 29.99
# Free trial period in days
STRIPE_TRIAL_PERIOD_DAYS = 14

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
    ALLOWED_HOSTS = ['127.0.0.1', 'localhost', '.poly-saas.local', 'yourdomain.com']

SITE_ID = 1

INSTALLED_APPS = [
    'jazzmin',  # Jazzmin admin theme
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.sites',  # Required for allauth
    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    'allauth.socialaccount.providers.github',
    'allauth.socialaccount.providers.google',  # PATCHED: Enable Google OAuth2
    'rest_framework',
    'dose.apps.DoseConfig',
    'parameters.apps.ParametersConfig',
    'alerts.apps.AlertsConfig',
    'drf_yasg',
    'easy_thumbnails',
    'corsheaders',
    'django_extensions',  # For ERD generation
    'oauth2_provider',    # Django OAuth Toolkit — OIDC provider for SSO
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
AUTHENTICATION_BACKENDS = (
    ('oauth2_provider.backends.OAuth2Backend', 'django.contrib.auth.backends.ModelBackend', 'allauth.account.auth_backends.AuthenticationBackend')
    if _oauth2_available else
    ('django.contrib.auth.backends.ModelBackend', 'allauth.account.auth_backends.AuthenticationBackend')
)

LOGIN_REDIRECT_URL = '/'
ACCOUNT_LOGOUT_REDIRECT_URL = '/'

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
    'OIDC_ISS_ENDPOINT': 'http://localhost:8000/o',
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
    'mysite.middleware.user_request_tracking.UserRequestTrackingMiddleware',
    'dose.debug_middleware.DebugRequestMiddleware',
    'dose.middleware.admin_unauthorized.AdminUnauthorizedMiddleware',
    'mysite.admin_tenant_session_middleware.AdminTenantSessionMiddleware',
    'mysite.session_tenant_middleware.SessionTenantMiddleware',
    'dose.doserequestcontroller.DoseRequestController',
    'dose.middleware.jazzmin_tenant_theme.JazzminTenantThemeMiddleware',
    'dose.doseresponsecontroller.DoseResponseController',
    # CRITICAL: ExternalPassthroughMiddleware must run BEFORE CsrfViewMiddleware
    # so it can return a response before CSRF validation occurs
    'dose.passthrough.middleware.ExternalPassthroughMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'allauth.account.middleware.AccountMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]
if _oauth2_available:
    MIDDLEWARE.insert(
        MIDDLEWARE.index('django.contrib.auth.middleware.AuthenticationMiddleware') + 1,
        'oauth2_provider.middleware.OAuth2TokenMiddleware',
    )

ROOT_URLCONF = 'mysite.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [
            os.path.join(BASE_DIR, 'dose', 'templates'),
            os.path.join(BASE_DIR, 'templates'),
        ],
        'APP_DIRS': True,
        'OPTIONS': {
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
        'ENGINE': 'django.db.backends.postgresql',  # Regular PostgreSQL backend for session-based tenancy
        'NAME': 'dosedbsaas',
        'USER': 'dosedbadmin',
        'PASSWORD': env('DOSE_DB_PASSWORD', default=''),
        'HOST': 'localhost',
        'PORT': '5433',
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



TIME_ZONE = 'Asia/Manila'

USE_I18N = True

USE_L10N = True

USE_TZ = True

CSRF_TRUSTED_ORIGINS = ["http://localhost:8000", "http://localhost:444"]
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
        'osticket_file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': './osticket.log',
        },
    },
    'loggers': {
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
        'osticket': {
            'handlers': ['osticket_file'],
            'level': 'INFO',
            'propagate': False,
        },
    },
    'root': {
        'handlers': ['console', 'file', 'info_file'],
        'level': 'INFO',
    },
}

# Only keep the first LOGGING config above, which defines all handlers and loggers.
# Custom user session settings


