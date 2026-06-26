"""Diagnose login + redirect to /admin/polysniffer/capture/2/."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "mysite.settings")
django.setup()

from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from django.db import connection
from django.test import Client
from dose.models import PassThroughEndpoint, Tenant

NEXT = "/admin/polysniffer/capture/2/"

print("=== Users ===")
for uname in ("polysaasppd", "polysaasppd2", "polysaasppv"):
    u = User.objects.filter(username=uname).first()
    if not u:
        print(f"{uname}: NOT FOUND")
        continue
    ok = authenticate(username=uname, password="PolySaaS2026!")
    print(f"{uname}: exists staff={u.is_staff} active={u.is_active} auth={bool(ok)}")

print("\n=== Endpoint id=2 per tenant schema ===")
for slug in ("polysaasppd2", "polysaasppv"):
    t = Tenant.objects.filter(slug=slug).first()
    if not t:
        continue
    with connection.cursor() as c:
        c.execute(f'SET search_path TO "{t.schema_name}", public;')
    eps = list(
        PassThroughEndpoint.objects.filter(id=2).values(
            "id", "menu_title", "endpoint_url", "is_enabled"
        )
    )
    print(f"{slug}: {eps or 'no id=2'}")

print("\n=== Login POST with next=capture/2 ===")
for uname in ("polysaasppd2", "polysaasppv", "polysaasppd"):
    c = Client()
    r = c.post(
        "/admin/login/",
        {"username": uname, "password": "PolySaaS2026!", "next": NEXT},
        follow=True,
    )
    body = r.content.decode("utf-8", "replace")
    print(f"\n{uname}:")
    print(f"  final status={r.status_code}")
    print(f"  redirect_chain={r.redirect_chain}")
    print(f"  login_page={'DOSE LOGIN PAGE' in body}")
    print(f"  capture_page={'PolySniffer Live Capture' in body}")
    print(f"  endpoint_error={'Error Loading Endpoint' in body}")
    if "errorlist" in body:
        import re

        errs = re.findall(r"<li>([^<]+)</li>", body)
        print(f"  form_errors={errs[:2]}")
