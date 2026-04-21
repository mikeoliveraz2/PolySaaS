import os
import sys
import django

# Add the project directory to the Python path
sys.path.append(os.path.dirname(__file__))

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
django.setup()

from django.db import connection, transaction

def fix_admin_constraints():
    with connection.cursor() as cursor:
        try:
            # Clean up invalid admin log entries
            cursor.execute('DELETE FROM django_admin_log WHERE user_id NOT IN (SELECT id FROM auth_user);')
            print('✅ Cleaned invalid admin log entries')
            
            # Check for tenantuser constraints
            cursor.execute("""
                SELECT conname, conrelid::regclass, confrelid::regclass 
                FROM pg_constraint 
                WHERE confrelid::regclass::text LIKE '%tenantuser%';
            """)
            constraints = cursor.fetchall()
            
            if constraints:
                print(f'❌ Found {len(constraints)} tenantuser constraints:')
                for constraint in constraints:
                    print(f'   {constraint[0]}: {constraint[1]} -> {constraint[2]}')
                    
                    # Drop the constraint
                    try:
                        cursor.execute(f'ALTER TABLE {constraint[1]} DROP CONSTRAINT {constraint[0]};')
                        print(f'✅ Dropped constraint {constraint[0]}')
                    except Exception as e:
                        print(f'❌ Error dropping constraint {constraint[0]}: {e}')
            else:
                print('✅ No tenantuser constraints found')
                
            # Commit the transaction
            transaction.commit()
            
        except Exception as e:
            print(f'❌ Error: {e}')
            transaction.rollback()

if __name__ == "__main__":
    fix_admin_constraints()
    print("✨ Database constraint fix completed!")
