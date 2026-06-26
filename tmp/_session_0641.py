import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "mysite.settings")
django.setup()
from django.db import connection
from dose.polysniffer.models import TrafficLog, TrafficCapture

with connection.cursor() as c:
    c.execute('SET search_path TO "polysaast142", public')
cap = TrafficCapture.objects.filter(capture_name="ep4-native-20260625-0641").first()
if cap:
    for log in TrafficLog.objects.filter(capture_session=cap):
        print(log.status_code, log.url, log.client_path)
