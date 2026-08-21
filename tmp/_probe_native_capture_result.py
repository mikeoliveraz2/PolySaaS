"""Report the newest capture sessions for olient and where their rows came from."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "mysite.settings")

import django

django.setup()

from django.db import connection

SCHEMA = "olient"
with connection.cursor() as cur:
    cur.execute(f'SET search_path TO "{SCHEMA}",public;')

from dose.polysniffer.models import TrafficCapture, TrafficLog

print("=== newest capture sessions ===")
for cap in TrafficCapture.objects.order_by("-id")[:5]:
    rows = TrafficLog.objects.filter(capture_session=cap)
    print(
        f"  id={cap.id} active={cap.is_active} name={cap.capture_name} rows={rows.count()}"
    )
    by_source = {}
    for src in rows.values_list("capture_source", flat=True):
        by_source[src] = by_source.get(src, 0) + 1
    print(f"    by capture_source: {by_source}")

newest = TrafficCapture.objects.order_by("-id").first()
if newest:
    print(f"\n=== first 15 rows of capture {newest.id} ===")
    for row in TrafficLog.objects.filter(capture_session=newest).order_by("id")[:15]:
        print(f"  {row.capture_source:>10} {row.method:<5} {row.status_code} {row.url[:110]}")
    print(f"\n=== distinct hosts in capture {newest.id} ===")
    hosts = {}
    for url in TrafficLog.objects.filter(capture_session=newest).values_list("url", flat=True):
        from urllib.parse import urlparse

        h = urlparse(url).netloc
        hosts[h] = hosts.get(h, 0) + 1
    for h, n in sorted(hosts.items(), key=lambda kv: -kv[1]):
        print(f"  {n:>5}  {h}")
