#!/usr/bin/env python
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
django.setup()

from admin_interface.models import Theme

print("🔍 Theme Count Check")
print("=" * 30)

all_themes = Theme.objects.all().order_by('name')
print(f"Total themes: {all_themes.count()}")

dose_themes = Theme.objects.filter(name__startswith='D.O.S.E.').order_by('name')
print(f"D.O.S.E. themes: {dose_themes.count()}")

print(f"\n📋 All D.O.S.E. themes:")
for theme in dose_themes:
    status = "🟢 Active" if theme.active else "⚪ Inactive" 
    print(f"  • {theme.name}: {status}")

if dose_themes.count() < 5:
    print(f"\n⚠️  Expected 5+ themes, found {dose_themes.count()}")
    print("🔧 Try running: python import_themes_robust.py")
else:
    print(f"\n✅ All themes imported successfully!")
