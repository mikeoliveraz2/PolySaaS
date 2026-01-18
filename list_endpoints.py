from dose.models import PassThroughEndpoint

# List all endpoints to see current config
for ep in PassThroughEndpoint.objects.all():
    print(f'ID: {ep.id}, Trigger: {ep.trigger_path}, URL: {ep.endpoint_url}, Enabled: {ep.is_enabled}, Bypass: {ep.bypass_middleware}')