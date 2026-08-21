# Proposal: Webhook mailboxes + consumer orchestration

**Status: OWNER APPROVED — implement only after I say go**

**Do not invent Slack passthrough, Native sniff, iframes, or /dose/sniff/{id}**

## Purpose

Unify how events are bound and executed.

- Webhooks are declared up front and act as dumb mailboxes.
- Consumers do updates and messaging asynchronously.
- While surfing, the user attaches orchestration the same way as before, but the bind target is a webhook → consumer, not "run an atomic inside the HTTP request."

## Locked rules

1. Webhooks do not run atomics. They accept, persist, timeout.
2. Tenant for Slack is resolved only from stored team_id mapping.
3. Slack is API-first. No SlackPassthroughHandler. No slack_native_sniff. No proxy of slack.com or polysaasworkspace.slack.com.
4. Native remains for self-hosted apps (Odoo, Nextcloud, Mattermost, Dolibarr): raw capture of cookies/assets/traffic to build handlers.
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

## Two surfaces

### 1) Surfing (passthrough / discovered apps)

- User navigates the real app under the usual PolySaaS look-and-feel.
- To add orchestration: same pattern as today — stop at a reasonable place.
- What they attach: identify the **webhook** for that event, then attach a **dynamic action consumer**.
- Later, when that webhook fires, the mailbox + consumer run. Not the browse request itself.

### 2) Slack (and similar SaaS)

- Main window: **real Slack** (normal browser or desktop). No PolySaaS proxy.
- Green bar: PolySaaS chrome as **embedded or separate div** so look-and-feel matches passthrough.
- Events: slash command / API webhook → mailbox → consumer.
- Binding UI: pick webhook (e.g. /poly) → attach consumer. Same gesture, no Slack site scraping.

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

- Slack browser proxy / Native / sign_in capture
- Mapping localhost:8888 to Slack
- HubSpot adapter
- New Instruction schema migration
- Delayed Slack response_url
- Changing frozen PolySniffer layout
- "Should Native open in an external browser?" for Slack — answer is no, question is invalid

## First implement slice (only if I say go)

- Confirm mailbox persist + TTL + consumer dequeue for /poly.
- Keep verify → ack → async work.
- Binding UI: attach consumer to webhook (same surfing pattern).
- Slack chrome: bar as sibling div or embed — no proxy.

Do not start Slack handler/registry work. Do not edit AI_RULES.md to invent a Native-Slack exception.

## Done when

- /poly acks in Slack
- Mailbox row exists then consumer runs
- Bar shows success/failure
- No Slack site in a PolySniffer pane is required
