#!/usr/bin/env python
import os
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
django.setup()

from django.db import connection

def fix_admin_constraint():
    with connection.cursor() as cursor:
        print("Fixing Django admin log constraint...")
        
        try:
            # Check if the old constraint exists
            cursor.execute("""
                SELECT COUNT(*) FROM pg_constraint 
                WHERE conname = 'django_admin_log_user_id_c564eba6_fk_dose_tenantuser_id'
            """)
            old_constraint_exists = cursor.fetchone()[0] > 0
            
            if old_constraint_exists:
                print("Found old constraint, dropping it...")
                cursor.execute("""
                    ALTER TABLE django_admin_log 
                    DROP CONSTRAINT IF EXISTS django_admin_log_user_id_c564eba6_fk_dose_tenantuser_id
                """)
                print("✓ Dropped old constraint")
            else:
                print("Old constraint not found")
            
            # Check if auth_user table exists
            cursor.execute("""
                SELECT EXISTS(
                    SELECT 1 FROM information_schema.tables 
                    WHERE table_name='auth_user'
                )
            """)
            auth_user_exists = cursor.fetchone()[0]
            
            if auth_user_exists:
                print("auth_user table exists, creating correct constraint...")
                
                # Clean up orphaned admin log entries first
                cursor.execute("""
                    DELETE FROM django_admin_log 
                    WHERE user_id NOT IN (SELECT id FROM auth_user)
                """)
                print("✓ Cleaned up orphaned admin log entries")
                
                # Create correct constraint
                cursor.execute("""
                    ALTER TABLE django_admin_log 
                    ADD CONSTRAINT django_admin_log_user_id_c564eba6_fk_auth_user_id 
                    FOREIGN KEY (user_id) REFERENCES auth_user(id) DEFERRABLE INITIALLY DEFERRED
                """)
                print("✓ Created correct constraint")
                
            else:
                print("❌ auth_user table does not exist!")
                
            print("✅ Constraint fix completed successfully!")
            
        except Exception as e:
            print(f"❌ Error: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    fix_admin_constraint()
