import os, sys
sys.path.insert(0, r'F:\PolySaaS')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
import django; django.setup()

from django.db import connection
with connection.cursor() as cur:
    cur.execute("SET search_path TO olient,public")

from dose.models import PassThroughEndpoint
ep = PassThroughEndpoint.objects.filter(id=4).first()
if ep:
    print(f"id={ep.id} title={ep.menu_title!r}")
    print(f"  endpoint_url={ep.endpoint_url!r}")
    print(f"  starting_uri={ep.starting_uri!r}")
    print(f"  slug={ep.slug!r}")
    if ep.starting_uri and ep.starting_uri not in ('/', ''):
        old = ep.starting_uri
        ep.starting_uri = '/'
        ep.save(update_fields=['starting_uri'])
        print(f"  FIXED: starting_uri {old!r} -> '/'")
    else:
        print(f"  starting_uri is already correct")
else:
    print("HubSpot endpoint (id=4) not found")
