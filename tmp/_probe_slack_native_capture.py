"""Show the most recent Slack native capture rows for tenant olient.

Prints only method / status / path metadata -- no headers, cookies or bodies.
"""
import os
import sys

import django

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "mysite.settings")
django.setup()

from django.db import connection  # noqa: E402

from dose.polysniffer.models import TrafficLog  # noqa: E402

with connection.cursor() as cur:
    cur.execute("SET search_path TO olient,public;")

rows = list(
    TrafficLog.objects.filter(url__icontains="slack")
    .order_by("-id")
    .values("id", "captured_at", "method", "status_code", "path", "capture_source")[:40]
)
print(f"total slack rows: {TrafficLog.objects.filter(url__icontains='slack').count()}")
print(f"{'id':>6}  {'when':<19}  {'src':<12}  {'st':>3}  method  path")
for r in reversed(rows):
    when = r["captured_at"].strftime("%Y-%m-%d %H:%M:%S") if r["captured_at"] else ""
    print(
        f"{r['id']:>6}  {when:<19}  {(r['capture_source'] or ''):<12}  "
        f"{str(r['status_code']):>3}  {(r['method'] or ''):<6}  {str(r['path'])[:90]}"
    )
