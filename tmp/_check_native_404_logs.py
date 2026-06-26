import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "mysite.settings")
django.setup()

from django.db import connection
from dose.polysniffer.models import TrafficLog, TrafficCapture

schema = "plysaast10"
with connection.cursor() as c:
    c.execute(f'SET search_path TO "{schema}", public')

caps = TrafficCapture.objects.filter(capture_name__icontains="ep4-native").order_by("-id")[:3]
for cap in caps:
    print("session", cap.id, cap.capture_name, cap.is_active)
    logs = TrafficLog.objects.filter(capture_session=cap, status_code=404).order_by("id")[:15]
    for log in logs:
        print(f"  404 path={log.path!r} url={log.url[:120]!r} client={log.client_path[:80]!r}")
