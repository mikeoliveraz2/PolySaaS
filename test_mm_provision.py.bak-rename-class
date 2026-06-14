"""Test the MattermostProvisioningService directly for olient tenant."""
import os, sys, django
sys.path.insert(0, os.path.dirname(__file__))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
django.setup()

from django.db import connection
connection.cursor().execute('SET search_path TO olient,public')

from django.contrib.auth import get_user_model
from dose.models import Tenant
from parameters.models import Parameter

User = get_user_model()
tenant = Tenant.objects.get(schema_name='olient')
user = User.objects.get(username='olientAdmin')

params = list(Parameter.objects.filter(matchingKey='MattermostProvisioningService').order_by('sequence'))
print(f"Tenant: {tenant.name}")
print(f"User: {user.username} ({user.email})")
print(f"Parameters: {len(params)} found")

# Build a mock request
class MockRequest:
    pass

request = MockRequest()
request.tenant = tenant
request.user = user
request.atomic_parameters = params
request.path = '/subscribe/'
request.method = 'POST'

# Build a mock instruction
class MockInstruction:
    pass

instruction = MockInstruction()
instruction.eventKey = 'mattermost_provision'
instruction.description = 'Provision Mattermost for tenant'
instruction.save_callbackdata = True

from dose.services.mattermost_provisioning_service import MattermostProvisioningService
import json

result = MattermostProvisioningService.execute_and_save(request, instruction)
print("\nResult:")
print(json.dumps(result, indent=2, default=str))
