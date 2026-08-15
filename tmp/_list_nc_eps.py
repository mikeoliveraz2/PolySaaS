import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "mysite.settings")
django.setup()

from django.db import connection

with connection.cursor() as c:
    c.execute("SET search_path TO pso17, public")
    c.execute(
        "SELECT id, slug, endpoint_url, starting_uri "
        "FROM dose_passthroughendpoint "
        "WHERE slug ILIKE %s OR endpoint_url ILIKE %s OR endpoint_url ILIKE %s",
        ["%nextcloud%", "%8888%", "%nextcloud%"],
    )
    print("endpoints:")
    for row in c.fetchall():
        print(row)
    c.execute(
        "SELECT app_name, status FROM dose_tenantapp WHERE app_name=%s",
        ["nextcloud"],
    )
    print("tenantapp:", c.fetchall())
