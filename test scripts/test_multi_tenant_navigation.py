#!/usr/bin/env python
"""
Simple Multi-Tenant Navigation Test

This script tests if PassThroughEndpoint creates NavigationItems for all tenants.
"""
import os
import sys
import django

# Add the project directory to Python path
project_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(project_dir)

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
django.setup()

def test_multi_tenant_navigation():
    """Test that PassThroughEndpoint creates NavigationItems for all tenants"""
    from dose.models import PassThroughEndpoint, NavigationPanel, NavigationItem, Tenant
    
    print("🧪 Testing Multi-Tenant Navigation Creation")
    print("="*50)
    
    # Get current state
    tenants = list(Tenant.objects.all())
    print(f"📊 Current tenants: {len(tenants)}")
    for tenant in tenants:
        print(f"   - {tenant.name} (ID: {tenant.id})")
    
    # Clean up any existing test data
    print("\n🧹 Cleaning up existing test data...")
    test_endpoints = PassThroughEndpoint.objects.filter(description__contains="Multi-Tenant Test")
    if test_endpoints.exists():
        print(f"   - Deleting {test_endpoints.count()} existing test endpoints")
        test_endpoints.delete()
    
    # Count existing navigation items before test
    nav_items_before = NavigationItem.objects.count()
    print(f"📊 Navigation items before test: {nav_items_before}")
    
    # Create a test passthrough endpoint with menu integration
    print("\n📝 Creating test PassThroughEndpoint with menu integration...")
    test_endpoint = PassThroughEndpoint.objects.create(
        endpoint_url="https://test-service.example.com/",
        trigger_path="/dose/test-service/",
        description="Multi-Tenant Test Service",
        is_enabled=True,
        show_in_menu=True,
        menu_title="Test Service",
        menu_icon="🧪",
        menu_sort_order=1
    )
    print(f"✅ Created PassThroughEndpoint: {test_endpoint.endpoint_url}")
    
    # Check navigation items after creation
    nav_items_after = NavigationItem.objects.count()
    print(f"📊 Navigation items after creation: {nav_items_after}")
    print(f"📊 New navigation items created: {nav_items_after - nav_items_before}")
    
    # Check navigation items for each tenant
    print("\n🔍 Checking navigation items by tenant...")
    for tenant in tenants:
        tenant_nav_items = NavigationItem.objects.filter(
            panel__tenant=tenant,
            title="Test Service"
        )
        print(f"   - {tenant.name}: {tenant_nav_items.count()} navigation items")
        
        if tenant_nav_items.exists():
            nav_item = tenant_nav_items.first()
            print(f"     URL: {nav_item.url}")
            print(f"     Panel: {nav_item.panel.title}")
            print(f"     Active: {nav_item.is_active}")
    
    # Check external services panels
    print("\n🔍 Checking External Services panels...")
    external_panels = NavigationPanel.objects.filter(title="External Services")
    print(f"📊 External Services panels: {external_panels.count()}")
    for panel in external_panels:
        items_count = NavigationItem.objects.filter(panel=panel).count()
        print(f"   - Tenant {panel.tenant.name}: {items_count} items")
    
    # Test update functionality
    print("\n🔄 Testing update functionality...")
    test_endpoint.menu_title = "Updated Test Service"
    test_endpoint.menu_icon = "🔄"
    test_endpoint.save()
    print("✅ Updated PassThroughEndpoint")
    
    # Check if navigation items were updated
    updated_items = NavigationItem.objects.filter(title="Updated Test Service")
    print(f"📊 Updated navigation items: {updated_items.count()}")
    
    # Test disabling menu integration
    print("\n❌ Testing disable menu integration...")
    test_endpoint.show_in_menu = False
    test_endpoint.save()
    print("✅ Disabled menu integration")
    
    # Check if navigation items were removed
    remaining_items = NavigationItem.objects.filter(
        url="/dose/test-service/",
        description__contains="external service"
    )
    print(f"📊 Remaining navigation items: {remaining_items.count()}")
    
    # Final cleanup
    print("\n🧹 Final cleanup...")
    test_endpoint.delete()
    print("✅ Deleted test endpoint")
    
    # Final count
    nav_items_final = NavigationItem.objects.count()
    print(f"📊 Final navigation items count: {nav_items_final}")
    
    print("\n✅ Multi-tenant navigation test completed!")
    
    # Summary
    expected_items_per_endpoint = len(tenants)
    print(f"\n📋 Test Summary:")
    print(f"   - Tenants in system: {len(tenants)}")
    print(f"   - Expected nav items per endpoint: {expected_items_per_endpoint}")
    print(f"   - Items created during test: {nav_items_after - nav_items_before}")
    print(f"   - Items remaining after cleanup: {nav_items_final - nav_items_before}")
    
    if nav_items_after - nav_items_before >= expected_items_per_endpoint:
        print("✅ PASS: Navigation items created for multiple tenants")
    else:
        print("❌ FAIL: Navigation items not created for all tenants")

if __name__ == "__main__":
    test_multi_tenant_navigation()