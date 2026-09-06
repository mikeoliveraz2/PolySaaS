# Mattermost → Odoo Adapter Build Spec

**Goal:** Mirror the Slack → Odoo contact/sale creation flow using Mattermost as the input source, reusing 100% of downstream orchestration, RabbitMQ queues, and Odoo consumers.

**Core Principle:** Mattermost adapter normalizes Mattermost webhooks into the **exact same canonical event schema** that Slack produces, then publishes to the **same RabbitMQ exchange** with the **same routing keys**.

---

## Architecture Overview

```
Mattermost Message
    ↓
Mattermost Webhook POST → /hooks/mattermost/events/
    ↓
[NEW] Mattermost Adapter Layer:
    - Token auth verification
    - Payload normalization
    - Routing key assignment
    ↓
Publish to RabbitMQ (SAME exchange as Slack)
    ↓
[UNCHANGED] Mailbox consumer
    ↓
[UNCHANGED] Orchestration hook
    ↓
[UNCHANGED] OdooCreatePartner / OdooCreateSale
    ↓
[UNCHANGED] Feedback generation
    ↓
[NEW] Post feedback to Mattermost channel
```

**Key:** Everything in brackets `[UNCHANGED]` requires ZERO code changes.

---

## 1. Webhook Endpoint

### New URL Route
```python
# mysite/urls.py
path('hooks/mattermost/events/', mattermost_events_webhook, name='mattermost_events_webhook')
```

### Mattermost Payload Format

#### Outgoing Webhook POST (preferred for messages)
```json
{
  "channel_id": "abc123def456",
  "channel_name": "town-square",
  "team_domain": "polysaas",
  "team_id": "xyz789ghi012",
  "post_id": "post123",
  "text": "New contact: Jane Doe, jane@acme.com, Acme Corp",
  "timestamp": 1725678900,
  "token": "webhook_secret_token_here",
  "trigger_word": "New contact:",
  "user_id": "user123abc",
  "user_name": "michael.oliver",
  "file_ids": ""
}
```

#### Slash Command POST (alternative trigger)
```json
{
  "channel_id": "abc123def456",
  "channel_name": "town-square",
  "command": "/createcontact",
  "response_url": "https://mm.example.com/hooks/commands/abc123",
  "team_domain": "polysaas",
  "team_id": "xyz789ghi012",
  "text": "Jane Doe, jane@acme.com, Acme Corp",
  "token": "slash_command_token_here",
  "trigger_id": "trigger123",
  "user_id": "user123abc",
  "user_name": "michael.oliver"
}
```

**Decision:** Start with **Outgoing Webhook** (simpler, message-driven). Slash Command can be added later.

---

## 2. Authentication Verification

### Mattermost Token-Based Auth
Unlike Slack's HMAC signature, Mattermost uses **simple shared token** comparison.

```python
def _verify_mattermost_token(request_token: str, expected_token: str) -> bool:
    """
    Verify Mattermost webhook token.
    
    Much simpler than Slack's HMAC - just compare tokens.
    Token is sent in POST body as 'token' field.
    """
    if not request_token or not expected_token:
        return False
    return hmac.compare_digest(request_token, expected_token)
```

### Token Storage
```python
# TenantApp.extra_config (Mattermost)
{
  "mm_team_id": "xyz789ghi012",
  "mm_webhook_token": "webhook_secret_token_here",
  "mm_server_url": "https://mm.polysaas.online",
  "mm_bot_token": "bearer_token_for_posting"
}
```

### Tenant Lookup
```python
def _find_mattermost_tenant(team_id: str):
    """Find tenant by Mattermost team_id."""
    for tenant in Tenant.objects.exclude(schema_name__iexact='public').filter(is_active=True):
        with tenant_schema_search_path(tenant) as ok:
            if not ok:
                continue
        try:
            app = TenantApp.objects.filter(
                app_name='mattermost',
                extra_config__mm_team_id=team_id,
                status__in=('active', 'provisioning'),
            ).first()
        except Exception:
            app = None
        if app:
            return tenant, app
    return None, None
```

---

## 3. Payload Normalization (The Key Piece)

### Canonical Event Schema (Target)
This is what BOTH Slack and Mattermost adapters must produce:

```python
{
    "event_type": "contact.new",  # or "sale.new"
    "source": "mattermost",  # vs "slack"
    "tenant_slug": "polysaasonline",
    "channel_id": "abc123def456",
    "channel_name": "town-square",
    "user_id": "user123abc",
    "user_name": "michael.oliver",
    "timestamp": 1725678900,
    "text": "New contact: Jane Doe, jane@acme.com, Acme Corp",
    "parsed_data": {
        "name": "Jane Doe",
        "email": "jane@acme.com",
        "company": "Acme Corp"
    },
    "metadata": {
        "post_id": "post123",
        "team_id": "xyz789ghi012",
        "trigger_word": "New contact:"
    }
}
```

### Field Mapping Table

| Mattermost Field | Canonical Field | Notes |
|---|---|---|
| `team_id` | `metadata.team_id` | Used for tenant lookup |
| `channel_id` | `channel_id` | Direct mapping |
| `channel_name` | `channel_name` | Direct mapping |
| `user_id` | `user_id` | Mattermost user ID |
| `user_name` | `user_name` | Mattermost username |
| `text` | `text` | Raw message text |
| `timestamp` | `timestamp` | Unix timestamp |
| `post_id` | `metadata.post_id` | For tracking/feedback |
| `trigger_word` | `metadata.trigger_word` | What triggered webhook |
| (computed) | `event_type` | Derived from routing logic |
| (computed) | `source` | Always `"mattermost"` |
| (computed) | `parsed_data` | Extracted via same regex as Slack |

### Normalizer Function
```python
def normalize_mattermost_webhook(payload: dict, tenant) -> dict:
    """
    Transform Mattermost webhook payload into canonical event schema.
    
    Returns same shape as Slack normalizer for downstream compatibility.
    """
    text = payload.get('text', '').strip()
    
    # Use SAME parsers as Slack
    contact_data = _parse_contact_message(text)  # Reuse from Slack
    sale_data = _parse_sale_message(text) if not contact_data else None
    
    # Determine event type (SAME routing logic as Slack)
    if contact_data:
        event_type = "contact.new"
        parsed_data = contact_data
    elif sale_data:
        event_type = "sale.new"
        parsed_data = sale_data
    else:
        return None  # Unrecognized format
    
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
```

---

## 4. Routing Key Assignment

### Routing Key Mapping (SAME as Slack)

| Event Type | RabbitMQ Routing Key | Downstream Consumer |
|---|---|---|
| `contact.new` | `contact.new` | OdooCreatePartner |
| `sale.new` | `sale.new` | OdooCreateSale |

**Critical:** Use **identical** routing keys as Slack so messages hit the **same queues**.

### Routing Logic
```python
def get_routing_key(canonical_event: dict) -> str:
    """
    Assign RabbitMQ routing key based on event type.
    
    SAME logic for both Slack and Mattermost.
    """
    return canonical_event['event_type']  # "contact.new" or "sale.new"
```

---

## 5. RabbitMQ Publishing (Unchanged)

### Publish to SAME Exchange
```python
def publish_mattermost_event(tenant, canonical_event: dict) -> dict:
    """
    Publish Mattermost event to RabbitMQ using SAME infrastructure as Slack.
    
    Exchange: polysaas.events (SAME)
    Routing Key: contact.new / sale.new (SAME)
    Consumer: mailbox_consumer (SAME)
    """
    routing_key = get_routing_key(canonical_event)
    
    envelope = {
        "event_key": canonical_event['event_type'],  # "contact.new"
        "action_path": f"/events/mattermost/{canonical_event['event_type']}",
        "source": "mattermost",
        "tenant_slug": tenant.slug,
        "payload": canonical_event,
        "timestamp": canonical_event['timestamp'],
    }
    
    # Use EXISTING RabbitMQ publisher (same as Slack uses)
    from dose.webhook_events import publish_to_rabbitmq
    return publish_to_rabbitmq(
        exchange='polysaas.events',
        routing_key=routing_key,
        message=envelope,
        tenant=tenant
    )
```

**Key Point:** The `publish_to_rabbitmq()` function is **unchanged**. It's the same one Slack uses.

---

## 6. Feedback Mechanism

### Mattermost REST API for Posting

#### API Endpoint
```
POST https://mm.polysaas.online/api/v4/posts
Authorization: Bearer <mm_bot_token>
Content-Type: application/json
```

#### Feedback Payload
```json
{
  "channel_id": "abc123def456",
  "message": "✅ Created contact 'Jane Doe' (jane@acme.com) → Odoo partner #42",
  "root_id": "post123"  // Reply to original post (optional)
}
```

#### Feedback Function
```python
def post_mattermost_feedback(tenant, mm_app: TenantApp, canonical_event: dict, result: dict):
    """
    Post feedback to Mattermost channel after Odoo operation completes.
    
    Equivalent to Slack's chat.postMessage.
    """
    import requests
    
    server_url = mm_app.extra_config.get('mm_server_url', '')
    bot_token = mm_app.extra_config.get('mm_bot_token', '')
    channel_id = canonical_event['channel_id']
    post_id = canonical_event['metadata']['post_id']
    
    # Reuse SAME feedback text generator as Slack
    from dose.messaging import feedback_text_for_result
    message = feedback_text_for_result(
        event_key=canonical_event['event_type'],
        result=result,
        source='mattermost'
    )
    
    payload = {
        "channel_id": channel_id,
        "message": message,
        "root_id": post_id  # Reply thread
    }
    
    response = requests.post(
        f"{server_url}/api/v4/posts",
        headers={
            "Authorization": f"Bearer {bot_token}",
            "Content-Type": "application/json"
        },
        json=payload,
        timeout=10
    )
    
    return response.status_code == 201
```

---

## 7. Identity Mapping (User → Odoo Partner)

### Current Slack Approach
Slack already resolves users by email or has a mapping table. We need the same for Mattermost.

### Option A: Email-Based Resolution (Simplest)
If Odoo partner lookup is by email, and Mattermost users have emails:

```python
def resolve_mattermost_user_to_odoo_partner(mm_user_id: str, mm_app: TenantApp):
    """
    Resolve Mattermost user to Odoo partner by email.
    
    Requires Mattermost API call to get user email.
    """
    server_url = mm_app.extra_config['mm_server_url']
    bot_token = mm_app.extra_config['mm_bot_token']
    
    response = requests.get(
        f"{server_url}/api/v4/users/{mm_user_id}",
        headers={"Authorization": f"Bearer {bot_token}"},
        timeout=5
    )
    
    if response.status_code == 200:
        user_data = response.json()
        email = user_data.get('email', '')
        # Look up Odoo partner by email
        return find_odoo_partner_by_email(email)
    
    return None
```

### Option B: Explicit Mapping Table
```python
# New model: MattermostUserMapping
class MattermostUserMapping(models.Model):
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE)
    mm_user_id = models.CharField(max_length=255)
    mm_username = models.CharField(max_length=255, blank=True)
    odoo_partner_id = models.IntegerField()
    
    class Meta:
        unique_together = ('tenant', 'mm_user_id')
```

**Recommendation:** Start with **Option A (email-based)** if Slack already uses it. Add Option B only if email resolution proves insufficient.

---

## 8. Configuration & Secrets

### TenantApp.extra_config Schema
```json
{
  "mm_team_id": "xyz789ghi012",
  "mm_webhook_token": "abc123secrettoken",
  "mm_server_url": "https://mm.polysaas.online",
  "mm_bot_token": "bearer_xyz_long_token_here"
}
```

### Mattermost Bot Setup Requirements
1. **Create Bot Account:** In Mattermost System Console
2. **Generate Personal Access Token:** User Settings → Security → Personal Access Tokens
3. **Grant Permissions:**
   - `read_channel` (to read channel info)
   - `post:channel` (to post feedback messages)
4. **Add Bot to Target Channels:** `/invite @polysaas-bot`

### Outgoing Webhook Configuration
1. **Mattermost Integrations → Outgoing Webhooks**
2. **Trigger Words:** `New contact:`, `New sale:`
3. **Callback URL:** `https://<ngrok or production>/hooks/mattermost/events/`
4. **Channel:** Select target channel (e.g., `town-square`)
5. **Token:** Copy generated token → store in `TenantApp.extra_config`

---

## 9. Implementation Files

### New Files to Create

```
dose/
├── views/
│   └── mattermost_events_webhook.py          # NEW - Webhook receiver
├── mattermost/
│   ├── __init__.py                           # NEW
│   ├── normalizer.py                         # NEW - Payload normalization
│   ├── auth.py                               # NEW - Token verification
│   ├── feedback.py                           # NEW - Post to Mattermost
│   └── parsers.py                            # SYMLINK/REUSE - Contact/sale parsers
├── tests/
│   └── test_mattermost_contact_creation.py   # NEW - Test suite
└── management/commands/
    └── seed_mattermost_orchestration.py      # NEW - Seed Instructions
```

### Modified Files

```
mysite/
└── urls.py                                   # ADD webhook route

dose/
├── webhook_events.py                         # ADD Mattermost envelope builders (minimal)
└── messaging.py                              # EXTEND feedback_text_for_result (if needed)
```

### Reused Files (No Changes)

```
dose/
├── atomic_services/odoo_create_partner.py    # UNCHANGED
├── atomic_services/odoo_create_sale.py       # UNCHANGED
├── orchestration_hook.py                     # UNCHANGED
├── mailbox_consumer.py                       # UNCHANGED
└── rabbitmq/                                 # UNCHANGED
```

---

## 10. Message Format Examples

### Contact Creation
**User Types in Mattermost:**
```
New contact: Jane Doe, jane@acme.com, Acme Corp
```

**Webhook Receives:**
```json
{
  "text": "New contact: Jane Doe, jane@acme.com, Acme Corp",
  "trigger_word": "New contact:",
  ...
}
```

**Normalizer Produces:**
```json
{
  "event_type": "contact.new",
  "source": "mattermost",
  "parsed_data": {
    "name": "Jane Doe",
    "email": "jane@acme.com",
    "company": "Acme Corp"
  }
}
```

**Published to RabbitMQ with Routing Key:** `contact.new`

**Consumer Processes:** OdooCreatePartner (same as Slack)

**Feedback Posted to Mattermost:**
```
✅ Mattermost → Odoo: created contact 'Jane Doe' (jane@acme.com) — partner #42
```

### Sale Creation (Future)
**User Types:**
```
New sale: Acme Corp - $50,000 - Enterprise License
```

**Routing Key:** `sale.new`

**Consumer:** OdooCreateSale (same as Slack would use)

---

## 11. Testing Strategy

### Unit Tests
```python
# test_mattermost_normalizer.py
def test_normalize_contact_message():
    payload = {
        'text': 'New contact: John Smith, john@example.com, Example Inc',
        'channel_id': 'ch123',
        'user_id': 'u456',
        'timestamp': 1234567890,
        'team_id': 't789',
        'trigger_word': 'New contact:'
    }
    
    result = normalize_mattermost_webhook(payload, mock_tenant)
    
    assert result['event_type'] == 'contact.new'
    assert result['source'] == 'mattermost'
    assert result['parsed_data']['name'] == 'John Smith'
    assert result['parsed_data']['email'] == 'john@example.com'
```

### Integration Tests
```python
def test_mattermost_to_odoo_contact_flow(db, tenant, mattermost_app):
    """End-to-end: Mattermost webhook → Odoo contact creation."""
    
    # 1. POST to webhook endpoint
    response = client.post('/hooks/mattermost/events/', json={
        'text': 'New contact: Test User, test@example.com, Test Co',
        'token': 'correct_webhook_token',
        'team_id': mattermost_app.extra_config['mm_team_id'],
        'channel_id': 'ch123',
        'user_id': 'u456',
    })
    
    assert response.status_code == 200
    
    # 2. Verify event published to RabbitMQ
    published_events = get_rabbitmq_messages('contact.new')
    assert len(published_events) == 1
    assert published_events[0]['source'] == 'mattermost'
    
    # 3. Verify Odoo contact created
    partner = odoo_api.search_partner(email='test@example.com')
    assert partner['name'] == 'Test User'
    assert partner['comment'] == 'Test Co'
```

---

## 12. Deployment Checklist

### Prerequisites
- [x] Mattermost server accessible
- [x] Bot account created with token
- [x] Outgoing webhook configured in Mattermost
- [x] Webhook token stored in TenantApp.extra_config
- [x] Bot added to target channel(s)

### Implementation Steps
1. Create `dose/mattermost/` module
2. Implement normalizer using SAME parsers as Slack
3. Implement token auth verification
4. Create webhook endpoint
5. Wire up RabbitMQ publishing (reuse existing)
6. Implement Mattermost feedback poster
7. Add tests (unit + integration)
8. Seed orchestration Instruction for `contact.new`
9. Test end-to-end with real Mattermost message
10. Update documentation

### Validation
- [ ] Message in Mattermost triggers webhook
- [ ] Token auth passes
- [ ] Payload normalized correctly
- [ ] Event published to RabbitMQ with `contact.new` routing key
- [ ] Odoo contact created (same consumer as Slack)
- [ ] Feedback posted back to Mattermost channel
- [ ] Works with multiple tenants

---

## 13. Differences from Slack (Summary)

| Aspect | Slack | Mattermost | Shared? |
|---|---|---|---|
| **Webhook Auth** | HMAC-SHA256 signature | Simple token comparison | Different |
| **Payload Format** | Events API JSON | Outgoing Webhook JSON | Different |
| **Normalization** | Slack-specific fields | Mattermost-specific fields | Different |
| **Canonical Schema** | Standard event shape | **SAME** standard event shape | **SAME** |
| **Parsing Logic** | `_parse_contact_message()` | **SAME** function | **SAME** |
| **Routing Keys** | `contact.new`, `sale.new` | **SAME** keys | **SAME** |
| **RabbitMQ Exchange** | `polysaas.events` | **SAME** exchange | **SAME** |
| **Mailbox Consumer** | Polls and processes | **SAME** consumer | **SAME** |
| **Orchestration** | Fires Instructions | **SAME** hook | **SAME** |
| **Odoo Consumer** | OdooCreatePartner | **SAME** atomic service | **SAME** |
| **Feedback Text** | `feedback_text_for_result()` | **SAME** function | **SAME** |
| **Feedback Delivery** | Slack API | Mattermost API | Different |

**Key Insight:** Only the **adapter layer** (webhook → normalize → feedback) differs. Everything else is **100% shared**.

---

## 14. Estimated Effort

### Breakdown
- **Webhook endpoint + auth:** 2-3 hours
- **Normalizer (reusing parsers):** 1-2 hours
- **RabbitMQ publishing (reuse):** 30 minutes
- **Feedback poster:** 1-2 hours
- **Tests:** 2-3 hours
- **Integration + debugging:** 2-3 hours
- **Documentation:** 1 hour

**Total:** ~10-14 hours for complete Mattermost adapter

### Sequence
1. **Phase 1:** Webhook + normalizer + RabbitMQ (get events flowing)
2. **Phase 2:** Verify downstream works (should be instant since unchanged)
3. **Phase 3:** Add feedback poster
4. **Phase 4:** Polish + tests + docs

---

## 15. Future Extensions

### Additional Event Types
Once `contact.new` works, adding `sale.new` is trivial:
1. Add new trigger word: `New sale:`
2. Add new parser (or reuse if format is same)
3. **That's it** - routing, queues, consumers already support it

### Other Mattermost Triggers
- **Slash Commands:** `/createcontact Jane Doe, jane@acme.com, Acme Corp`
- **Interactive Dialogs:** Modal form in Mattermost UI
- **Bot DMs:** Private message to bot

All use **same normalizer** → **same downstream flow**.

---

## Conclusion

The Mattermost adapter is **purely additive** - a thin translation layer that reuses all existing infrastructure. The design is clean because:

1. **Same canonical event schema** for both sources
2. **Same routing keys** → same queues
3. **Same consumers** → no Odoo changes
4. **Same feedback text** → consistent UX

Only the **edges** (webhook reception + feedback delivery) need Mattermost-specific code.

**Next Step:** Build the normalizer first, get events flowing to RabbitMQ, then verify Odoo side "just works".
