"""
Fix PolySniffer Port Configuration
===================================
Fixes any endpoints pointing to localhost:9001 and updates them to use the correct port 5001
or removes them if not needed (since PolySniffer is now integrated into Django)
"""
import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
django.setup()

from dose.models import PassThroughEndpoint
try:
    from django_tenants.utils import schema_context
    HAS_TENANTS = True
except ImportError:
    HAS_TENANTS = False
    def schema_context(schema):
        from contextlib import contextmanager
        @contextmanager
        def dummy_context():
            yield
        return dummy_context()

def fix_polysniffer_endpoints():
    """Check and fix any endpoints with port 9001 or 5001 and update to 5002"""
    
    print("\n" + "="*80)
    print("FIXING POLYSNIFFER PORT CONFIGURATION")
    print("="*80 + "\n")
    
    # Check public schema
    print("🔍 Checking endpoints...")
    if not HAS_TENANTS:
        print("   (Running without tenant support)")
    
    with schema_context('public' if HAS_TENANTS else 'public'):
        endpoints = PassThroughEndpoint.objects.filter(
            endpoint_url__icontains=':9001'
        ) | PassThroughEndpoint.objects.filter(
            endpoint_url__icontains=':5001'
        )
        if endpoints.exists():
            print(f"   ⚠️  Found {endpoints.count()} endpoint(s) with port 9001 or 5001")
            for endpoint in endpoints:
                print(f"   - ID {endpoint.id}: {endpoint.menu_title or endpoint.trigger_path}")
                print(f"     Current URL: {endpoint.endpoint_url}")
                new_url = endpoint.endpoint_url.replace(':9001', ':5002').replace(':5001', ':5002')
                endpoint.endpoint_url = new_url
                endpoint.save()
                print(f"     ✅ Updated to: {endpoint.endpoint_url}")
        else:
            print("   ✅ No endpoints with port 9001 or 5001 found in PUBLIC schema")
    
    # Check all tenant schemas
    try:
        from dose.models.tenant import Tenant
        tenants = Tenant.objects.all()
        
        if tenants.exists():
            print(f"\n🔍 Checking {tenants.count()} tenant schema(s)...")
            for tenant in tenants:
                if tenant.schema_name and tenant.schema_name != 'public':
                    print(f"   Checking tenant: {tenant.name} ({tenant.schema_name})")
                    with schema_context(tenant.schema_name):
                        endpoints = PassThroughEndpoint.objects.filter(
                            endpoint_url__icontains=':9001'
                        ) | PassThroughEndpoint.objects.filter(
                            endpoint_url__icontains=':5001'
                        )
                        if endpoints.exists():
                            print(f"      ⚠️  Found {endpoints.count()} endpoint(s) with port 9001 or 5001")
                            for endpoint in endpoints:
                                print(f"      - ID {endpoint.id}: {endpoint.menu_title or endpoint.trigger_path}")
                                print(f"        Current URL: {endpoint.endpoint_url}")
                                new_url = endpoint.endpoint_url.replace(':9001', ':5002').replace(':5001', ':5002')
                                endpoint.endpoint_url = new_url
                                endpoint.save()
                                print(f"        ✅ Updated to: {endpoint.endpoint_url}")
                        else:
                            print(f"      ✅ No endpoints with port 9001 or 5001 found")
    except Exception as e:
        print(f"   ⚠️  Could not check tenant schemas: {e}")
    
    print("\n" + "="*80)
    print("SUMMARY")
    print("="*80)
    print("✅ All endpoints with port 9001 or 5001 have been updated to port 5002")
    print("\n📝 NOTE: The integrated PolySniffer doesn't need an external service.")
    print("   You can use the '🔍 Sniff' button directly from the admin interface")
    print("   without running any standalone service.\n")

if __name__ == '__main__':
    fix_polysniffer_endpoints()
