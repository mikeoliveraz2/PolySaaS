#!/usr/bin/env python
"""
Create TrafficLog table in olient schema (bypassing contenttypes issue)
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
django.setup()

from django.db import connection

print("="*60)
print("Creating TrafficLog table in olient schema")
print("="*60)
print()

# Set schema to olient
with connection.cursor() as cursor:
    # Switch to olient schema
    cursor.execute("SET search_path TO olient, public;")

    # Check if table already exists
    cursor.execute("""
        SELECT EXISTS (
            SELECT FROM information_schema.tables
            WHERE table_schema = 'olient'
            AND table_name = 'dose_trafficlog'
        );
    """)
    exists = cursor.fetchone()[0]

    if exists:
        print("[OK] TrafficLog table already exists in olient schema!")
    else:
        print("[ACTION] Creating TrafficLog table...")

        # Create the table using the migration SQL
        cursor.execute("""
            CREATE TABLE olient.dose_trafficlog (
                id BIGSERIAL PRIMARY KEY,
                method VARCHAR(10) NOT NULL,
                url VARCHAR(500) NOT NULL,
                path VARCHAR(500) NOT NULL,
                headers JSONB DEFAULT '{}'::jsonb,
                cookies JSONB DEFAULT '{}'::jsonb,
                query_params JSONB DEFAULT '{}'::jsonb,
                body TEXT,
                status_code INTEGER NOT NULL,
                response_headers JSONB DEFAULT '{}'::jsonb,
                response_body TEXT,
                response_size INTEGER DEFAULT 0,
                endpoint_name VARCHAR(200),
                captured_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                duration_ms DOUBLE PRECISION DEFAULT 0,
                har_data JSONB,
                user_id INTEGER REFERENCES olient.auth_user(id) ON DELETE SET NULL
            );
        """)

        # Create indexes
        cursor.execute("""
            CREATE INDEX dose_traffi_capture_d016d1_idx ON olient.dose_trafficlog (captured_at DESC);
        """)

        cursor.execute("""
            CREATE INDEX dose_traffi_url_8db12d_idx ON olient.dose_trafficlog (url);
        """)

        cursor.execute("""
            CREATE INDEX dose_traffi_endpoin_d4c682_idx ON olient.dose_trafficlog (endpoint_name);
        """)

        print("[OK] TrafficLog table created with indexes!")

# Verify in all schemas
print()
print("="*60)
print("Verifying all schemas...")
print("="*60)

schemas = ['public', 'olient']
for schema in schemas:
    with connection.cursor() as cursor:
        cursor.execute(f"SET search_path TO {schema}, public;")
        cursor.execute(f"""
            SELECT EXISTS (
                SELECT FROM information_schema.tables
                WHERE table_schema = '{schema}'
                AND table_name = 'dose_trafficlog'
            );
        """)
        exists = cursor.fetchone()[0]
        status = "[OK] TrafficLog exists" if exists else "[MISSING] TrafficLog missing"
        print(f"{schema}: {status}")

print()
print("="*60)
print("Done! All schemas should have TrafficLog table now.")
print("="*60)

