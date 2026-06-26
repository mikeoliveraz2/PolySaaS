import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "mysite.settings")
django.setup()

from django.db import connection
from dose.models import Tenant, PassThroughEndpoint


def main():
    with connection.cursor() as cur:
        cur.execute(
            """
            SELECT schema_name FROM information_schema.schemata
            WHERE schema_name LIKE '%t10%' OR schema_name LIKE '%ppd%' OR schema_name LIKE '%hubspot%'
            ORDER BY schema_name
            """
        )
        schemas = [r[0] for r in cur.fetchall()]
    print("PG schemas:", schemas)

    with connection.cursor() as cur:
        cur.execute("SET search_path TO public")
    for t in Tenant.objects.all().order_by("schema_name"):
        if "t10" in t.schema_name or "ppd" in (t.slug or "") or t.id <= 10:
            print(
                f"Tenant id={t.id} slug={t.slug} schema={t.schema_name} active={t.is_active}"
            )

    for schema in schemas:
        try:
            with connection.cursor() as cur:
                cur.execute(f'SET search_path TO "{schema}", public')
                cur.execute(
                    "SELECT id, menu_title, endpoint_url FROM dose_passthroughendpoint WHERE id=4"
                )
                row = cur.fetchone()
                if row:
                    print(f"Endpoint 4 in schema {schema}:", row)
        except Exception as exc:
            print(f"schema {schema} endpoint check failed: {exc}")

    # users on plysaast10 tenant
    with connection.cursor() as cur:
        cur.execute("SET search_path TO public")
        t = Tenant.objects.filter(schema_name="plysaast10").first()
        if t:
            print("Found tenant plysaast10:", t.slug, t.name)
        t2 = Tenant.objects.filter(schema_name__icontains="t10").first()
        if t2:
            print("First t10 tenant:", t2.slug, t2.schema_name)


if __name__ == "__main__":
    main()
