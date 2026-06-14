"""One-shot script to create MattermostProvisioningService parameters in olient schema."""
import os, sys, django
sys.path.insert(0, os.path.dirname(__file__))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
django.setup()

from django.db import connection
connection.cursor().execute('SET search_path TO olient,public')

from parameters.models import Parameter

p, created = Parameter.objects.update_or_create(
    matchingKey='MattermostProvisioningService',
    sequence=1,
    defaults={
        'param1': 'http://localhost:8065',
        'param2': 'h4wd46ha8fbc7kdanzsi1w8zye',
        'param3': 'I',
        'description': 'Mattermost provisioning config: param1=URL, param2=admin token, param3=team type',
    }
)
status = "created" if created else "updated"
print(f"Parameter {status}: {p}")
print(f"  URL: {p.param1}")
print(f"  Token: {p.param2[:8]}...")
print(f"  Type: {p.param3}")
