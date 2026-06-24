"""Test native sniff proxy login + config/client."""
import os
import sys

import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "mysite.settings")
sys.path.insert(0, "D:/PolySaaS")
django.setup()

import json
from django.contrib.auth import get_user_model
from django.test import Client

User = get_user_model()
c = Client()
u = User.objects.filter(username="polysaasppd2").first()
if not u:
    u = User.objects.filter(is_staff=True).first()
c.force_login(u)

c.post("/dose/sniff/2/session/start/", {"mode": "native"})

paths = [
    "/dose/sniff/2/native/login/",
    "/dose/sniff/2/native/api/v4/config/client",
    "/dose/sniff/2/native/api/v4/config/client?format=old",
]
for path in paths:
    r = c.get(path)
    ct = r.get("Content-Type", "")
    print("---", path, r.status_code, ct[:40])
    if "json" in ct:
        try:
            d = r.json()
            if "EnableSignInWithEmail" in d:
                print("  EnableSignInWithEmail", d.get("EnableSignInWithEmail"))
                print("  SiteURL", d.get("SiteURL"))
            elif d.get("id"):
                print("  error", d.get("id"), d.get("message", "")[:80])
        except Exception as e:
            print("  json err", e)
    elif "html" in ct:
        body = r.content.decode("utf-8", errors="replace")
        print("  shim", "polysniffer-mm-native" in body)
        print("  no-sign-in", "sign-in methods" in body.lower())
        print("  loginid", "loginid" in body.lower() or "login_id" in body.lower())
