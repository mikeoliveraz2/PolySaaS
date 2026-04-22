"""
Render / container production settings.

Usage:
  export DJANGO_SETTINGS_MODULE=mysite.settings_render

Extends mysite.settings and overrides database, broker, sessions, static files,
logging, and security for a 12-factor deploy (env vars only).
"""
import os
import logging
from urllib.parse import urlsplit, urlunsplit

import environ

print("[Django] Loading mysite/settings_render.py at", os.path.basename(__file__), flush=True)

from mysite.settings import *  # noqa: F401,F403

print("[Django] Base settings loaded, configuring Render overrides", flush=True)

# Liveness: respond before SecurityMiddleware (no HTTP→HTTPS redirect on
# internal probes) and before SessionTenantMiddleware (no DB cursor on cold Postgres).
MIDDLEWARE.insert(0, "mysite.render_health_middleware.RenderLivenessMiddleware")
print("[Django] RenderLivenessMiddleware inserted at MIDDLEWARE position 0", flush=True)

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
    # Render default hostname pattern + localhost for health probes
    ALLOWED_HOSTS = [".onrender.com", "localhost", "127.0.0.1"]

# --- Database: DATABASE_URL preferred (Render), else discrete vars ---
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

# --- HTTPS / proxy (Render terminates TLS) ---
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
USE_X_FORWARDED_HOST = True

if not DEBUG:
    # Default False: Render terminates TLS; internal health checks are often HTTP
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

# --- OAuth2 / OIDC (Render): public issuer URL + optional PEM via env ---
# See documentation/deployment/render/OAUTH2-RENDER.md
_oidc_iss = os.environ.get("OIDC_ISS_ENDPOINT", "").strip()
_oidc_pem = os.environ.get("OIDC_RSA_PRIVATE_KEY", "").strip()
if (_oidc_iss or _oidc_pem) and isinstance(OAUTH2_PROVIDER, dict):
    _oauth2_provider = dict(OAUTH2_PROVIDER)
    if _oidc_iss:
        _oauth2_provider["OIDC_ISS_ENDPOINT"] = _oidc_iss.rstrip("/")
    if _oidc_pem:
        _oauth2_provider["OIDC_RSA_PRIVATE_KEY"] = _oidc_pem.replace("\\n", "\n")
    OAUTH2_PROVIDER = _oauth2_provider

# --- Logging: explicit stdout for Render log streams ---
# Python's StreamHandler defaults to stderr; Render shows both, but stdout matches
# ops expectations and matches gunicorn --error-logfile - style piping.
# Env: LOG_LEVEL (root), DJANGO_LOG_LEVEL, DOSE_LOG_LEVEL, CC_LOG_LEVEL (polysaas.*).
# Container: set PYTHONUNBUFFERED=1 (already in Dockerfile.django + render.yaml polysaas-common).
_ALLOWED_LOG_LEVELS = frozenset({"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"})


def _env_log_level(name: str, default: str) -> str:
    raw = os.environ.get(name, default).strip().upper()
    return raw if raw in _ALLOWED_LOG_LEVELS else default


_root_level = _env_log_level("LOG_LEVEL", "INFO")
_django_level = _env_log_level("DJANGO_LOG_LEVEL", _root_level)
_dose_level = _env_log_level("DOSE_LOG_LEVEL", _root_level)
_cc_level = _env_log_level("CC_LOG_LEVEL", _root_level)

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "render": {
            "format": "%(asctime)s | %(levelname)s | %(name)s | %(message)s",
            "datefmt": "%Y-%m-%d %H:%M:%S",
        },
    },
    "handlers": {
        "stdout": {
            "class": "logging.StreamHandler",
            "formatter": "render",
            "stream": "ext://sys.stdout",
        },
    },
    "root": {
        "handlers": ["stdout"],
        "level": _root_level,
    },
    "loggers": {
        "django": {
            "handlers": ["stdout"],
            "level": _django_level,
            "propagate": False,
        },
        "django.server": {
            "handlers": ["stdout"],
            "level": _django_level,
            "propagate": False,
        },
        "dose": {
            "handlers": ["stdout"],
            "level": _dose_level,
            "propagate": False,
        },
        # Cross-cutting / passthrough / PolySniffer style code: logging.getLogger("polysaas.cc")
        "polysaas": {
            "handlers": ["stdout"],
            "level": _cc_level,
            "propagate": False,
        },
        "gunicorn.error": {
            "handlers": ["stdout"],
            "level": "INFO",
            "propagate": False,
        },
        "gunicorn.access": {
            "handlers": ["stdout"],
            "level": "INFO",
            "propagate": False,
        },
        "llm_router": {
            "handlers": ["stdout"],
            "level": _dose_level,
            "propagate": False,
        },
        "llm_router.decisions": {
            "handlers": ["stdout"],
            "level": "INFO",
            "propagate": False,
        },
    },
}

# Quiet startup print from base settings if desired
if not DEBUG:
    logging.getLogger("django.utils.autoreload").setLevel(logging.WARNING)

print("[Django] mysite/settings_render.py fully loaded and ready", flush=True)
