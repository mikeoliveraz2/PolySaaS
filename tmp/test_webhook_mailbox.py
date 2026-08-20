"""
Test the webhook mailbox flow end-to-end:
1. Create a fake /poly webhook event
2. Write to mailbox
3. Consumer processes it
4. Check results
"""
from django.utils import timezone
from datetime import timedelta
from dose.models import Tenant, WebhookMailbox
from dose.webhook_events import build_slack_command_envelope, process_trigger_envelope
from dose.tenant_app_lookup import tenant_schema_search_path

# Get a test tenant (e.g., olient)
tenant = Tenant.objects.get(schema_name='olient')
print(f"Using tenant: {tenant.schema_name}")

# Simulate a /poly command from Slack
fake_slack_payload = {
    'team_id': 'T12345TEST',
    'user_id': 'U12345TEST',
    'command': '/poly',
    'text': 'test mailbox',
    'channel_id': 'C12345TEST',
    'response_url': 'https://hooks.slack.com/test',
    'trigger_id': 'test_trigger_123'
}

# Build canonical envelope
print("\n1. Building envelope...")
envelope = build_slack_command_envelope(tenant, fake_slack_payload)
print(f"   Event ID: {envelope['event_id'][:16]}...")
print(f"   Action path: {envelope['action_path']}")

# Write to mailbox
print("\n2. Writing to mailbox...")
mailbox = WebhookMailbox.create_from_envelope(envelope, ttl_seconds=300)
print(f"   Mailbox ID: {mailbox.id}")
print(f"   Status: {mailbox.status}")
print(f"   Expires: {mailbox.expires_at}")

# Verify mailbox entry exists
count = WebhookMailbox.objects.filter(status='pending').count()
print(f"\n3. Mailbox check: {count} pending entries")

# Process the mailbox entry (simulating consumer)
print("\n4. Processing envelope...")
with tenant_schema_search_path(tenant) as ok:
    if not ok:
        print("   ERROR: Could not set tenant schema")
    else:
        result = process_trigger_envelope(envelope, tenant)
        print(f"   Status: {result.get('status')}")
        print(f"   Matched: {result.get('matched', 0)} instructions")
        if result.get('results'):
            for r in result['results']:
                print(f"   - Instruction {r.get('instruction_id')}: {r.get('status')}")

# Check final mailbox status
mailbox.refresh_from_db()
print(f"\n5. Final mailbox status: {mailbox.status}")
if mailbox.result:
    print(f"   Result: {mailbox.result.get('status')}")

print("\n✓ Mailbox flow test complete!")
