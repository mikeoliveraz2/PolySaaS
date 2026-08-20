"""
Script to manually create webhook_mailbox table.
Run with: python manage.py shell < tmp/create_mailbox_table.py
"""
from django.db import connection
from django.apps import apps
from dose.models import WebhookMailbox

# Get the model's schema
with connection.schema_editor() as schema_editor:
    # This will create the table in the current schema
    schema_editor.create_model(WebhookMailbox)
    print(f"Created webhook_mailbox table in current schema")
