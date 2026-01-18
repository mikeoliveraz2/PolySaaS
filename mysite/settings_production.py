#!/usr/bin/env python
"""
Production settings for GCP deployment.
This file extends the base settings.py and overrides for production.
"""

import os
from mysite.settings import *

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.environ.get('DEBUG', 'False') == 'True'

# Use environment variable for allowed hosts
ALLOWED_HOSTS = os.environ.get('ALLOWED_HOSTS', '*').split(',')

# Database configuration for Cloud SQL
if os.environ.get('USE_CLOUD_SQL'):
    # Cloud SQL connection settings
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': os.environ.get('DB_NAME', 'dosedbsaas'),
            'USER': os.environ.get('DB_USER', 'dosedbadmin'),
            'PASSWORD': os.environ.get('DOSE_DB_PASSWORD', ''),
            'HOST': os.environ.get('DB_HOST', '/cloudsql/' + os.environ.get('CLOUDSQL_CONNECTION_NAME', '')),
            'PORT': os.environ.get('DB_PORT', '5432'),
        }
    }

# Static files configuration for GCS
if os.environ.get('USE_GCS_STATIC'):
    # Google Cloud Storage for static files
    DEFAULT_FILE_STORAGE = 'storages.backends.gcloud.GoogleCloudStorage'
    STATICFILES_STORAGE = 'storages.backends.gcloud.GoogleCloudStorage'
    GS_BUCKET_NAME = os.environ.get('GCS_BUCKET_NAME', 'dosev3-static')
    GS_PROJECT_ID = os.environ.get('GCP_PROJECT_ID')
    STATIC_URL = f'https://storage.googleapis.com/{GS_BUCKET_NAME}/'
else:
    # Use local static files (for Cloud Run with volume)
    STATIC_ROOT = '/app/var/static_root/'
    STATIC_URL = '/static/'

MEDIA_ROOT = '/app/var/media_root/'
MEDIA_URL = '/media/'

# Security settings for production
if not DEBUG:
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_BROWSER_XSS_FILTER = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    X_FRAME_OPTIONS = 'DENY'
    SECURE_HSTS_SECONDS = 31536000
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True

# Logging configuration for GCP
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': os.environ.get('DJANGO_LOG_LEVEL', 'INFO'),
            'propagate': False,
        },
    },
}

# Email configuration for production
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = os.environ.get('EMAIL_HOST', 'smtp.gmail.com')
EMAIL_PORT = int(os.environ.get('EMAIL_PORT', '587'))
EMAIL_USE_TLS = True
EMAIL_HOST_USER = os.environ.get('EMAIL_HOST_USER', '')
EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD', '')
DEFAULT_FROM_EMAIL = os.environ.get('DEFAULT_FROM_EMAIL', 'noreply@dosesaas.com')

# Celery configuration for Cloud Tasks (optional)
if os.environ.get('USE_CLOUD_TASKS'):
    # TODO: Configure Cloud Tasks instead of Celery for GCP
    pass
