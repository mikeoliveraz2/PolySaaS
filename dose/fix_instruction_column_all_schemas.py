import os
import sys
import django
import psycopg2

def main():
    # Django setup
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
    django.setup()

    # DB connection
    from django.conf import settings
    DB_SETTINGS = settings.DATABASES['default']
    conn = psycopg2.connect(
        dbname=DB_SETTINGS['NAME'],
        user=DB_SETTINGS['USER'],
        password=DB_SETTINGS['PASSWORD'],
        host=DB_SETTINGS['HOST'],
        port=DB_SETTINGS.get('PORT', 5432)
    )

    # Forced alpha schema block
    print("\n--- Forcing column addition for alpha schema ---")
    try:
        with conn.cursor() as cur:
            cur.execute("SET search_path TO alpha")
            cur.execute("""
                SELECT column_name FROM information_schema.columns 
                WHERE table_name='dose_instruction' AND column_name='save_callbackdata';
            """)
            result = cur.fetchone()
            if result:
                print("Alpha schema: 'save_callbackdata' column already exists, skipping.")
            else:
                try:
                    cur.execute("ALTER TABLE dose_instruction ADD COLUMN save_callbackdata BOOLEAN DEFAULT FALSE;")
                    print("Alpha schema: Added 'save_callbackdata' column.")
                except Exception as add_err:
                    print(f"Alpha schema: Error adding column: {add_err}")
        conn.commit()
    except Exception as e:
        print(f"Alpha schema: Fatal error: {e}\n")
        conn.rollback()

    # Tenant loop (example, adjust as needed for your codebase)
    from dose.models import Tenant
    for tenant in Tenant.objects.all():
        schema = tenant.schema_name
        print(f"Checking schema: {schema}")
        try:
            with conn.cursor() as cur:
                cur.execute(f"SET search_path TO {schema}")
                cur.execute("""
                    SELECT column_name FROM information_schema.columns 
                    WHERE table_name='dose_instruction' AND column_name='save_callbackdata';
                """)
                result = cur.fetchone()
                if result:
                    print(f"Schema {schema}: 'save_callbackdata' column already exists, skipping.")
                else:
                    try:
                        cur.execute("ALTER TABLE dose_instruction ADD COLUMN save_callbackdata BOOLEAN DEFAULT FALSE;")
                        print(f"Schema {schema}: Added 'save_callbackdata' column.")
                    except Exception as add_err:
                        print(f"Schema {schema}: Error adding column: {add_err}")
            conn.commit()
        except Exception as e:
            print(f"Schema {schema}: Error in schema operation: {e}\n")
            conn.rollback()

if __name__ == "__main__":
    main()
