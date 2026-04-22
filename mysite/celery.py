"""
Celery application for PolySaaS (DOSE).

Worker (Render / local):
  celery -A mysite worker -l INFO

Beat (optional; requires django-celery-beat in INSTALLED_APPS if using DB scheduler):
  celery -A mysite beat -l INFO
"""
import os

from celery import Celery

# Respect DJANGO_SETTINGS_MODULE from environment (e.g. mysite.settings_render on Render).
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "mysite.settings")

app = Celery("mysite")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()
