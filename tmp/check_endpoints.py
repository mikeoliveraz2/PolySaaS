import os, sys
sys.path.insert(0, r'F:\PolySaaS')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
import django; django.setup()

from django.db import connection
with connection.cursor() as cur:
    cur.execute("SET search_path TO olient,public")

from dose.models import PassThroughEndpoint
eps = PassThroughEndpoint.objects.filter(is_enabled=True)
for ep in eps:
    print(f"id={ep.id} menu_title={ep.menu_title!r} slug={ep.slug!r}")
    print(f"  endpoint_url={ep.endpoint_url!r}")
    print(f"  get_menu_url()={ep.get_menu_url()!r}")
