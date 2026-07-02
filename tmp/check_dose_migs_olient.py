"""Show dose migrations applied in olient vs public."""
from django.db import connection

with connection.cursor() as cur:
    cur.execute("SELECT name FROM olient.django_migrations WHERE app='dose' ORDER BY name;")
    olient_dose = [r[0] for r in cur.fetchall()]
    print(f"dose migrations in olient ({len(olient_dose)}):")
    for m in olient_dose:
        print(f"  {m}")

    cur.execute("SELECT name FROM public.django_migrations WHERE app='dose' ORDER BY name;")
    public_dose = [r[0] for r in cur.fetchall()]
    print(f"\ndose migrations in public ({len(public_dose)}):")
    for m in public_dose:
        print(f"  {m}")

    missing = set(public_dose) - set(olient_dose)
    print(f"\nMissing in olient ({len(missing)}):")
    for m in sorted(missing):
        print(f"  MISSING: {m}")
