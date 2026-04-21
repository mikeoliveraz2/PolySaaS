import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
django.setup()

from django.db import connection

def add_missing_columns():
    cursor = connection.cursor()
    print('Adding missing columns to dose_userprofile table...')
    
    columns_to_add = [
        ("last_selected_theme", "VARCHAR(50)", "flatly"),
        ("light_theme", "VARCHAR(50)", "flatly"),
        ("dark_theme", "VARCHAR(50)", "darkly"),
        ("use_system_pref", "BOOLEAN", "FALSE")
    ]
    
    for column_name, column_type, default_value in columns_to_add:
        try:
            if column_type == "BOOLEAN":
                sql = f"ALTER TABLE dose_userprofile ADD COLUMN {column_name} {column_type} DEFAULT {default_value};"
            else:
                sql = f"ALTER TABLE dose_userprofile ADD COLUMN {column_name} {column_type} DEFAULT '{default_value}';"
            
            cursor.execute(sql)
            print(f"✓ Added {column_name} column")
        except Exception as e:
            print(f"⚠ {column_name}: {e}")
    
    # Verify the columns were added
    cursor.execute("SELECT column_name, data_type FROM information_schema.columns WHERE table_name = 'dose_userprofile' ORDER BY ordinal_position;")
    columns = cursor.fetchall()
    print("\nCurrent columns in dose_userprofile:")
    for col_name, col_type in columns:
        print(f"  {col_name} - {col_type}")
    
    print("\nDatabase schema update completed!")

if __name__ == "__main__":
    add_missing_columns()