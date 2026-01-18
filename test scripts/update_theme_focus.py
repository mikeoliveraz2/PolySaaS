#!/usr/bin/env python
"""
Update tenant themes from medical focus to technology focus
"""
import os
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
django.setup()

from dose.models import Tenant

def update_tenant_themes():
    """Update tenant themes to technology-focused naming."""
    
    print("🔧 Updating D.O.S.E. Themes - Technology Focus")
    print("=" * 50)
    print("D.O.S.E. = Dynamic Orchestration Service Engine")
    print("=" * 50)
    
    # Update medical_blue to tech_blue
    updated_count = 0
    tenants = Tenant.objects.filter(admin_theme='medical_blue')
    
    if tenants.exists():
        print(f"📝 Updating {tenants.count()} tenants from 'medical_blue' to 'tech_blue'")
        
        for tenant in tenants:
            tenant.admin_theme = 'tech_blue'
            tenant.save()
            updated_count += 1
            print(f"  ✅ Updated: {tenant.name}")
    
    print(f"\n🎨 Current Available Themes:")
    for value, display in Tenant.THEME_CHOICES:
        print(f"  • {value}: {display}")
    
    print(f"\n📊 Theme Summary:")
    all_tenants = Tenant.objects.all()
    theme_counts = {}
    
    for tenant in all_tenants:
        theme = tenant.admin_theme
        theme_counts[theme] = theme_counts.get(theme, 0) + 1
        
    for theme, count in theme_counts.items():
        theme_display = next((display for value, display in Tenant.THEME_CHOICES if value == theme), theme)
        print(f"  {theme}: {count} organizations ({theme_display})")
    
    print(f"\n✅ Theme update complete!")
    print(f"📝 Updated {updated_count} organizations")
    print(f"🚀 D.O.S.E. now properly reflects: Dynamic Orchestration Service Engine")

if __name__ == "__main__":
    update_tenant_themes()
