"""
Railway / container production settings.

Usage:
  export DJANGO_SETTINGS_MODULE=mysite.settings_railway

Extends mysite.settings and overrides database, broker, sessions, static files,
logging, and security for a 12-factor deploy (env vars only).
"""
import os
import logging
from urllib.parse import urlsplit, urlunsplit

import environ

print("[Django] Loading mysite/settings_railway.py at", os.path.basename(__file__), flush=True)

from mysite.settings import *  # noqa: F401,F403

print("[Django] Base settings loaded, configuring Railway overrides", flush=True)

# Liveness for Railway: respond before SecurityMiddleware (no HTTP→HTTPS redirect on
# internal probes) and before SessionTenantMiddleware (no DB cursor on cold Postgres).
MIDDLEWARE.insert(0, "mysite.railway_health_middleware.RailwayLivenessMiddleware")
print("[Django] RailwayLivenessMiddleware inserted at MIDDLEWARE position 0", flush=True)

_env = environ.Env(
    DEBUG=(bool, False),
)


def _normalize_database_url(database_url):
    parts = urlsplit(database_url)
    scheme = parts.scheme.lower()
    if scheme in {"postgres", "postgresql"}:
        return database_url
    if scheme.startswith("postgres+") or scheme.startswith("postgresql+"):
        return urlunsplit(("postgresql", parts.netloc, parts.path, parts.query, parts.fragment))
    return database_url

# --- Core ---
DEBUG = _env.bool("DEBUG", default=False)
SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY", SECRET_KEY)

_allowed = os.environ.get("ALLOWED_HOSTS", "").strip()
if _allowed:
    ALLOWED_HOSTS = [h.strip() for h in _allowed.split(",") if h.strip()]
elif DEBUG:
    ALLOWED_HOSTS = ["*"]
else:
    # Railway default hostname pattern + localhost for health probes
    ALLOWED_HOSTS = [".railway.app", ".up.railway.app", "localhost", "127.0.0.1"]

# --- Database: DATABASE_URL preferred (Railway), else discrete vars ---
_database_url = os.environ.get("DATABASE_URL", "").strip()
if _database_url:
    DATABASES = {"default": environ.Env.db_url_config(_normalize_database_url(_database_url))}
    DATABASES["default"]["CONN_MAX_AGE"] = int(os.environ.get("DB_CONN_MAX_AGE", "0"))
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": os.environ.get("DB_NAME", "dosedbsaas"),
            "USER": os.environ.get("DB_USER", "dosedbadmin"),
            "PASSWORD": os.environ.get("DOSE_DB_PASSWORD", os.environ.get("DB_PASSWORD", "")),
            "HOST": os.environ.get("DB_HOST", "localhost"),
            "PORT": os.environ.get("DB_PORT", "5432"),
            "CONN_MAX_AGE": int(os.environ.get("DB_CONN_MAX_AGE", "0")),
        }
    }

# --- Celery / RabbitMQ ---
_celery_broker = os.environ.get("CELERY_BROKER_URL", "").strip()
if _celery_broker:
    CELERY_BROKER_URL = _celery_broker

# --- Sessions: avoid file-based sessions on ephemeral containers ---
SESSION_ENGINE = "django.contrib.sessions.backends.db"

# --- Static & media (Whitenoise for app-served static) ---
STATIC_ROOT = os.environ.get("STATIC_ROOT", "/app/var/static_root/")
MEDIA_ROOT = os.environ.get("MEDIA_ROOT", "/app/var/media_root/")

if "whitenoise.middleware.WhiteNoiseMiddleware" not in MIDDLEWARE:
    try:
        _sec_idx = MIDDLEWARE.index("django.middleware.security.SecurityMiddleware")
        MIDDLEWARE.insert(_sec_idx + 1, "whitenoise.middleware.WhiteNoiseMiddleware")
    except ValueError:
        MIDDLEWARE.insert(0, "whitenoise.middleware.WhiteNoiseMiddleware")

STATICFILES_STORAGE = "whitenoise.storage.CompressedStaticFilesStorage"
WHITENOISE_KEEP_ONLY_HASHED_FILES = False

# --- HTTPS / proxy (Railway terminates TLS) ---
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
USE_X_FORWARDED_HOST = True

if not DEBUG:
    # Default False: Railway terminates TLS; internal health checks are often HTTP
    # without X-Forwarded-Proto — a True default yields 301 and a failed deploy healthcheck.
    SECURE_SSL_REDIRECT = _env.bool("SECURE_SSL_REDIRECT", default=False)
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_BROWSER_XSS_FILTER = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    X_FRAME_OPTIONS = "DENY"

# --- CSRF ---
_csrf_origins = os.environ.get("CSRF_TRUSTED_ORIGINS", "").strip()
if _csrf_origins:
    CSRF_TRUSTED_ORIGINS = [o.strip() for o in _csrf_origins.split(",") if o.strip()]

# --- OAuth2 / OIDC (Railway): public issuer URL + optional PEM via env ---
# See documentation/deployment/railway/OAUTH2-RAILWAY.md
_oidc_iss = os.environ.get("OIDC_ISS_ENDPOINT", "").strip()
_oidc_pem = os.environ.get("OIDC_RSA_PRIVATE_KEY", "").strip()
if (_oidc_iss or _oidc_pem) and isinstance(OAUTH2_PROVIDER, dict):
    _oauth2_provider = dict(OAUTH2_PROVIDER)
    if _oidc_iss:
        _oauth2_provider["OIDC_ISS_ENDPOINT"] = _oidc_iss.rstrip("/")
    if _oidc_pem:
        _oauth2_provider["OIDC_RSA_PRIVATE_KEY"] = _oidc_pem.replace("\\n", "\n")
    OAUTH2_PROVIDER = _oauth2_provider

# --- Logging: stdout only ---
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "railway": {
            "format": "{levelname} {asctime} {name} {message}",
            "style": "{",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "railway",
        },
    },
    "root": {
        "handlers": ["console"],
        "level": os.environ.get("LOG_LEVEL", "DEBUG"),
    },
    "loggers": {
        "django": {
            "handlers": ["console"],
            "level": os.environ.get("DJANGO_LOG_LEVEL", "INFO"),
            "propagate": False,
        },
        "dose": {
            "handlers": ["console"],
            "level": os.environ.get("DOSE_LOG_LEVEL", "INFO"),
            "propagate": False,
        },
    },
}

# Quiet startup print from base settings if desired
if not DEBUG:
    logging.getLogger("django.utils.autoreload").setLevel(logging.WARNING)

print("[Django] mysite/settings_railway.py fully loaded and ready", flush=True)
