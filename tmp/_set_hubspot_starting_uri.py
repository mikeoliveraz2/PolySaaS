import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "mysite.settings")
django.setup()
from django.db import connection
from dose.models import PassThroughEndpoint

uri = "/global-home/246571499"
for schema in ("plysaast10", "public", "polysaasppd2"):
    with connection.cursor() as c:
        c.execute(f'SET search_path TO "{schema}", public')
    ep = PassThroughEndpoint.objects.filter(id=4).first()
    if ep:
        ep.starting_uri = uri
        ep.save(update_fields=["starting_uri"])
        print(f"updated {schema} endpoint 4 starting_uri={uri}")
