from django.db import connection
with connection.cursor() as cur:
    cur.execute('SET search_path TO olient,public')
from dose.models import PassThroughEndpoint
eps = PassThroughEndpoint.objects.filter(trigger_path__icontains='nextcloud')
for e in eps:
    print(f"id={e.id} trigger={e.trigger_path} url={e.endpoint_url} enabled={e.is_enabled}")
if not eps.exists():
    print("NO nextcloud endpoint found")
    # show all endpoints
    all_eps = PassThroughEndpoint.objects.all()
    for e in all_eps:
        print(f"  id={e.id} trigger={e.trigger_path} url={e.endpoint_url}")
