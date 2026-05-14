import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE','mysite.settings')
import django
django.setup()
from django.db import connection
from dose.models import PassThroughEndpoint

for schema in ['polysaase2e2', 'polysaas', 'public']:
    with connection.cursor() as cur:
        cur.execute(f'SET search_path TO "{schema}", public')
    pts = PassThroughEndpoint.objects.all()
    print(f"=== {schema} ({pts.count()} records) ===")
    for pt in pts:
        print(f"  {pt.trigger_path}: url={pt.endpoint_url}")
    print()
