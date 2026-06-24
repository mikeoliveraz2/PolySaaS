"""
GCP / Cloud Run production settings for PolySaaS.

Usage:
  export DJANGO_SETTINGS_MODULE=mysite.settings_gcp

Extends settings_render.py (12-factor, Whitenoise fallback) and adds:
  - Cloud SQL Unix socket via USE_CLOUD_SQL + CLOUDSQL_CONNECTION_NAME
  - Optional GCS static/media via USE_GCS_STATIC + django-storages
  - Bundled app URLs from env (ODOO_SHARED_URL, MATTERMOST_URL)
"""
import os

print("[Django] Loading mysite/settings_gcp.py", flush=True)

from mysite.settings_render import *  # noqa: F401,F403

print("[Django] Render base loaded; applying GCP overrides", flush=True)

# --- Cloud SQL (Unix socket on Cloud Run) ---
if os.environ.get("USE_CLOUD_SQL", "").lower() in ("1", "true", "yes"):
    _conn = os.environ.get("CLOUDSQL_CONNECTION_NAME", "").strip()
    _host = os.environ.get("DB_HOST", "").strip()
    if not _host and _conn:
        _host = f"/cloudsql/{_conn}"
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": os.environ.get("DB_NAME", "dosedbsaas"),
            "USER": os.environ.get("DB_USER", "dosedbadmin"),
            "PASSWORD": os.environ.get(
                "DOSE_DB_PASSWORD", os.environ.get("DB_PASSWORD", "")
            ),
            "HOST": _host,
            "PORT": os.environ.get("DB_PORT", ""),
            "CONN_MAX_AGE": int(os.environ.get("DB_CONN_MAX_AGE", "0")),
        }
    }
    print(f"[Django] Cloud SQL enabled host={_host!r}", flush=True)

# --- GCS static + media (optional; Whitenoise remains default when off) ---
if os.environ.get("USE_GCS_STATIC", "").lower() in ("1", "true", "yes"):
    if "storages" not in INSTALLED_APPS:
        INSTALLED_APPS = list(INSTALLED_APPS) + ["storages"]

    _static_bucket = os.environ.get("GCS_STATIC_BUCKET", "polysaas-django-static")
    _media_bucket = os.environ.get("GCS_MEDIA_BUCKET", "polysaas-django-media")

    STORAGES = {
        "default": {
            "BACKEND": "storages.backends.gcloud.GoogleCloudStorage",
            "OPTIONS": {"bucket_name": _media_bucket},
        },
        "staticfiles": {
            "BACKEND": "storages.backends.gcloud.GoogleCloudStorage",
            "OPTIONS": {"bucket_name": _static_bucket},
        },
    }
    GS_BUCKET_NAME = _static_bucket
    GS_PROJECT_ID = os.environ.get("GCP_PROJECT_ID", os.environ.get("GOOGLE_CLOUD_PROJECT", ""))
    STATIC_URL = f"https://storage.googleapis.com/{_static_bucket}/"
    MEDIA_URL = f"https://storage.googleapis.com/{_media_bucket}/"
    # Whitenoise not needed when GCS serves static
    MIDDLEWARE = [m for m in MIDDLEWARE if m != "whitenoise.middleware.WhiteNoiseMiddleware"]
    if "STATICFILES_STORAGE" in globals():
        del STATICFILES_STORAGE
    print(f"[Django] GCS static bucket={_static_bucket} media={_media_bucket}", flush=True)

# --- GCP bundled app URLs (override Render defaults when set) ---
for _key, _default in (
    ("ODOO_SHARED_URL", None),
    ("MATTERMOST_URL", None),
):
    _val = os.environ.get(_key, "").strip()
    if _val:
        globals()[_key] = _val

# --- Cloud Run allowed hosts ---
for _host in (".run.app", ".polysaas.online", "production.polysaas.online"):
    if _host not in ALLOWED_HOSTS:
        ALLOWED_HOSTS.append(_host)

_csrf = os.environ.get("CSRF_TRUSTED_ORIGINS", "").strip()
if _csrf:
    CSRF_TRUSTED_ORIGINS = [o.strip() for o in _csrf.split(",") if o.strip()]
else:
    for _origin in (
        "https://production.polysaas.online",
        "https://*.polysaas.online",
        "https://*.run.app",
    ):
        if _origin not in CSRF_TRUSTED_ORIGINS:
            CSRF_TRUSTED_ORIGINS.append(_origin)

print("[Django] mysite/settings_gcp.py fully loaded", flush=True)
