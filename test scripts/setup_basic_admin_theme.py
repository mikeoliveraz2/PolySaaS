#!/usr/bin/env python
"""
Simple setup for django-admin-interface with basic D.O.S.E. theme
"""
import os
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
django.setup()

from admin_interface.models import Theme

def setup_basic_dose_theme():
    """Create a basic D.O.S.E. theme for admin interface."""
    
    print("⚙️ Setting up Basic D.O.S.E. Admin Theme")
    print("=" * 45)
    
    try:
        # Simple theme creation with minimal required fields
        theme, created = Theme.objects.get_or_create(
            name='D.O.S.E. Technology Platform',
            defaults={
                'active': True,
                'title': 'D.O.S.E. Administration',
                'title_visible': True,
            }
        )
        
        if created:
            print("✅ Created D.O.S.E. admin theme")
        else:
            print("🔄 Found existing D.O.S.E. theme")
            theme.active = True
            theme.title = 'D.O.S.E. Administration'
            theme.save()
        
        print(f"\n📋 Theme Details:")
        print(f"  Name: {theme.name}")
        print(f"  Title: {theme.title}")
        print(f"  Active: {theme.active}")
        
        # Show all available themes
        all_themes = Theme.objects.all()
        print(f"\n🎨 Available Themes ({all_themes.count()}):")
        
        for t in all_themes:
            status = "🟢 Active" if t.active else "⚪ Inactive"
            print(f"  • {t.name}: {status}")
        
        print(f"\n📍 Next Steps:")
        print(f"  1. Visit: http://127.0.0.1:8000/admin/")
        print(f"  2. Look for improved admin interface styling")
        print(f"  3. Go to: http://127.0.0.1:8000/admin/admin_interface/theme/")
        print(f"  4. Customize colors and appearance as needed")
        
        print(f"\n✅ Basic D.O.S.E. admin interface ready!")
        
    except Exception as e:
        print(f"❌ Error setting up theme: {e}")
        print("💡 Try visiting http://127.0.0.1:8000/admin/admin_interface/theme/ manually")

if __name__ == "__main__":
    setup_basic_dose_theme()
