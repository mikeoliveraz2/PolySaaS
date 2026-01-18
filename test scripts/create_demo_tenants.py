#!/usr/bin/env python
"""
Create demo tenants with different themes for testing
"""
import os
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
django.setup()

from dose.models import Tenant, UserProfile
from django.contrib.auth.models import User

def create_demo_tenants():
    """Create sample tenants with different themes for demonstration."""
    
    print("⚙️ Creating Demo Organizations with D.O.S.E. Themes")
    print("=" * 60)
    print("D.O.S.E. = Dynamic Orchestration Service Engine")
    print("=" * 60)
    
    demo_tenants = [
        {
            'name': 'TechCorp Industries',
            'slug': 'techcorp-industries',
            'theme': 'tech_blue',
            'tagline': 'Excellence in Service Orchestration',
            'description': 'A leading technology corporation providing comprehensive orchestration services.'
        },
        {
            'name': 'GreenTech Solutions',
            'slug': 'greentech-solutions',
            'theme': 'forest_green', 
            'tagline': 'Sustainable Computing Environment',
            'description': 'Focused on eco-friendly and sustainable technology practices.'
        },
        {
            'name': 'Premium Platform Corp',
            'slug': 'premium-platform',
            'theme': 'royal_purple',
            'tagline': 'Enterprise-Grade Service Platform',
            'description': 'Luxury enterprise services with world-class infrastructure.'
        },
        {
            'name': 'Dynamic Systems LLC',
            'slug': 'dynamic-systems',
            'theme': 'sunset_orange',
            'tagline': 'Bringing Energy to Orchestration',
            'description': 'Community-focused platform providing accessible service orchestration.'
        },
        {
            'name': 'Steel City Computing',
            'slug': 'steel-city-computing',
            'theme': 'steel_gray',
            'tagline': 'Industrial Strength Technology',
            'description': 'Corporate computing solutions with cutting-edge orchestration technology.'
        }
    ]
    
    created_count = 0
    updated_count = 0
    
    for tenant_data in demo_tenants:
        try:
            tenant, created = Tenant.objects.get_or_create(
                slug=tenant_data['slug'],
                defaults={
                    'name': tenant_data['name'],
                    'admin_theme': tenant_data['theme'],
                    'tagline': tenant_data['tagline'],
                    'description': tenant_data['description']
                }
            )
            
            if created:
                created_count += 1
                print(f"✅ Created: {tenant.name} ({tenant.get_admin_theme_display()})")
            else:
                # Update theme if tenant exists
                tenant.admin_theme = tenant_data['theme']
                tenant.tagline = tenant_data['tagline']
                tenant.description = tenant_data['description']
                tenant.save()
                updated_count += 1
                print(f"🔄 Updated: {tenant.name} ({tenant.get_admin_theme_display()})")
                
        except Exception as e:
            print(f"❌ Error with {tenant_data['name']}: {e}")
    
    print(f"\n📊 Summary:")
    print(f"  🆕 Created: {created_count} tenants")
    print(f"  🔄 Updated: {updated_count} tenants")
    
    # Show all tenants with themes
    print(f"\n🎨 Current Organization Themes:")
    print(f"{'Name':<35} {'Theme':<25} {'Tagline':<30}")
    print("-" * 92)
    
    all_tenants = Tenant.objects.all().order_by('name')
    for tenant in all_tenants:
        name = tenant.name[:34] if len(tenant.name) > 34 else tenant.name
        theme = tenant.get_admin_theme_display()[:24] if len(tenant.get_admin_theme_display()) > 24 else tenant.get_admin_theme_display()
        tagline = tenant.tagline[:29] if tenant.tagline and len(tenant.tagline) > 29 else (tenant.tagline or "")
        print(f"{name:<35} {theme:<25} {tagline:<30}")
    
    print(f"\n🧪 Testing Instructions:")
    print(f"1. Create user profiles for different organizations:")
    print(f"   python manage.py shell")
    print(f"   from dose.models import UserProfile, Tenant")
    print(f"   from django.contrib.auth.models import User")
    print(f"   ")
    print(f"2. Create test users and assign to organizations:")
    print(f"   user = User.objects.create_user('testuser', 'test@example.com', 'password')")
    print(f"   tenant = Tenant.objects.get(slug='techcorp-industries')")
    print(f"   UserProfile.objects.create(user=user, tenant=tenant)")
    print(f"   ")
    print(f"3. Login as that user and see the themed admin interface!")
    print(f"   ")
    print(f"4. Or use the management command:")
    print(f"   python manage.py set_tenant_theme 'TechCorp' forest_green")
    
    print(f"\n🌐 Admin URLs to test:")
    print(f"  • Organization List: http://127.0.0.1:8000/admin/dose/tenant/")
    print(f"  • User Management: http://127.0.0.1:8000/admin/auth/user/")
    print(f"  • User Profiles: http://127.0.0.1:8000/admin/dose/userprofile/")
    
    print(f"\n🚀 Demo organizations created! Each will show a different theme when accessed by their users.")
    print(f"⚙️ D.O.S.E. = Dynamic Orchestration Service Engine")

if __name__ == "__main__":
    create_demo_tenants()
