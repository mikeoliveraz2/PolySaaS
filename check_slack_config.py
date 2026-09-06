from dose.models import Tenant, TenantApp
from django.db import connection

tenant = Tenant.objects.get(slug='polysaasonline')
with connection.cursor() as cur:
    cur.execute(f'SET search_path TO {tenant.schema_name}, public')

slack_apps = TenantApp.objects.filter(app_name='slack')
print(f'Found {slack_apps.count()} Slack app(s) for tenant {tenant.name}')
for app in slack_apps:
    print(f'\nApp ID: {app.id}')
    print(f'Status: {app.status}')
    print(f'extra_config keys: {list(app.extra_config.keys()) if app.extra_config else "None"}')
    if app.extra_config:
        team_id = app.extra_config.get('slack_team_id', 'NOT SET')
        signing = 'SET' if app.extra_config.get('signing_secret') else 'NOT SET'
        print(f'  slack_team_id: {team_id}')
        print(f'  signing_secret: {signing}')
