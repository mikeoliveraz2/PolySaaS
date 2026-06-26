import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "mysite.settings")
django.setup()
from django.db import connection
from dose.polysniffer.models import TrafficLog, TrafficCapture

for schema in ["plysaast10", "polysaast142", "polysaasppd2", "public"]:
    with connection.cursor() as c:
        c.execute(f'SET search_path TO "{schema}", public')
    caps = TrafficCapture.objects.filter(capture_name__icontains="ep4-native-20260625").order_by("-id")
    if not caps.exists():
        continue
    print(f"\n=== {schema} ===")
    for cap in caps[:5]:
        n404 = TrafficLog.objects.filter(capture_session=cap, status_code=404).count()
        n200 = TrafficLog.objects.filter(capture_session=cap, status_code=200).count()
        hs = TrafficLog.objects.filter(capture_session=cap, url__icontains="hsappstatic").count()
        print(f"  {cap.capture_name} active={cap.is_active} 200={n200} 404={n404} cdn_logs={hs}")
