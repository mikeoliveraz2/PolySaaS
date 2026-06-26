import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "mysite.settings")
django.setup()

from django.db import connection

with connection.cursor() as c:
    c.execute(
        """
        SELECT table_schema FROM information_schema.tables
        WHERE table_name = 'polysniffer_trafficlog'
        ORDER BY 1
        """
    )
    schemas = [r[0] for r in c.fetchall()]

from dose.polysniffer.models import TrafficLog

for schema in schemas:
    try:
        with connection.cursor() as c:
            c.execute(f'SET search_path TO "{schema}", public')
        n = TrafficLog.objects.filter(capture_source="native", status_code=404).count()
        if n:
            print(schema, "native 404 count", n)
            for log in TrafficLog.objects.filter(capture_source="native", status_code=404).order_by("-id")[:5]:
                print(" ", log.url[:140])
    except Exception as exc:
        pass
