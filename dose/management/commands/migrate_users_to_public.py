"""
Migrate users from tenant schemas to public schema.
Users should be in public schema for shared access across tenants.
Usage: python manage.py migrate_users_to_public [--dry-run]
"""
from django.core.management.base import BaseCommand
from django.db import connection, transaction
from django.contrib.auth import get_user_model
from django.core.exceptions import IntegrityError

User = get_user_model()


class Command(BaseCommand):
    help = 'Migrate users from tenant schemas to public schema'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be migrated without making changes',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        
        self.stdout.write("=== User Migration to Public Schema ===\n")
        
        # Get list of tenant schemas (excluding public)
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT schema_name 
                FROM information_schema.schemata 
                WHERE schema_name NOT IN ('public', 'pg_catalog', 'pg_toast', 
                                          'information_schema', 'pg_temp_1', 
                                          'pg_toast_temp_1')
                AND schema_name NOT LIKE 'pg_%'
            """)
            schemas = [row[0] for row in cursor.fetchall()]
        
        self.stdout.write(f"Found schemas: {schemas}\n")
        
        # Track users to migrate
        users_to_migrate = []
        
        # Find all users in tenant schemas
        for schema in schemas:
            with connection.cursor() as cursor:
                cursor.execute(f"SET search_path TO {schema}")
                cursor.execute("SELECT id, username, email, first_name, last_name, is_active, is_staff, is_superuser, date_joined, last_login FROM auth_user")
                rows = cursor.fetchall()
                
                if rows:
                    self.stdout.write(f"\nSchema '{schema}': Found {len(rows)} users")
                    for row in rows:
                        user_data = {
                            'id': row[0],
                            'username': row[1],
                            'email': row[2],
                            'first_name': row[3],
                            'last_name': row[4],
                            'is_active': row[5],
                            'is_staff': row[6],
                            'is_superuser': row[7],
                            'date_joined': row[8],
                            'last_login': row[9],
                            'source_schema': schema,
                        }
                        users_to_migrate.append(user_data)
                        self.stdout.write(f"  - {row[1]} (id={row[0]})")
        
        # Check which users already exist in public
        with connection.cursor() as cursor:
            cursor.execute("SET search_path TO public")
            cursor.execute("SELECT id, username FROM auth_user")
            existing_users = {row[1]: row[0] for row in cursor.fetchall()}
        
        self.stdout.write(f"\n\nPublic schema has {len(existing_users)} existing users")
        
        # Separate into new users and existing users
        new_users = []
        existing_to_check = []
        
        for user_data in users_to_migrate:
            if user_data['username'] in existing_users:
                existing_to_check.append(user_data)
            else:
                new_users.append(user_data)
        
        self.stdout.write(f"\nUsers to migrate:")
        self.stdout.write(f"  - New users: {len(new_users)}")
        self.stdout.write(f"  - Already exist in public: {len(existing_to_check)}")
        
        if dry_run:
            self.stdout.write("\n[DRY RUN - No changes made]")
            return
        
        if not new_users and not existing_to_check:
            self.stdout.write("\nNo users to migrate.")
            return
        
        # Confirm migration
        self.stdout.write("\nProceeding with migration...\n")
        
        migrated_count = 0
        error_count = 0
        
        with transaction.atomic():
            with connection.cursor() as cursor:
                cursor.execute("SET search_path TO public")
                
                # Migrate new users
                for user_data in new_users:
                    try:
                        cursor.execute("""
                            INSERT INTO auth_user (id, username, email, first_name, last_name, 
                                                  is_active, is_staff, is_superuser, date_joined, last_login)
                            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        """, [
                            user_data['id'], user_data['username'], user_data['email'],
                            user_data['first_name'], user_data['last_name'],
                            user_data['is_active'], user_data['is_staff'], 
                            user_data['is_superuser'], user_data['date_joined'],
                            user_data['last_login']
                        ])
                        migrated_count += 1
                        self.stdout.write(f"  ✓ Migrated {user_data['username']}")
                    except IntegrityError as e:
                        error_count += 1
                        self.stdout.write(f"  ✗ Failed to migrate {user_data['username']}: {e}")
                
                # Check existing users match
                for user_data in existing_to_check:
                    public_id = existing_users[user_data['username']]
                    if public_id != user_data['id']:
                        self.stdout.write(
                            f"  ! User {user_data['username']} exists in public with different ID "
                            f"(public={public_id}, {user_data['source_schema']}={user_data['id']})"
                        )
        
        self.stdout.write(f"\n=== Migration Complete ===")
        self.stdout.write(f"Migrated: {migrated_count}")
        self.stdout.write(f"Errors: {error_count}")
        self.stdout.write(f"Already in public: {len(existing_to_check)}")
