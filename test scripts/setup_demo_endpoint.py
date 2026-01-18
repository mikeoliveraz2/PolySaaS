#!/usr/bin/env python
"""
Setup Demo Passthrough Endpoint
Creates a simple test service endpoint for investor demo
No authentication required - works immediately!
"""
import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
django.setup()

from dose.models import PassThroughEndpoint
from django.contrib.auth import get_user_model

User = get_user_model()

def setup_demo_endpoint():
    """Create a demo passthrough endpoint using the test service"""

    # Test service URL (runs on localhost:5000)
    test_service_url = "http://localhost:5000"

    # Check if endpoint already exists
    existing = PassThroughEndpoint.objects.filter(trigger_path='monitor-logger').first()

    if existing:
        print(f"Monitor Logger endpoint already exists!")
        print(f"   Trigger: {existing.trigger_path}")
        print(f"   URL: {existing.endpoint_url}")
        print(f"   Enabled: {existing.is_enabled}")
        print(f"   Bypass: {existing.bypass_middleware}")
        print(f"\n   To update, delete it first or modify manually in admin.")
        return existing

    # Create new endpoint
    endpoint = PassThroughEndpoint.objects.create(
        trigger_path='monitor-logger',  # Will match /pt/admin/monitor-logger/
        endpoint_url=test_service_url,
        passthrough_type='scraper',  # HTML content
        bypass_middleware=True,  # Let the view handle it
        is_enabled=True,
        description='Real-time monitoring and logging service - intercepts and logs events',
        menu_title='Monitor Logger',
        menu_icon='📊',
        provider='custom',
        show_in_menu=True,
    )

    print("Monitor Logger endpoint created successfully!")
    print(f"\nConfiguration:")
    print(f"   Trigger Path: {endpoint.trigger_path}")
    print(f"   Endpoint URL: {endpoint.endpoint_url}")
    print(f"   Type: {endpoint.passthrough_type}")
    print(f"   Bypass Middleware: {endpoint.bypass_middleware}")
    print(f"   Enabled: {endpoint.is_enabled}")
    print(f"   Show in Menu: {endpoint.show_in_menu}")

    print(f"\nAccess the Monitor Logger at:")
    print(f"   http://localhost:8000/pt/admin/monitor-logger/")
    print(f"   http://localhost:8000/pt/admin/monitor-logger/any/path/here")

    print(f"\nNext steps:")
    print(f"   1. Start the monitoring service: cd pass_through_service && python app.py")
    print(f"   2. Access http://localhost:8000/pt/admin/monitor-logger/ in your browser")
    print(f"   3. You should see the monitoring dashboard")

    return endpoint

if __name__ == '__main__':
    print("="*60)
    print("Setting up Demo Passthrough Endpoint")
    print("="*60)
    print()

    endpoint = setup_demo_endpoint()

    print()
    print("="*60)
    print("Setup complete!")
    print("="*60)

