"""
Mattermost webhook payload normalizer.

Transforms Mattermost Outgoing Webhook payloads into the canonical event schema
that downstream consumers (RabbitMQ, orchestration, Odoo) expect.

This normalizer produces the SAME schema as the Slack normalizer, ensuring
both sources can feed the same queues and consumers.
"""
import re
import time
from typing import Optional


# Reuse SAME contact parser as Slack
CONTACT_PATTERN = re.compile(
    r'^New contact:\s*([^,]+),\s*([^,]+@[^,]+\.[^,]+),\s*(.+)$',
    re.IGNORECASE
)

# Future: Sale parser (same pattern as Slack will use)
SALE_PATTERN = re.compile(
    r'^New sale:\s*([^-]+)\s*-\s*\$?([\d,]+(?:\.\d{2})?)\s*-\s*(.+)$',
    re.IGNORECASE
)


def parse_contact_message(text: str) -> Optional[dict]:
    """
    Parse contact format: 'New contact: Name, email, Company'
    
    Returns dict with name, email, company or None if format doesn't match.
    
    IDENTICAL to Slack's parser - ensures same validation logic.
    """
    match = CONTACT_PATTERN.match(text.strip())
    if not match:
        return None
    
    name = match.group(1).strip()
    email = match.group(2).strip()
    company = match.group(3).strip()
    
    if not name or not email or not company:
        return None
    
    return {
        'name': name[:100],      # Odoo res.partner.name limit
        'email': email[:100],
        'company': company[:100],
    }


def parse_sale_message(text: str) -> Optional[dict]:
    """
    Parse sale format: 'New sale: Company - $50000 - Description'
    
    Returns dict with company, amount, description or None if format doesn't match.
    
    Future enhancement - same pattern as Slack will use.
    """
    match = SALE_PATTERN.match(text.strip())
    if not match:
        return None
    
    company = match.group(1).strip()
    amount_str = match.group(2).strip().replace(',', '')
    description = match.group(3).strip()
    
    try:
        amount = float(amount_str)
    except ValueError:
        return None
    
    if not company or amount <= 0 or not description:
        return None
    
    return {
        'company': company[:100],
        'amount': amount,
        'description': description[:500],
    }


def normalize_mattermost_webhook(payload: dict, tenant) -> Optional[dict]:
    """
    Transform Mattermost webhook payload into canonical event schema.
    
    Args:
        payload: Raw Mattermost Outgoing Webhook JSON
        tenant: Tenant model instance
    
    Returns:
        Canonical event dict or None if unrecognized format
    
    Canonical Schema (SAME as Slack produces):
    {
        "event_type": "contact.new" | "sale.new",
        "source": "mattermost",
        "tenant_slug": "tenant-slug",
        "channel_id": "mm-channel-id",
        "channel_name": "town-square",
        "user_id": "mm-user-id",
        "user_name": "username",
        "timestamp": 1725678900,
        "text": "Original message text",
        "parsed_data": {
            "name": "Jane Doe",
            "email": "jane@acme.com",
            "company": "Acme Corp"
        },
        "metadata": {
            "post_id": "mm-post-id",
            "team_id": "mm-team-id",
            "trigger_word": "New contact:"
        }
    }
    """
    text = payload.get('text', '').strip()
    
    # Try contact parser first
    contact_data = parse_contact_message(text)
    if contact_data:
        event_type = "contact.new"
        parsed_data = contact_data
    else:
        # Try sale parser
        sale_data = parse_sale_message(text)
        if sale_data:
            event_type = "sale.new"
            parsed_data = sale_data
        else:
            # Unrecognized format
            return None
    
    # Build canonical event (SAME schema as Slack)
    return {
        "event_type": event_type,
        "source": "mattermost",
        "tenant_slug": tenant.slug,
        "channel_id": payload.get('channel_id', ''),
        "channel_name": payload.get('channel_name', ''),
        "user_id": payload.get('user_id', ''),
        "user_name": payload.get('user_name', ''),
        "timestamp": payload.get('timestamp', int(time.time())),
        "text": text,
        "parsed_data": parsed_data,
        "metadata": {
            "post_id": payload.get('post_id', ''),
            "team_id": payload.get('team_id', ''),
            "trigger_word": payload.get('trigger_word', ''),
        }
    }


def get_routing_key(canonical_event: dict) -> str:
    """
    Get RabbitMQ routing key from canonical event.
    
    SAME routing keys as Slack uses:
    - "contact.new" → OdooCreatePartner consumer
    - "sale.new" → OdooCreateSale consumer
    
    Returns:
        Routing key string (e.g., "contact.new")
    """
    return canonical_event['event_type']
