from dose.models import Tenant, TenantApp
from django.db import connection

# Get tenant and set search_path
tenant = Tenant.objects.get(slug='polysaasonline')
with connection.cursor() as cur:
    cur.execute(f'SET search_path TO {tenant.schema_name}, public')

# Find the Slack app
slack_app = TenantApp.objects.filter(app_name='slack').first()

if slack_app:
    print(f"Found Slack app: {slack_app.id}")
    print(f"Current extra_config: {slack_app.extra_config}")
    
    # Ask for signing secret
    print("\nPaste the signing secret and press Enter:")
    signing_secret = input().strip()
    
    # Update extra_config
    if not slack_app.extra_config:
        slack_app.extra_config = {}
    
    slack_app.extra_config['signing_secret'] = signing_secret
    slack_app.save()
    
    print(f"\n✓ Updated! New extra_config: {slack_app.extra_config}")
else:
    print("ERROR: No Slack app found")
