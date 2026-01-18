#!/usr/bin/env python
"""
Test tenant-specific theming on landing page
"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
django.setup()

from dose.tenant_utils import get_tenant_theme_colors

def test_all_themes():
    """Test all available tenant themes"""
    themes = ['tech_blue', 'forest_green', 'royal_purple', 'sunset_orange', 'steel_gray']
    
    print("🎨 Testing D.O.S.E. Tenant Theme System")
    print("=" * 50)
    
    for theme in themes:
        colors = get_tenant_theme_colors(theme)
        print(f"\n📋 {colors['name']} Theme:")
        print(f"   Primary: {colors['primary']}")
        print(f"   Secondary: {colors['secondary']}")
        print(f"   Gradient: {colors['gradient']}")
        
    print("\n✅ All themes loaded successfully!")
    print("\nNow when you switch tenants or admin themes, the landing page")
    print("will automatically adapt to show the tenant-specific colors!")

if __name__ == '__main__':
    test_all_themes()
