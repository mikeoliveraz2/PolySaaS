#!/usr/bin/env python
"""
Setup PolySysMon PassThroughEndpoint for PolySaaS
Configures PolySysMon as a passthrough service for dynamic orchestration
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
django.setup()

from dose.models import PassThroughEndpoint

print("="*60)
print("Setting Up PolySysMon Passthrough Endpoint")
print("="*60)
print()

# PolySysMon configuration
TRIGGER_PATH = 'polysysmon'  # Will match /pt/admin/polysysmon/ and /pt/dose/polysysmon/
ENDPOINT_URL = 'http://localhost:8081'  # Docker PolySysMon container

# Check if endpoint already exists
existing = PassThroughEndpoint.objects.filter(
    trigger_path__iexact='polysysmon'
).first()

if existing:
    print(f"Found existing PolySysMon endpoint ID: {existing.id}")
    print(f"  Current trigger_path: {existing.trigger_path}")
    print(f"  Current endpoint_url: {existing.endpoint_url}")
    print()
    
    # Update configuration
    print("Updating PolySysMon endpoint configuration...")
    existing.trigger_path = TRIGGER_PATH
    existing.endpoint_url = ENDPOINT_URL
    existing.is_enabled = True
    existing.show_in_menu = True
    existing.menu_title = 'PolySysMon'
    existing.menu_icon = '🖥️'
    existing.passthrough_type = 'scraper'  # PolySysMon is HTML-based
    existing.bypass_middleware = False  # Let middleware handle it
    existing.provider = 'custom'
    existing.integration_mode = 'web_only'
    existing.description = 'PolySysMon - Proactive system monitoring and alerting'
    existing.save()
    
    endpoint = existing
    print("✅ Update complete!")
else:
    print("Creating new PolySysMon endpoint...")
    endpoint = PassThroughEndpoint.objects.create(
        trigger_path=TRIGGER_PATH,
        endpoint_url=ENDPOINT_URL,
        is_enabled=True,
        show_in_menu=True,
        menu_title='PolySysMon',
        menu_icon='🖥️',
        passthrough_type='scraper',
        bypass_middleware=False,
        provider='custom',
        integration_mode='web_only',
        description='PolySysMon - Proactive system monitoring and alerting',
    )
    print(f"✅ Created endpoint ID: {endpoint.id}")

print()
print("="*60)
print("PolySysMon Endpoint Configuration:")
print("="*60)
print(f"  ID: {endpoint.id}")
print(f"  Trigger Path: {endpoint.trigger_path}")
print(f"  Endpoint URL: {endpoint.endpoint_url}")
print(f"  Menu Title: {endpoint.menu_title}")
print(f"  Show in Menu: {endpoint.show_in_menu}")
print(f"  Enabled: {endpoint.is_enabled}")
print(f"  Passthrough Type: {endpoint.passthrough_type}")
print(f"  Bypass Middleware: {endpoint.bypass_middleware}")
print(f"  Provider: {endpoint.provider}")
print(f"  Integration Mode: {endpoint.integration_mode}")
print()
print("="*60)
print("Access URLs:")
print("="*60)
print("  - http://localhost:8000/pt/admin/polysysmon/")
print("  - http://localhost:8000/pt/dose/polysysmon/")
print()
print("="*60)
print("Next Steps:")
print("="*60)
print("""
1. Start your Django PolySaaS server:
   python manage.py runserver

2. Access PolySysMon through PolySaaS middleware:
   http://localhost:8000/pt/admin/polysysmon/

3. PolySysMon will appear in the admin navigation menu

4. Use PolySniffer to capture PolySysMon traffic patterns

5. The middleware will dynamically orchestrate requests between
   PolySaaS and PolySysMon, enabling multi-tenant monitoring.
""")
