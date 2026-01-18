#!/usr/bin/env python
"""
Add admin_theme column to tenant table directly
"""
import os
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
django.setup()

from django.db import connection

def add_admin_theme_column():
    """Add admin_theme column to dose_tenant table."""
    
    print("🔧 Adding admin_theme column to Tenant table")
    print("=" * 50)
    
    with connection.cursor() as cursor:
        try:
            # Check if column already exists
            cursor.execute("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name='dose_tenant' 
                AND column_name='admin_theme';
            """)
            
            if cursor.fetchone():
                print("✅ admin_theme column already exists!")
                
                # Just update the existing records to have default theme
                cursor.execute("""
                    UPDATE dose_tenant 
                    SET admin_theme = 'medical_blue' 
                    WHERE admin_theme IS NULL OR admin_theme = '';
                """)
                
                updated = cursor.rowcount
                print(f"📝 Updated {updated} tenant records with default theme")
                
            else:
                # Add the column
                print("➕ Adding admin_theme column...")
                cursor.execute("""
                    ALTER TABLE dose_tenant 
                    ADD COLUMN admin_theme VARCHAR(20) DEFAULT 'medical_blue';
                """)
                print("✅ Column added successfully!")
                
                # Set default values for existing records
                cursor.execute("""
                    UPDATE dose_tenant 
                    SET admin_theme = 'medical_blue' 
                    WHERE admin_theme IS NULL;
                """)
                
                updated = cursor.rowcount
                print(f"📝 Set default theme for {updated} existing tenants")
            
            # Verify the column was added
            cursor.execute("""
                SELECT id, name, admin_theme 
                FROM dose_tenant 
                ORDER BY id;
            """)
            
            tenants = cursor.fetchall()
            print(f"\n📋 Current Tenant Themes:")
            print(f"{'ID':<5} {'Name':<25} {'Theme':<15}")
            print("-" * 47)
            
            for tenant_id, name, theme in tenants:
                name_display = name[:24] if len(name) > 24 else name
                print(f"{tenant_id:<5} {name_display:<25} {theme:<15}")
            
            print(f"\n🎯 Theme Options Available:")
            themes = [
                'medical_blue - 🏥 Medical Blue - Professional Healthcare',
                'forest_green - 🌿 Forest Green - Natural Environment', 
                'royal_purple - 👑 Royal Purple - Premium Experience',
                'sunset_orange - 🌅 Sunset Orange - Warm & Welcoming',
                'steel_gray - 🏗️ Steel Gray - Modern Professional'
            ]
            
            for theme in themes:
                print(f"  • {theme}")
                
        except Exception as e:
            print(f"❌ Error: {e}")
            print("💡 This might be normal if the column already exists")
    
    print(f"\n✅ Database update complete!")
    print(f"🌐 Next: Update admin templates to use tenant themes")

if __name__ == "__main__":
    add_admin_theme_column()
