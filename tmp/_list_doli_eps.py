import os, django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "mysite.settings")
django.setup()
from django.db import connection
from dose.models import PassThroughEndpoint

for schema in ("public", "pso17", "olient"):
    with connection.cursor() as cur:
        cur.execute(f"SET search_path TO {schema},public;")
    print("===", schema)
    for e in PassThroughEndpoint.objects.all():
        print(
            f"  id={e.id} slug={e.slug!r} url={e.endpoint_url!r} enabled={e.is_enabled}"
        )
