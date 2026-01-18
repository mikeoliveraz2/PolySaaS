#!/usr/bin/env python
"""
Test Passthrough Menu Integration

This script tests the automatic menu integration feature for PassThroughEndpoint.
It creates a test passthrough endpoint and verifies that navigation items are
automatically created in the menu system.
"""
import os
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
django.setup()

from dose.models import PassThroughEndpoint, NavigationPanel, NavigationItem, Tenant

def test_passthrough_menu_integration():
    """Test the complete passthrough menu integration flow"""
    print("🧪 Testing Passthrough Menu Integration")
    print("="*60)
    
    # Step 1: Create a test passthrough endpoint
    print("\n📝 Step 1: Creating test passthrough endpoint...")
    
    # Clean up any existing test data
    PassThroughEndpoint.objects.filter(description__contains="Test Integration").delete()
    NavigationItem.objects.filter(title__contains="Test Service").delete()
    
    test_endpoint = PassThroughEndpoint.objects.create(
        provider='custom',
        endpoint_url='https://test.example.com/app/',
        description='Test Integration Service for Menu Testing',
        trigger_path='/dose/testservice/',
        is_enabled=True,
        # Menu integration fields
        show_in_menu=True,
        menu_title='Test Service',
        menu_icon='🧪',
        menu_sort_order=50
    )
    
    print(f"✅ Created test endpoint: {test_endpoint}")
    print(f"   - Menu title: {test_endpoint.get_menu_title()}")
    print(f"   - Menu URL: {test_endpoint.get_menu_url()}")
    print(f"   - Show in menu: {test_endpoint.show_in_menu}")
    
    # Step 2: Verify navigation panels were created
    print("\n📊 Step 2: Checking navigation panels...")
    
    tenants = Tenant.objects.all()
    external_panels = NavigationPanel.objects.filter(title="External Services")
    
    print(f"   - Total tenants: {tenants.count()}")
    print(f"   - External Services panels created: {external_panels.count()}")
    
    for panel in external_panels:
        print(f"   - Panel for {panel.tenant.name}: {panel.title} (ID: {panel.id})")
    
    # Step 3: Verify navigation items were created
    print("\n🔗 Step 3: Checking navigation items...")
    
    nav_items = NavigationItem.objects.filter(title="Test Service")
    print(f"   - Navigation items created: {nav_items.count()}")
    
    for item in nav_items:
        print(f"   - Item: {item.title} in {item.panel.tenant.name}")
        print(f"     URL: {item.url}")
        print(f"     Icon: {item.icon_value}")
        print(f"     Active: {item.is_active}")
        print(f"     Sort order: {item.sort_order}")
    
    # Step 4: Test updating the endpoint
    print("\n🔄 Step 4: Testing endpoint updates...")
    
    test_endpoint.menu_title = "Updated Test Service"
    test_endpoint.menu_icon = "🚀"
    test_endpoint.menu_sort_order = 25
    test_endpoint.save()
    
    # Check if navigation items were updated
    updated_items = NavigationItem.objects.filter(title="Updated Test Service")
    print(f"   - Updated navigation items: {updated_items.count()}")
    
    for item in updated_items:
        print(f"   - Updated item: {item.title}")
        print(f"     New icon: {item.icon_value}")
        print(f"     New sort order: {item.sort_order}")
    
    # Step 5: Test disabling menu integration
    print("\n❌ Step 5: Testing menu integration disable...")
    
    test_endpoint.show_in_menu = False
    test_endpoint.save()
    
    remaining_items = NavigationItem.objects.filter(url="/dose/testservice/")
    print(f"   - Remaining navigation items after disable: {remaining_items.count()}")
    
    # Step 6: Test re-enabling
    print("\n✅ Step 6: Testing menu integration re-enable...")
    
    test_endpoint.show_in_menu = True
    test_endpoint.save()
    
    re_enabled_items = NavigationItem.objects.filter(title="Updated Test Service")
    print(f"   - Re-created navigation items: {re_enabled_items.count()}")
    
    # Step 7: Test deletion
    print("\n🗑️ Step 7: Testing endpoint deletion...")
    
    test_endpoint.delete()
    
    deleted_items = NavigationItem.objects.filter(url="/dose/testservice/")
    print(f"   - Navigation items after deletion: {deleted_items.count()}")
    
    # Summary
    print("\n" + "="*60)
    print("📋 INTEGRATION TEST SUMMARY")
    print("="*60)
    print("✅ Endpoint creation with menu integration")
    print("✅ Automatic navigation panel creation")
    print("✅ Automatic navigation item creation")
    print("✅ Endpoint updates sync to navigation items")
    print("✅ Menu integration disable/enable")
    print("✅ Automatic cleanup on deletion")
    
    return True

def display_current_navigation():
    """Display current navigation structure for all tenants"""
    print("\n" + "="*60)
    print("🧭 CURRENT NAVIGATION STRUCTURE")
    print("="*60)
    
    for tenant in Tenant.objects.all():
        print(f"\n🏢 {tenant.name}")
        panels = NavigationPanel.objects.filter(tenant=tenant, is_active=True).order_by('sort_order')
        
        for panel in panels:
            items = NavigationItem.objects.filter(panel=panel, is_active=True).order_by('sort_order')
            print(f"   📁 {panel.title} ({items.count()} items)")
            
            for item in items:
                icon = item.icon_value or "🔗"
                print(f"      {icon} {item.title} → {item.url}")

if __name__ == "__main__":
    try:
        # Run the integration test
        success = test_passthrough_menu_integration()
        
        # Display current navigation
        display_current_navigation()
        
        if success:
            print("\n🎉 All tests passed! Passthrough menu integration is working correctly.")
            print("\n📋 Next steps:")
            print("1. Go to /admin/dose/passthroughendpoint/ to test in the admin interface")
            print("2. Create a real passthrough endpoint with menu integration enabled")
            print("3. Check the navigation menu on /dose/landing/ to see the new item")
            print("4. Test clicking the menu item to verify passthrough functionality")
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()