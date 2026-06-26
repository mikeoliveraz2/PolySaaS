import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "mysite.settings")
django.setup()
from django.db import connection
from dose.polysniffer.models import TrafficLog, TrafficCapture

for schema in ("plysaast10", "polysaast142", "polysaasppd2"):
    try:
        with connection.cursor() as c:
            c.execute(f'SET search_path TO "{schema}", public')
        cap = TrafficCapture.objects.filter(capture_name__icontains="ep4-native").order_by("-id").first()
        if not cap:
            continue
        print(f"\n{schema} latest session: {cap.capture_name} active={cap.is_active}")
        logs = TrafficLog.objects.filter(capture_session=cap).order_by("-id")[:6]
        for log in logs:
            print(f"  {log.status_code} {log.client_path[:100] if log.client_path else log.path[:100]}")
    except Exception as e:
        print(schema, e)
