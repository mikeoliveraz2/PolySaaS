import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "dose.settings")
django.setup()

import json
from django.contrib.auth import get_user_model
from django.db import connection
from django.test import Client

from dose.models import Tenant
from dose.polysniffer.models import TrafficCapture, TrafficLog

User = get_user_model()
u = User.objects.filter(is_staff=True).first()
print("staff user:", u.username if u else None)

c = Client()
r = c.post(
    "/admin/login/",
    {"username": "polysaasppd2", "password": "PolySaaS2026!", "next": "/dose/sniff/2/"},
    follow=True,
)
print("login:", r.status_code, r.redirect_chain[-1] if r.redirect_chain else "ok")

t = Tenant.objects.filter(slug="polysaasppd2").first()

r = c.post("/dose/sniff/2/session/start/", {"mode": "native"})
print("start:", r.status_code, r.content[:200])
cap_id = c.session.get("polysniffer_ep2_capture_id")
print("cap_id in session:", cap_id)

r2 = c.get("/dose/sniff/2/native/")
print("native GET:", r2.status_code, len(r2.content))

with connection.cursor() as cur:
    cur.execute(f'SET search_path TO "{t.schema_name}", public;')

cap = TrafficCapture.objects.filter(pk=cap_id).first()
print("cap active:", cap.is_active if cap else None, cap.capture_name if cap else None)
logs = TrafficLog.objects.filter(capture_session_id=cap_id).count() if cap_id else 0
print("logs for session:", logs)

r3 = c.get("/dose/sniff/2/workspace/poll/?mode=native&since_id=0")
print("poll:", json.loads(r3.content))
