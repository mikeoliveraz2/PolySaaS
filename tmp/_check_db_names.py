import os
import sys

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "mysite.settings")
import django

django.setup()

from django.conf import settings
import psycopg2

db = settings.DATABASES["default"]
print("Django configured:")
print(f"  HOST={db['HOST']} PORT={db['PORT']} NAME={db['NAME']} USER={db['USER']}")

for dbname in ("dosedbsaas", "polysaas"):
    try:
        conn = psycopg2.connect(
            host=db["HOST"],
            port=db["PORT"],
            user=db["USER"],
            password=db["PASSWORD"],
            dbname=dbname,
        )
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM auth_user")
        user_count = cur.fetchone()[0]
        cur.execute(
            "SELECT username, email FROM auth_user "
            "WHERE username = %s OR email ILIKE %s LIMIT 10",
            ("olientAdmin", "%michael.oliver%"),
        )
        users = cur.fetchall()
        cur.execute(
            "SELECT slug, schema_name, name FROM dose_tenant "
            "WHERE slug = %s OR name ILIKE %s LIMIT 10",
            ("olient", "%oliver%"),
        )
        tenants = cur.fetchall()
        conn.close()
        print(f"\nDatabase {dbname!r}:")
        print(f"  auth_user count: {user_count}")
        print(f"  matching users: {users}")
        print(f"  matching tenants: {tenants}")
    except Exception as exc:
        print(f"\nDatabase {dbname!r}: ERROR {exc}")
