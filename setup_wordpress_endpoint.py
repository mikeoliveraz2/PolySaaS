#!/usr/bin/env python
"""
Setup WordPress PassThroughEndpoint for PolySaaS
Configures WordPress as a passthrough service for dynamic orchestration
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
django.setup()

from dose.models import PassThroughEndpoint

print("="*60)
print("Setting Up WordPress Passthrough Endpoint")
print("="*60)
print()

# WordPress configuration
TRIGGER_PATH = 'wordpress'  # Will match /pt/admin/wordpress/ and /pt/dose/wordpress/
ENDPOINT_URL = 'http://localhost:8980'  # Docker WordPress container

# Check if endpoint already exists
existing = PassThroughEndpoint.objects.filter(
    trigger_path__iexact='wordpress'
).first()

if existing:
    print(f"Found existing WordPress endpoint ID: {existing.id}")
    print(f"  Current trigger_path: {existing.trigger_path}")
    print(f"  Current endpoint_url: {existing.endpoint_url}")
    print()
    
    # Update configuration
    print("Updating WordPress endpoint configuration...")
    existing.trigger_path = TRIGGER_PATH
    existing.endpoint_url = ENDPOINT_URL
    existing.is_enabled = True
    existing.show_in_menu = True
    existing.menu_title = 'WordPress'
    existing.menu_icon = 'ðŸ"'
    existing.passthrough_type = 'scraper'  # WordPress is HTML-based
    existing.bypass_middleware = False  # Let middleware handle it
    existing.provider = 'custom'  # Use custom provider for WordPress
    existing.integration_mode = 'web_only'
    existing.description = 'WordPress CMS passthrough with Bricks theme'
    existing.save()
    
    endpoint = existing
    print("â Update complete!")
else:
    print("Creating new WordPress endpoint...")
    endpoint = PassThroughEndpoint.objects.create(
        trigger_path=TRIGGER_PATH,
        endpoint_url=ENDPOINT_URL,
        is_enabled=True,
        show_in_menu=True,
        menu_title='WordPress',
        menu_icon='ðŸ"',
        passthrough_type='scraper',
        bypass_middleware=False,
        provider='custom',  # Use custom provider for WordPress
        integration_mode='web_only',
        description='WordPress CMS passthrough with Bricks theme',
    )
    print(f"â Created endpoint ID: {endpoint.id}")

print()
print("="*60)
print("WordPress Endpoint Configuration:")
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
print("  - http://localhost:8000/pt/admin/wordpress/")
print("  - http://localhost:8000/pt/dose/wordpress/")
print()
print("="*60)
print("Next Steps:")
print("="*60)
print("""
1. Start PolySniffer to capture WordPress traffic:
   python polysniffer_final_for_real.py

2. Access WordPress through PolySaaS middleware:
   http://localhost:8000/pt/admin/wordpress/

3. Use WordPress admin:
   - Username: wpadmin
   - Password: admin123

4. PolySniffer will capture all traffic patterns for analysis

5. The middleware will dynamically orchestrate requests between
   PolySaaS and WordPress, enabling multi-tenant capabilities.
""")
