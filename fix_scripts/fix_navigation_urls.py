#!/usr/bin/env python
"""
Fix Navigation URLs Script

This script updates existing navigation items to include the correct port numbers
and fixes any relative URLs to be absolute URLs with localhost:8000.
"""
import os
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
django.setup()

from dose.models import NavigationItem

def fix_navigation_urls():
    """Fix navigation URLs to include proper port numbers and be absolute"""
    
    print("🔧 Fixing Navigation URLs...")
    print("="*50)
    
    # URL mappings for common fixes
    url_fixes = {
        '/admin/dose/task/add/': 'http://localhost:8000/admin/dose/task/add/',
        '/admin/dose/instruction/add/': 'http://localhost:8000/admin/dose/instruction/add/',
        '/dose/': 'http://localhost:8000/dose/',
        '/dose/reports/usage/': 'http://localhost:8000/dose/reports/usage/',
        '/dose/reports/performance/': 'http://localhost:8000/dose/reports/performance/',
        '/dose/export/csv/': 'http://localhost:8000/dose/export/csv/',
        '/admin/auth/user/': 'http://localhost:8000/admin/auth/user/',
        '/admin/dose/tenant/': 'http://localhost:8000/admin/dose/tenant/',
    }
    
    updated_count = 0
    
    for item in NavigationItem.objects.all():
        original_url = item.url
        
        # Check if this URL needs fixing
        if original_url in url_fixes:
            item.url = url_fixes[original_url]
            item.save()
            print(f"  ✅ Updated: '{item.title}' - {original_url} → {item.url}")
            updated_count += 1
        elif original_url.startswith('/') and not original_url.startswith('http'):
            # Fix any other relative URLs
            item.url = f'http://localhost:8000{original_url}'
            item.save()
            print(f"  ✅ Updated: '{item.title}' - {original_url} → {item.url}")
            updated_count += 1
    
    print("\n" + "="*50)
    print(f"📊 SUMMARY: Updated {updated_count} navigation URLs")
    
    if updated_count > 0:
        print("\n🎉 Navigation URLs have been fixed!")
        print("🚀 You can now test the navigation links on the landing page.")
    else:
        print("\n✨ All navigation URLs were already correct!")

def display_all_urls():
    """Display all current navigation URLs for verification"""
    print("\n📋 Current Navigation URLs:")
    print("="*60)
    
    for item in NavigationItem.objects.select_related('panel').all():
        tenant_name = item.panel.tenant.name
        panel_title = item.panel.title
        print(f"  🏢 {tenant_name} | {panel_title} | {item.title}")
        print(f"     URL: {item.url}")
        print(f"     Type: {item.item_type} | Target: {item.target}")
        print()

if __name__ == "__main__":
    print("🚀 D.O.S.E. Navigation URL Fix Script")
    print("="*50)
    
    try:
        fix_navigation_urls()
        display_all_urls()
        
        print("\n" + "="*60)
        print("✅ SCRIPT COMPLETE!")
        print("="*60)
        print("Next steps:")
        print("1. Test the navigation links on the landing page: http://localhost:8000/dose/landing/")
        print("2. Try adding a new task: http://localhost:8000/admin/dose/task/add/")
        print("3. Verify all links work with the correct port number")
        
    except Exception as e:
        print(f"\n❌ Error fixing navigation URLs: {e}")
        import traceback
        traceback.print_exc()
