import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
os.chdir(ROOT)
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "mysite.settings")

import django
django.setup()

from django.contrib.auth import authenticate, get_user_model

User = get_user_model()
for name in ("olientAdmin", "olientadmin", "olientAdmin"):
    u = User.objects.filter(username__iexact=name).first()
    print(f"user {name!r} exists:", bool(u), "active:", getattr(u, "is_active", None) if u else None)

auth = authenticate(username="olientAdmin", password="olientPasswor123!")
print("authenticate olientAdmin:", auth)
