#!/usr/bin/env python
"""Quick test to verify migration"""
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
django.setup()

from django.db import connection

print("="*60)
print("Checking migration status...")
print("="*60)

with connection.cursor() as cursor:
    # Check PassThroughEndpoint
    cursor.execute("SELECT COUNT(*) FROM olient.dose_passthroughendpoint")
    olient_count = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM public.dose_passthroughendpoint")
    public_count = cursor.fetchone()[0]
    print(f"PassThroughEndpoint: public={public_count}, olient={olient_count}")

    # Check CallBackData
    try:
        cursor.execute("SELECT COUNT(*) FROM olient.dose_callbackdata")
        olient_cb = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM public.dose_callbackdata")
        public_cb = cursor.fetchone()[0]
        print(f"CallBackData: public={public_cb}, olient={olient_cb}")
    except:
        print("CallBackData: table may not exist")

    # Check Instruction
    try:
        cursor.execute("SELECT COUNT(*) FROM olient.dose_instruction")
        olient_inst = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM public.dose_instruction")
        public_inst = cursor.fetchone()[0]
        print(f"Instruction: public={public_inst}, olient={olient_inst}")
    except:
        print("Instruction: table may not exist")

print("="*60)

