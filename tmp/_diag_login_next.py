import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
os.chdir(ROOT)

import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "mysite.settings")
django.setup()

from django.template import Template, Context
from django.test import Client
from urllib.parse import urlencode

print("Template None render:", repr(Template("{{ x }}").render(Context({"x": None}))))

r = Client().get("/accounts/login/")
html = r.content.decode()
for m in re.finditer(r'name="next"[^>]*', html):
    print("Found:", m.group(0)[:120])

# Simulate redirect with Python None in urlencode
next_url = None
print("urlencode with None:", urlencode({"next": next_url}))
