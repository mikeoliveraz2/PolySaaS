"""List PassThroughEndpoint id, slug, menu_title, endpoint_url in each tenant schema."""
import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "mysite.settings")
django.setup()

from django.db import connection
from dose.models import Tenant, PassThroughEndpoint

print("schema\tid\tslug\tmenu_title\turl")
tenants = list(Tenant.objects.exclude(schema_name="public").order_by("schema_name"))
schemas = ["public"] + [t.schema_name for t in tenants if t.schema_name]
seen = set()
for schema in schemas:
    if not schema or schema in seen:
        continue
    seen.add(schema)
    with connection.cursor() as cur:
        cur.execute(f'SET search_path TO "{schema}", public;')
    try:
        rows = list(PassThroughEndpoint.objects.all().order_by("id"))
    except Exception as exc:
        print(f"{schema}\tERR\t{exc}")
        continue
    if not rows:
        print(f"{schema}\t(none)")
        continue
    for ep in rows:
        slug = repr(ep.slug or "")
        title = (ep.menu_title or "")[:40]
        url = (ep.endpoint_url or "")[:80]
        print(f"{schema}\t{ep.id}\t{slug}\t{title}\t{url}")
