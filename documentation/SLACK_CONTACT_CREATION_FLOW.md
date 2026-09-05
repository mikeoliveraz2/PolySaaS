# Slack → Odoo Contact Creation Flow

**Date:** 2026-09-06  
**Status:** Complete  
**Session:** Cursor — Slack message contact creation

## Overview

This feature enables automatic creation of Odoo contacts from Slack messages using a deterministic format. When a user posts a message in Slack matching the pattern `New contact: Name, email, Company`, PolySaaS:

1. Receives the message via Slack Events API webhook
2. Parses the contact information deterministically (no LLM in hot path)
3. Queues the contact creation via the producer/consumer pattern
4. Calls Odoo's XML-RPC API to create or update the contact
5. Shows feedback in the orchestration bar and via Geronimo

This flow prioritizes **reliability** (deterministic parsing, no LLM failures) and **visibility** (green bar always shows activity, errors displayed).

## Architecture

### Flow Diagram

```
Slack message
    ↓
POST /hooks/slack/events/
    ↓
slack_events_webhook.py
    ├── URL verification challenge
    ├── Signature verification
    ├── Parse contact format
    └── publish_slack_contact_event
        ↓
WebhookMailbox (envelope)
        ↓
WebhookMailboxConsumer
        ↓
process_trigger_envelope
        ↓
Instruction (action_path: /events/slack/message/contact)
        ↓
OdooCreatePartner (Atomic Service)
        ├── OdooRpcClient
        ├── Find or create res.partner
        └── Save callback data
            ↓
create_orchestration_feedback
            ↓
Green bar: "✓ Slack → Odoo: created contact 'Jane Doe' (jane@acme.com) — partner #42"
```

### Components

| Component | Purpose |
|-----------|---------|
| `dose/views/slack_events_webhook.py` | Webhook endpoint for Slack Events API |
| `dose/webhook_events.py` | Envelope builder and mailbox publisher |
| `dose/management/commands/seed_slack_contact_orchestration.py` | Instruction seeding |
| `dose/services/odoo_create_partner.py` | Atomic service (reused, frozen) |
| `dose/messaging.py` | Enhanced feedback for Slack contact events |
| `dose/tests/test_slack_contact_creation.py` | 18 tests covering full flow |

## Contact Format

### Valid Format

```
New contact: <Name>, <email>, <Company>
```

- **Case-insensitive:** `new contact`, `NEW CONTACT`, `New Contact` all work
- **Whitespace tolerant:** Extra spaces around fields are trimmed
- **Strict structure:** All three fields required, comma-separated
- **Email validation:** Basic `@` and `.` pattern required

### Examples

**Valid:**
```
New contact: Jane Doe, jane@acme.com, Acme Corp
NEW CONTACT: Bob Smith, bob@test.com, Test Inc
new contact:  Alice Johnson  ,  alice@example.org  ,  Example Org  
```

**Invalid (ignored):**
```
Contact: Jane Doe, jane@acme.com          # Missing "New"
New contact Jane Doe                      # Missing punctuation
New contact: Jane Doe, jane@acme.com      # Missing company
New contact: Jane Doe, not-an-email, Co   # Invalid email
Just a normal Slack message               # Does not match pattern
```

## Setup

### 1. Seed the Instruction

```bash
python manage.py seed_slack_contact_orchestration olient
```

This creates:
- **Instruction:** `slack.message.contact` → `/events/slack/message/contact`
- **Atomic Service:** `OdooCreatePartner`
- **Match:** Exact path match, POST, REQ direction

### 2. Configure Slack App

**In Slack API Console (api.slack.com/apps):**

1. **Event Subscriptions:**
   - Enable Event Subscriptions: **On**
   - Request URL: `https://your-polysaas-domain.com/hooks/slack/events/`
   - Subscribe to bot events:
     - `message.channels` (for channel messages)

2. **URL Verification:**
   - Slack will POST a `url_verification` challenge to your endpoint
   - The webhook automatically responds with the challenge value
   - Save changes after verification succeeds

3. **Signing Secret:**
   - Copy the Signing Secret from **Basic Information**
   - Store in `TenantApp.extra_config` for your Slack app:
     ```json
     {
       "signing_secret": "abc123...",
       "slack_team_id": "T99999..."
     }
     ```

4. **Reinstall App:**
   - After changing event subscriptions, reinstall the app to your workspace
   - The app must have permission to read channel messages

### 3. Test the Flow

**In Slack:**
```
New contact: Test User, test@example.com, Example Corp
```

**Expected:**
1. Green orchestration bar shows: `✓ Slack → Odoo: created contact 'Test User' (test@example.com) — partner #42`
2. Check Odoo Contacts to verify the contact was created
3. If error, green bar shows: `Consumer failed: <error detail>`

## Webhook Endpoint

### URL

```
POST /hooks/slack/events/
```

### Request

**Headers:**
- `X-Slack-Request-Timestamp`: Unix timestamp of request
- `X-Slack-Signature`: `v0=<hmac-sha256-hex>`
- `Content-Type`: `application/json`

**Body:**
```json
{
  "type": "event_callback",
  "team_id": "T99999",
  "event": {
    "type": "message",
    "text": "New contact: Jane Doe, jane@acme.com, Acme Corp",
    "user": "U12345",
    "channel": "C67890",
    "ts": "1234567890.123456"
  }
}
```

### Response

**Success (queued):**
```json
{
  "status": "queued",
  "event_id": "abc123...",
  "mailbox_id": 42
}
```

**Ignored (not contact format):**
```json
{
  "status": "ignored",
  "reason": "message does not match contact format"
}
```

**Error:**
```json
{
  "status": "error",
  "error": "Failed to queue event"
}
```

## Canonical Envelope

The webhook builds a standard `polysaas.trigger.v1` envelope:

```json
{
  "kind": "polysaas.trigger.v1",
  "event_id": "deterministic-hash-from-slack-metadata",
  "correlation_id": "uuid-v4",
  "tenant_schema": "olient",
  "source": "slack",
  "action_path": "/events/slack/message/contact",
  "method": "POST",
  "direction": "REQ",
  "event_key": "slack.message.contact",
  "actor": {
    "external_user_id": "U12345",
    "team_id": "T99999"
  },
  "payload": {
    "name": "Jane Doe",
    "email": "jane@acme.com",
    "company": "Acme Corp",
    "slack_user_id": "U12345",
    "slack_channel_id": "C67890",
    "slack_message_ts": "1234567890.123456"
  },
  "received_at": "2026-09-06T12:34:56.789Z"
}
```

## Security

### Signature Verification

Every request (except `url_verification`) is verified using Slack's signature scheme:

1. Extract `X-Slack-Request-Timestamp` and `X-Slack-Signature` headers
2. Reject requests older than 5 minutes (replay protection)
3. Compute HMAC-SHA256 of `v0:{timestamp}:{body}` using signing secret
4. Compare with provided signature using constant-time comparison

### Deduplication

Event IDs are deterministically hashed from Slack metadata:
- `tenant_schema`
- `slack_team_id`
- `slack_message_ts`
- `slack_channel_id`

The same message delivered twice will produce the same `event_id` and be rejected by the `_claim_event` lock.

## Odoo Integration

### Existing Partner Detection

`OdooCreatePartner` implements find-or-create logic:

1. **Search by email** (exact match)
2. **Search by name** (exact match) if no email match
3. **Update** existing partner if found
4. **Create** new partner if not found

### Odoo Fields Mapped

| Payload Field | Odoo Field | Notes |
|---------------|------------|-------|
| `name` | `name` | Required |
| `email` | `email` | Used for deduplication |
| `company` | `_company_name` | Not directly stored; can be enhanced with Mapping |
| — | `customer_rank` | Set to `1` (filters Contacts bookmark) |

### XML-RPC Transport

The `OdooRpcClient` attempts JSON-RPC first, falls back to XML-RPC. Connection details come from:
1. `TenantApp.extra_config` (`odoo_url`, `odoo_db`, `odoo_login`, `odoo_password`)
2. `PassThroughEndpoint` slug
3. Django settings (`ODOO_SHARED_URL`, `ODOO_XMLRPC_ADMIN_LOGIN`, etc.)

## Orchestration Feedback

### Green Bar Message

Enhanced `feedback_text_for_result` in `dose/messaging.py` detects `event_key == "slack.message.contact"` and builds a narrative message:

**Created:**
```
✓ Slack → Odoo: created contact 'Jane Doe' (jane@acme.com) — partner #42
```

**Updated:**
```
✓ Slack → Odoo: updated contact 'Jane Doe' (jane@acme.com) — partner #42
```

**Error:**
```
Consumer failed: Authentication failed
```

### Geronimo Narration

Geronimo can explain the process if asked:

**User:** "What just happened?"

**Geronimo:** "A Slack message in the format 'New contact: Name, email, Company' triggered automatic contact creation in Odoo. The contact 'Jane Doe' (jane@acme.com) was created as partner #42. This flow uses deterministic parsing (no AI in the hot path) and the existing OdooCreatePartner atomic service via the producer/consumer pattern."

## Tests

18 tests in `dose/tests/test_slack_contact_creation.py`:

### Coverage

- **Parsing:** Valid format, case-insensitive, whitespace handling, invalid formats, truncation
- **Signature:** Valid signature, invalid signature, replay protection, missing v0 prefix
- **Envelope:** Canonical structure, deterministic event_id, different messages produce different IDs
- **Webhook:** URL verification, contact message queued, non-contact ignored, bot messages ignored
- **Feedback:** Slack → Odoo narrative, created vs updated distinction

### Run Tests

```bash
python manage.py test dose.tests.test_slack_contact_creation --keepdb --noinput
```

## Troubleshooting

### "Unknown Slack workspace"

**Cause:** `_find_slack_tenant` could not match the `team_id` from the Slack event.

**Fix:** Verify `TenantApp.extra_config` contains `slack_team_id` matching the Slack workspace.

### "Invalid Slack signature"

**Cause:** Signing secret mismatch or expired timestamp.

**Fix:**
1. Check `TenantApp.extra_config.signing_secret` matches Slack app's signing secret
2. Ensure server clock is accurate (signature verification has 5-minute window)
3. Check that the raw body is used for signature computation (not decoded/modified)

### Contact not created in Odoo

**Cause:** Instruction not seeded, Odoo credentials invalid, or network error.

**Fix:**
1. Run `python manage.py seed_slack_contact_orchestration`
2. Check Odoo connection: `python manage.py shell` → test `OdooRpcClient.from_config(config).authenticate()`
3. Check `CallBackData` rows for error details
4. Check orchestration bar for error message

### Messages ignored even with correct format

**Cause:** Message subtypes (edits, deletes) or bot messages are intentionally ignored.

**Fix:** Post a fresh message (not an edit) from a human user (not a bot).

## Future Enhancements

### Optional LLM Extraction

If deterministic parsing proves too restrictive, add an LLM fallback:

```python
if not contact_data:
    contact_data = _llm_extract_contact(text)  # Fallback
```

Trade-off: More flexible (handles "Create contact for Jane at Acme") but less reliable (LLM can fail, hallucinate, or be slow).

### Custom Field Mapping

Use `Mapping` rows to map `company` to Odoo company hierarchy or custom fields:

```python
{
  "payload.company": "_company_name",
  "payload.phone": "phone",
  "payload.website": "website"
}
```

### Multi-Channel Support

Currently any subscribed channel. Could restrict to a single demo channel by checking `event.channel` matches a configured ID.

### Geronimo Proactive Notification

Instead of passive feedback, Geronimo could proactively announce:

> "New contact created from Slack: Jane Doe (jane@acme.com) is now in Odoo as partner #42. [View Contact]"

## Related Documentation

- `POLYSAAS_ORCHESTRATION_MODEL.md` — Producer/consumer pattern
- `SLACK_WEBHOOK_ORCHESTRATION_DESIGN.md` — Slash command flow (different trigger)
- `GERONIMO_CHAT_INTEGRATION.md` — Chat dock and page context
- `dose/services/odoo_create_partner.py` — Atomic service (frozen, BINGO)
- `dose/webhook_events.py` — Envelope builders and mailbox publishing

## Commit

Files changed:
- `dose/views/slack_events_webhook.py` (new)
- `dose/webhook_events.py` (+ `.bak`)
- `mysite/urls.py` (+ `.bak`)
- `dose/management/commands/seed_slack_contact_orchestration.py` (new)
- `dose/messaging.py` (+ `.bak`)
- `dose/tests/test_slack_contact_creation.py` (new)
- `documentation/SLACK_CONTACT_CREATION_FLOW.md` (new, this file)

Tests: **18 passed**  
Django check: **No issues**

---

**Implementation complete. Green bar shows activity. Errors displayed. Go go go. ✓**
