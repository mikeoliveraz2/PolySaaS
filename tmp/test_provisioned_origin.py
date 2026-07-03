import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "mysite.settings")

import django

django.setup()

from django.db import connection
from dose.passthrough.handlers.hubspot_handler import HubspotPassthroughHandler

with connection.cursor() as cur:
    cur.execute("SET search_path TO olient,public;")

h = HubspotPassthroughHandler()
print("from_db eid=4:", h._provisioned_hub_origin_from_db(4))
print("from_db eid=None:", h._provisioned_hub_origin_from_db(None))

with connection.cursor() as cur:
    cur.execute("SHOW search_path")
    print("search_path after:", cur.fetchone())

print("upstream /home:", h.upstream_url_for_subpath("https://app.hubspot.com", "/home/"))
