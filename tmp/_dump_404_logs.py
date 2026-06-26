import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "mysite.settings")
django.setup()
from django.db import connection
from dose.polysniffer.models import TrafficLog

with connection.cursor() as c:
    c.execute('SET search_path TO "polysaast142", public')
for log in TrafficLog.objects.filter(capture_source="native", status_code=404).order_by("-id")[:8]:
    print("---")
    print("url:", log.url)
    print("path:", log.path)
    print("client_path:", log.client_path)
