#!/usr/bin/env python
import os, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
django.setup()

from django.db import connection

with connection.cursor() as c:
    c.execute('SET search_path TO "polysaast15"')
    c.execute('''
        SELECT column_name FROM information_schema.columns 
        WHERE table_name = 'dose_tenantapp' 
        ORDER BY ordinal_position
    ''')
    print('Columns in dose_tenantapp:')
    for row in c.fetchall():
        print(f'  - {row[0]}')
