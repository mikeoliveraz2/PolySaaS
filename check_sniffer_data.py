#!/usr/bin/env python
"""Inspect TrafficLog and PassThroughEndpoints to debug matching"""
import os, django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "mysite.settings")
django.setup()

from django.db import connection, ProgrammingError

# Set search_path to olient
with connection.cursor() as cur:
    cur.execute("SET search_path TO olient, public;")

try:
    from dose.polysniffer.models import TrafficLog
    total = TrafficLog.objects.count()
    print(f"\nTrafficLog total rows: {total}")
    post_logs = TrafficLog.objects.filter(method="POST")
    print(f"POST logs: {post_logs.count()}")
    if post_logs.exists():
        print("Sample endpoint_names:")
        for name in post_logs.values_list("endpoint_name", flat=True).distinct()[:10]:
            print(f"  {name!r}")
        print("Sample paths:")
        for path in post_logs.values_list("path", flat=True).distinct()[:10]:
            print(f"  {path!r}")
    else:
        print("No POST traffic logs found!")
        print("All methods present:")
        for m in TrafficLog.objects.values_list("method", flat=True).distinct():
            print(f"  {m!r}")
except ProgrammingError as e:
    print(f"Error: {e}")

from dose.models.pass_through_endpoint import PassThroughEndpoint
eps = PassThroughEndpoint.objects.all()
print(f"\nPassThroughEndpoints: {eps.count()}")
for ep in eps[:10]:
    print(f"  trigger={ep.trigger_path!r}  url={ep.endpoint_url!r}")
