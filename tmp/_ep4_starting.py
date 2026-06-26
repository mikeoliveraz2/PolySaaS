import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "mysite.settings")
django.setup()
from django.db import connection
from dose.models import PassThroughEndpoint

for s in ("plysaast10", "public"):
    with connection.cursor() as c:
        c.execute(f'SET search_path TO "{s}", public')
    ep = PassThroughEndpoint.objects.filter(id=4).first()
    if ep:
        print(s, ep.menu_title, ep.endpoint_url, ep.starting_uri)
