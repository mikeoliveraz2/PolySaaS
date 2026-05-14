import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE','mysite.settings')
import django
django.setup()
from django.db import connection
from dose.models import PassThroughEndpoint

with connection.cursor() as cur:
    cur.execute('SET search_path TO "polysaase2e2", public')
pts = PassThroughEndpoint.objects.all()
print('polysaase2e2 count:', pts.count())
for pt in pts:
    print(f'  {pt.trigger_path}: {pt.endpoint_url}')
