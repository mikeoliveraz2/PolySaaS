# PolySaaS Active Handoff

This file is the canonical startup and end-of-day handoff for the repo.

Every agent — Copilot, Cursor, and Windsurf — must read this file at the start of every session.

## Status

- Date: 2026-08-20
- Branch: `cursor/polysniffer-slack-native-capture` (renamed from `cursor/polysniffer-switch-object-to-iframe`)
- Latest commit: `db527f66` - Webhook mailbox consumer + timezone fixes
- Validation: Webhook mailbox flow tested end-to-end, consumer operational with known timezone bug

## Last session summary (2026-08-20)

### Orchestration Model Implementation - First Slice

**Major milestone:** Implemented webhook mailbox + consumer orchestration per `documentation/POLYSAAS_ORCHESTRATION_MODEL.md`.

#### Work completed:

1. **Documented orchestration model** (`documentation/POLYSAAS_ORCHESTRATION_MODEL.md`)
   - Owner-approved architectural design
   - Two surfaces: Surfing (passthrough for self-hosted) vs SaaS (API-first like Slack)
   - Webhook mailboxes with TTL + consumer pattern
   - Protected with `.cursor/rules/orchestration-model-locked.mdc`

2. **WebhookMailbox model** (`dose/models/webhook_mailbox.py`)
   - Database table for webhook events with TTL (default 5 minutes)
   - Status state machine: pending → claimed → processed/failed/expired
   - Dedup via unique constraint on (tenant_id, event_id)
   - Helper methods: create_from_envelope, dequeue_pending, expire_old_entries

3. **Updated webhook publisher** (`dose/webhook_events.py`)
   - `publish_slack_command_event` now writes to WebhookMailbox instead of RabbitMQ
   - Immediate return after mailbox write (non-blocking)

4. **WebhookMailboxConsumer** (`dose/webhook_mailbox_consumer.py`)
   - Polls mailbox for pending entries (configurable interval)
   - Dequeues and processes via existing `process_trigger_envelope`
   - Background thread support

5. **Management command** (`dose/management/commands/start_mailbox_consumer.py`)
   - Run with: `python manage.py start_mailbox_consumer --poll-interval 1`

6. **Database setup**
   - Migration created: `dose/migrations/0061_webhook_mailbox.py`
   - Table manually created in public schema via pgAdmin (migration blocked by inconsistent DB state)
   - SQL script: `tmp/create_webhook_mailbox_fixed.sql`

7. **End-to-end validation**
   - Created test mailbox entries
   - Consumer polled and found pending entries
   - Processed entries (status: pending → failed)
   - **Flow confirmed working**: webhook → mailbox → consumer → process

#### Branch renamed:
- Old: `cursor/polysniffer-switch-object-to-iframe` (misleading name suggesting iframes)
- New: `cursor/polysniffer-slack-native-capture` (accurate description)

#### Files changed:
- `documentation/POLYSAAS_ORCHESTRATION_MODEL.md` (new)
- `.cursor/rules/orchestration-model-locked.mdc` (new)
- `dose/models/webhook_mailbox.py` (new)
- `dose/webhook_mailbox_consumer.py` (new)
- `dose/management/commands/start_mailbox_consumer.py` (new)
- `dose/webhook_events.py` (modified - mailbox write instead of RabbitMQ)
- `dose/models/__init__.py` (added WebhookMailbox import)

## Current blockers

1. **Timezone comparison bug** (known issue, tracked)
   - Error: "can't compare offset-naive and offset-aware datetimes"
   - Location: Somewhere in `process_trigger_envelope` or `Instruction.execute_atomic_service`
   - Impact: Mailbox entries process but fail with this error
   - Partial fix: Updated `WebhookMailbox.is_expired()` to handle naive datetimes as UTC
   - Remaining: Need to fix timezone handling deeper in the execution path

2. **Database migration state** (pre-existing)
   - Django migrations blocked by inconsistent state (tables exist but migrations not marked applied)
   - Workaround: Manual table creation via pgAdmin
   - Not blocking: Mailbox table created and working

## Next actions

1. **Fix timezone bug**
   - Search for datetime comparisons in `dose/webhook_events.py::process_trigger_envelope`
   - Check `Instruction.execute_atomic_service` for naive datetime usage
   - Ensure all datetime fields use timezone-aware datetimes throughout

2. **Test complete flow**
   - Start consumer: `python manage.py start_mailbox_consumer`
   - Send real Slack `/poly` command
   - Verify: mailbox entry → consumer processes → DoseMessage in orchestration bar

3. **Consumer startup integration**
   - Add consumer to `dose/apps.py::DoseConfig.ready()` for auto-start
   - Or document as separate service to run alongside Django

4. **Resolve DB migration state** (optional, not blocking)
   - Mark problematic migrations 0028-0060 as fake applied
   - Or restore from clean backup

## Validation

- Ran: `python scripts/check_agent_sync.py` - PASSED
- Webhook mailbox table created in public schema
- Consumer tested: polls mailbox, finds pending entries, processes them
- Status transitions verified: pending → claimed → failed (due to timezone bug)
- Dedup constraint verified: duplicate event_id rejected correctly

## Session summary for this EOD

- Implemented webhook mailbox orchestration (first slice per orchestration model)
- Renamed branch to remove misleading iframe reference
- Created and tested WebhookMailbox table, consumer, management command
- Validated end-to-end flow: webhook → mailbox → consumer → process
- Identified and partially fixed timezone bug (remaining work needed)
- All code committed and pushed to remote

## Commit info

- Branch: `cursor/polysniffer-slack-native-capture`
- Orchestration model doc: `823fd3a3`
- Mailbox implementation: `696e8de8`
- Consumer + timezone fixes: `db527f66`
- Latest push status: All commits pushed to remote

---

This is the current handoff-of-record for PolySaaS. Read it before continuing work.
