"""Report WHICH Slack credential keys exist for tenant olient.

Prints key names and value lengths only -- never credential values.
"""
import os
import sys

import django

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "mysite.settings")
django.setup()

from django.db import connection  # noqa: E402

from dose.models import PassThroughEndpoint, TenantApp  # noqa: E402

with connection.cursor() as cur:
    cur.execute("SET search_path TO olient,public;")

print("--- PassThroughEndpoint rows matching slack ---")
for ep in PassThroughEndpoint.objects.filter(endpoint_url__icontains="slack"):
    print(f"  id={ep.id} slug={getattr(ep, 'slug', '')!r} url={ep.endpoint_url}")

print("--- TenantApp rows matching slack ---")
qs = TenantApp.objects.all()
for app in qs:
    name = (getattr(app, "app_name", "") or str(app)).lower()
    if "slack" not in name:
        continue
    cfg = getattr(app, "extra_config", None) or {}
    print(f"  id={app.id} app={getattr(app, 'app_name', '')!r}")
    if isinstance(cfg, dict):
        if not cfg:
            print("    extra_config: EMPTY")
        for k, v in cfg.items():
            print(f"    key={k!r} len={len(str(v))}")
    else:
        print(f"    extra_config type={type(cfg).__name__}")

print(f"--- total TenantApp rows: {qs.count()} ---")
for app in qs:
    print(f"  {getattr(app, 'app_name', '')!r}")
