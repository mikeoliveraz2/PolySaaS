"""
fix_polysniffer_migration.py

The polysniffer_trafficlog table already exists in public schema from a prior run.
This script:
 1. Fakes the polysniffer.0001_initial migration record in every schema that
    already has the table (so migrate_all_schemas won't try to CREATE it again).
 2. Creates the table + marks the migration in schemas that still lack it.

Run once: python fix_polysniffer_migration.py
"""
import os, sys, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
django.setup()

from django.db import connection
from dose.models import Tenant
from datetime import datetime

CREATE_SQL = """
CREATE TABLE IF NOT EXISTS polysniffer_trafficlog (
    id SERIAL PRIMARY KEY,
    method VARCHAR(10) NOT NULL,
    url VARCHAR(500) NOT NULL,
    path VARCHAR(500) NOT NULL,
    headers JSONB NOT NULL DEFAULT '{}',
    cookies JSONB NOT NULL DEFAULT '{}',
    query_params JSONB NOT NULL DEFAULT '{}',
    body TEXT NOT NULL DEFAULT '',
    status_code INTEGER NOT NULL,
    response_headers JSONB NOT NULL DEFAULT '{}',
    response_body TEXT NOT NULL DEFAULT '',
    response_size INTEGER NOT NULL DEFAULT 0,
    endpoint_name VARCHAR(200) NOT NULL DEFAULT '',
    user_id INTEGER REFERENCES auth_user(id) ON DELETE SET NULL,
    captured_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    duration_ms DOUBLE PRECISION NOT NULL DEFAULT 0,
    har_data JSONB
);
CREATE INDEX IF NOT EXISTS polysniffer_tlog_captured
    ON polysniffer_trafficlog (captured_at DESC);
CREATE INDEX IF NOT EXISTS polysniffer_tlog_url
    ON polysniffer_trafficlog (url);
CREATE INDEX IF NOT EXISTS polysniffer_tlog_endpoint
    ON polysniffer_trafficlog (endpoint_name);
"""

FAKE_MIGRATION_SQL = """
INSERT INTO django_migrations (app, name, applied)
VALUES ('polysniffer', '0001_initial', NOW())
ON CONFLICT DO NOTHING;
"""

CHECK_TABLE_SQL = """
SELECT EXISTS (
    SELECT FROM information_schema.tables
    WHERE table_schema = current_schema()
    AND table_name = 'polysniffer_trafficlog'
);
"""

CHECK_MIGRATION_SQL = """
SELECT EXISTS (
    SELECT FROM django_migrations
    WHERE app = 'polysniffer' AND name = '0001_initial'
);
"""

def handle_schema(schema, label):
    with connection.cursor() as cur:
        cur.execute(f"SET search_path TO {schema}, public;")
        cur.execute(CHECK_TABLE_SQL)
        table_exists = cur.fetchone()[0]

        cur.execute(CHECK_MIGRATION_SQL)
        migration_recorded = cur.fetchone()[0]

        if not table_exists:
            print(f"  [{label}] Creating polysniffer_trafficlog ...")
            cur.execute(CREATE_SQL)
        else:
            print(f"  [{label}] Table already exists — skipping CREATE")

        if not migration_recorded:
            cur.execute(FAKE_MIGRATION_SQL)
            print(f"  [{label}] Migration record inserted")
        else:
            print(f"  [{label}] Migration already recorded — skipping INSERT")

    connection.connection.commit()
    print(f"  [{label}] Done\n")

def main():
    print("=== PolySniffer migration fix ===\n")

    # Public schema first
    handle_schema("public", "public")

    # All tenant schemas
    with connection.cursor() as cur:
        cur.execute("SET search_path TO public;")
    tenants = Tenant.objects.all().order_by("schema_name")
    for t in tenants:
        if not t.schema_name or t.schema_name.lower() == "public":
            continue
        handle_schema(t.schema_name, t.schema_name)

    print("=== All done. polysniffer_trafficlog is ready in all schemas. ===")

if __name__ == "__main__":
    main()
