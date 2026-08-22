"""Recent captured request metadata for tenant olient (method / status / path only)."""
import os
import sys

import django

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "mysite.settings")
django.setup()

from datetime import timedelta  # noqa: E402

from django.db import connection  # noqa: E402
from django.utils import timezone  # noqa: E402

from dose.polysniffer.models import TrafficLog  # noqa: E402

with connection.cursor() as cur:
    cur.execute("SET search_path TO olient,public;")

since = timezone.now() - timedelta(hours=2)
rows = list(
    TrafficLog.objects.filter(captured_at__gte=since)
    .order_by("id")
    .values("id", "captured_at", "method", "status_code", "path", "client_path", "capture_source")
)
print(f"rows in last 2h: {len(rows)}")
for r in rows:
    when = r["captured_at"].strftime("%H:%M:%S") if r["captured_at"] else ""
    print(
        f"{r['id']:>6} {when} {(r['capture_source'] or ''):<12} "
        f"{str(r['status_code']):>3} {(r['method'] or ''):<5} "
        f"client={str(r['client_path'])[:55]:<55} up={str(r['path'])[:45]}"
    )
