import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "mysite.settings")
django.setup()

from django.db import connection
from django.test import Client

c = Client()
assert c.login(username="polysaasppv", password="PolySaaS2026!")
s = c.session
s["tenant_slug"] = "polysaasppv"
s.save()

r = c.get("/dose/sniff/2/native/")
print("native status", r.status_code, "len", len(r.content))

with connection.cursor() as cur:
    cur.execute(
        """
        SELECT table_schema FROM information_schema.tables
        WHERE table_name = 'polysniffer_trafficlog' AND table_schema = 'polysaasppv'
        """
    )
    print("polysaasppv trafficlog table", cur.fetchone())
