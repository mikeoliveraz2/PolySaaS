import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "mysite.settings")
django.setup()
from django.db import connection
from dose.polysniffer.models import TrafficLog, TrafficCapture

with connection.cursor() as c:
    c.execute('SET search_path TO "polysaast142", public')
cap = TrafficCapture.objects.filter(capture_name="ep4-native-20260625-0717").first()
if not cap:
    with connection.cursor() as c:
        c.execute('SET search_path TO "plysaast10", public')
    cap = TrafficCapture.objects.filter(capture_name="ep4-native-20260625-0717").first()
print("cap", cap.capture_name if cap else None, "schema", connection.schema_name if hasattr(connection,'schema_name') else '?')
if cap:
    for log in TrafficLog.objects.filter(capture_session=cap).order_by("id")[:20]:
        print(log.status_code, log.method, (log.client_path or log.path)[:90])
        print("  url:", (log.url or "")[:100])
