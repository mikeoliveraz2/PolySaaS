"""Exercise the stray-root relay through the real MIDDLEWARE stack."""
import os
import sys

import django

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "mysite.settings")
django.setup()

from django.test import Client  # noqa: E402

PANE = "http://testserver/pt/polysniff/app.slack.com/"
FOREIGN_PANE = "http://localhost:8000/pt/polysniff/app.slack.com/"
QUERY = "app=client&return_to=%2Fpt%2Fpolysniff%2Fapp.slack.com%2F&teams="

client = Client()
resp = client.get(f"/auth?{QUERY}", HTTP_REFERER=PANE, follow=False)
print("claimed  /auth        ->", resp.status_code, resp.headers.get("Location"))

resp = client.get(f"/auth?{QUERY}", follow=False)
print("no referer           ->", resp.status_code, resp.headers.get("Location"))

resp = client.get("/accounts/login/", HTTP_REFERER=PANE, follow=False)
print("unclaimed path       ->", resp.status_code, resp.headers.get("Location"))

resp = client.get(f"/auth?{QUERY}", HTTP_REFERER=FOREIGN_PANE, follow=False)
print("cross-origin referer ->", resp.status_code, resp.headers.get("Location"))
