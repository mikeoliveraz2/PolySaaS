#!/usr/bin/env python
"""
Verify imported D.O.S.E. themes in admin interface
"""
import os
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
django.setup()

from admin_interface.models import Theme

def verify_imported_themes():
    """Verify that D.O.S.E. themes were imported successfully."""
    
    print("🔍 Verifying D.O.S.E. Theme Import")
    print("=" * 40)
    
    # Check for D.O.S.E. themes
    dose_themes = Theme.objects.filter(name__startswith='D.O.S.E.').order_by('name')
    
    print(f"📊 Found {dose_themes.count()} D.O.S.E. themes:")
    
    if dose_themes.exists():
        for theme in dose_themes:
            status = "🟢 ACTIVE" if theme.active else "⚪ Inactive" 
            print(f"  • {theme.name}: {status}")
            print(f"    Title: {theme.title}")
            if hasattr(theme, 'env_name') and theme.env_name:
                print(f"    Environment: {theme.env_name}")
    else:
        print("  ⚠️  No D.O.S.E. themes found")
        return
    
    # Check all available theme fields for debugging
    print(f"\n🔧 Available Theme Model Fields:")
    field_names = [f.name for f in Theme._meta.fields]
    
    color_fields = [f for f in field_names if 'color' in f.lower()]
    print(f"  Color fields ({len(color_fields)}):")
    for field in sorted(color_fields)[:10]:  # Show first 10
        print(f"    • {field}")
    
    if len(color_fields) > 10:
        print(f"    ... and {len(color_fields) - 10} more")
    
    # Show current active theme
    active_theme = Theme.objects.filter(active=True).first()
    if active_theme:
        print(f"\n🎯 Currently Active Theme:")
        print(f"  • {active_theme.name}")
        print(f"  • Title: {active_theme.title}")
    else:
        print(f"\n⚠️  No active theme found")
    
    print(f"\n📍 Next Steps:")
    print(f"  1. Visit: http://127.0.0.1:8000/admin/admin_interface/theme/")
    print(f"  2. You should see all D.O.S.E. themes listed")
    print(f"  3. Click 'Edit' on any theme to customize colors") 
    print(f"  4. Set one theme as 'Active' to apply it")
    print(f"  5. Visit any admin page to see the theme in action")
    
    print(f"\n✅ Theme verification complete!")

if __name__ == "__main__":
    verify_imported_themes()
