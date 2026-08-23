# Webhook mailboxes + consumer orchestration

**Status: OWNER APPROVED — active architecture**

**UI and navigation are governed by
`documentation/POLYSAAS_UI_NAVIGATION_AND_EVENTS.md`.**

## Purpose

Unify how events are bound and executed.

- Webhooks are declared up front and act as dumb mailboxes.
- Consumers do updates and messaging asynchronously.
- While surfing, the user attaches orchestration the same way as before, but the bind target is a webhook → consumer, not "run an atomic inside the HTTP request."

## Locked rules

1. Webhooks do not run atomics. They accept, persist, timeout.
2. Tenant for Slack is resolved only from stored team_id mapping.
3. Slack production orchestration is API-first. A Slack handler may provide
   mock/wireframe context or specialized discovery hooks, but production does
   not depend on proxying Slack's full SPA.
4. Native remains a specialized HAR discovery tool for applications where
   capture is supported. It is not the universal endpoint home.
5. No iframes unless owner explicitly authorizes.
6. PolySaaS = port 8000. Nextcloud = 8888. Never mix.
7. Proposal first. One change → validate → stop.

## Model

```
User or external UI action
→ webhook fires (pre-registered)
→ dumb mailbox (store envelope, TTL)
→ consumer dequeues
→ updates + messaging
→ orchestration bar (DoseMessage / equivalent)
```

Webhooks deliver triggers. They are not trigger sources and not executors.

## Product surfaces

### 1) Endpoint home (universal)

- The primary surface is PolySaaS-owned mock/screenshot chrome plus bookmarks.
- A bookmark can open a controlled form, fire a controlled event, show a mock
  surface, or open the unchanged real app in a top-level browser.
- Form/direct actions publish to the same mailbox + consumer pipeline.

### 2) Native / passthrough (specialized)

- Native captures HAR evidence and does not expose orchestration feedback.
- Passthrough validates app handlers and can bind captured action points.
- These tools remain available for self-hosted/capturable apps; they are not
  forced onto vendor SaaS.

### 3) Slack and similar SaaS

- The default PolySaaS surface is mock + bookmarks.
- The complete vendor application opens in a normal top-level browser.
- Events use slash commands, webhooks, or controlled PolySaaS wrappers.
- The green bar remains on the PolySaaS origin.

## Slack HTTP path (already designed)

Canonical event:
- action_path = `/events/slack/command/poly`
- method = `POST`
- direction = `REQ`
- event_key = `slack.command.poly`

Flow:
```
/poly in Slack
→ POST /hooks/slack/commands/
→ verify signature + team_id (403 if invalid)
→ write mailbox / publish envelope
→ immediate ephemeral ack
→ consumer: exact match → run work
→ CallBackData + DoseMessage → bar
```

HTTP request never runs the atomic. Publish/mailbox failure may return retryable 503.

## Event generators

- Flexible assignment: each webhook/mailbox can be bound to a chosen consumer.
- Multiple generators (Slack /poly, later HubSpot, etc.) share the same mailbox + consumer pattern.
- Do not hard-code a second orchestration engine per provider.

## Envelope (canonical)

```json
{
  "kind": "polysaas.trigger.v1",
  "event_id": "tenant-safe-stable-hash",
  "correlation_id": "uuid",
  "tenant_schema": "tenant_one",
  "source": "slack",
  "action_path": "/events/slack/command/poly",
  "method": "POST",
  "direction": "REQ",
  "event_key": "slack.command.poly",
  "actor": { "external_user_id": "U123", "team_id": "T123" },
  "payload": { "command": "/poly", "text": "...", "channel_id": "C123" },
  "received_at": "ISO-8601"
}
```

Dedup: `(tenant_schema, event_id)`. Mailbox TTL: timeout if not consumed.

## Out of scope unless owner says so

- Mapping localhost:8888 to Slack
- HubSpot adapter
- New Instruction schema migration
- Delayed Slack response_url
- Reconstructing or framing complete vendor SPAs
- Arbitrary executable bookmark actions

## Separation from PolySniffer Native

- **PolySniffer Native** (specialized discovery HAR via forwarder) is documented
  in `documentation/architecture/POLYSNIFFER_NATIVE_FORWARDER.md`.
- **This mailbox model** is production event delivery. Do not conflate the two tracks.
- Vendor SaaS production does not require Native capture or a passthrough product.

## Implemented Slack slice

- Contact and sale wireframe actions publish real mailbox envelopes.
- Consumers create an Odoo contact or draft quotation asynchronously.
- The bar reports queue, processing, success, failure, expiration, and
  missing-consumer states.
- `/poly` remains the canonical Slack slash-command event path.

Do not invent a second orchestration engine.

## Done when

- /poly acks in Slack
- Mailbox row exists then consumer runs
- Bar shows success/failure
- Production path does not require Slack inside PolySniffer pane (Native sniff remains optional discovery)