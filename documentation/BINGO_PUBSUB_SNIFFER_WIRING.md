# BINGO — Passthrough Sniffer → GCP Pub/Sub Topic Wiring

**Date:** March 31, 2026  
**Status:** COMPLETE — Code verified, `manage.py check` passes  
**Collaboration:** Shela (architecture review) + Cursor/Claude Opus (CC) + MO

---

## Summary

Rewired the sniffer-generated Instruction + MQOutput records so that live passthrough POSTs actually trigger publishing to **GCP Pub/Sub topics** instead of dead-ending with empty `executescript` and RabbitMQ defaults that were never connected.

This closes the loop on the core PolySaaS data pipeline:  
**Sniff → Instruction → Live POST → EndpointDataExtractorService → Pub/Sub Topic → Subscribers**

---

## Requirements Addressed

| Req | Description | Status |
|-----|-------------|--------|
| Passthrough → Topic | Sniffed POST creates Instruction that publishes to a topic on live replay | DONE |
| GCP Pub/Sub primary | All new MQOutput records use `google_pubsub` provider, not `rabbitmq` | DONE |
| executescript wiring | Instructions set `executescript = 'EndpointDataExtractorService'` so DoseRequestController actually runs the publish service | DONE |
| Tenant MQConfig lookup | Pub/Sub project_id and credentials pulled from tenant's active MQConfig | DONE |
| Topic-centric design | One topic per unique POST path; multiple subscribers can process in parallel | DONE |
| Tenant isolation (Req 3) | Instructions and MQOutput scoped to tenant; MQConfig lookup is tenant-first | DONE |

---

## Collaboration Discussion (Shela + MO + CC)

### Context (Shela's Analysis)

Shela reviewed the full CC chat history and identified the **main gaps** from the previous session:

1. Sniffer-generated Instructions had **empty `executescript`** — so even when DoseRequestController matched an Instruction on a live POST, it had no service to execute, and nothing got published.
2. MQOutput records defaulted to **`provider = 'rabbitmq'`** with localhost connection details — but PolySaaS's target broker has always been **GCP Pub/Sub**, not RabbitMQ. RabbitMQ was only used as an early test.
3. No tenant-aware Pub/Sub config wiring existed in the sniffer path — MQOutput was created with hardcoded RabbitMQ fields instead of reading from the tenant's `MQConfig`.

### Shela's Recommended Fix (Prompt for CC)

Shela provided a targeted prompt for Cursor/Opus:
- Set `executescript = 'EndpointDataExtractorService'` on sniffer Instructions
- Set `provider = 'google_pubsub'` on MQOutput with `pubsub_topic` field
- Resolve `pubsub_project_id` and `pubsub_credentials_json` from tenant's active MQConfig
- Keep topic-centric thinking: one topic, multiple subscribers
- Do not introduce RabbitMQ unless as fallback

### CC (Cursor/Opus) Execution

CC traced the full chain before making changes:

1. **Path matching verified:** DoseRequestController uses substring matching (`instr.requestpath in normalized_request_path`). A sniffer instruction with `requestpath = "/odoo/web/dataset/call_kw"` correctly matches a live request to `/pt/admin/odoo/web/dataset/call_kw`.

2. **Service registry verified:** `EndpointDataExtractorService` has `execute_and_save()` and auto-registers in `ATOMIC_SERVICE_REGISTRY` via the scanner in `atomic_services_registry.py`.

3. **Publish chain verified:** `EndpointDataExtractorService._publish_to_pubsub()` queries `MQConfig` for active `google_pubsub` providers, instantiates `PubSubAdapter`, calls `adapter.publish(message, topic=topic)`.

4. **PubSubAdapter.publish() verified:** Accepts `topic` kwarg, builds `topic_path` from `project_id + topic_name`, serializes message as JSON, publishes via `publisher.publish()`.

---

## End-to-End Flow (Complete)

```
1. SNIFF PHASE
   User browses via /pt/admin/{trigger}/... with sniffer enabled
   → ExternalPassthroughMiddleware proxies requests
   → POST requests create TrafficLog records

2. INSTRUCTION CREATION (signal fires on TrafficLog post_save)
   _on_trafficlog_created() runs:
   → Creates Instruction:
       requestpath = "/{trigger}/{post_path}"
       requestmethod = "POST"
       executescript = "EndpointDataExtractorService"   ← KEY FIX
       eventKey = "{trigger}-{path_slug}"
   → Creates MQOutput:
       provider = "google_pubsub"                       ← KEY FIX
       pubsub_topic = "{trigger}-{path_slug}"
       pubsub_project_id = (from tenant MQConfig)

3. LIVE POST PHASE
   User does a real POST to /pt/admin/{trigger}/{post_path}
   → DoseRequestController matches instruction (substring match)
   → Finds executescript = "EndpointDataExtractorService"
   → Looks it up in ATOMIC_SERVICE_REGISTRY
   → Calls EndpointDataExtractorService.execute_and_save(request, instruction_row)

4. PUBLISH PHASE
   EndpointDataExtractorService:
   → Extracts POST body as raw_data
   → Tries Mapping engine, falls back to app_endpoint_catalog
   → Calls _publish_to_pubsub(topic, message)
   → Queries MQConfig for active google_pubsub provider
   → PubSubAdapter.connect() → PubSubAdapter.publish()
   → Message lands on GCP Pub/Sub topic "{trigger}-{path_slug}"

5. DOWNSTREAM (parallel processing)
   Any number of subscribers on that Pub/Sub topic receive the message
   → MQQueueMonitor → MQRequestController path for downstream atomic services
```

---

## Files Changed

### `dose/services/sniffer_stream_actions.py`

| Change | Before | After |
|--------|--------|-------|
| Instruction `executescript` | *(not set — empty)* | `"EndpointDataExtractorService"` |
| Instruction `save_callbackdata` | `False` | `True` |
| MQOutput `provider` | `"rabbitmq"` | `"google_pubsub"` |
| MQOutput topic field | `rabbitmq_queue` / `rabbitmq_routing_key` | `pubsub_topic` |
| MQOutput credentials | hardcoded localhost RabbitMQ | from tenant `MQConfig` via `_resolve_pubsub_defaults()` |
| RabbitMQ fields | `rabbitmq_host`, `_port`, `_username`, `_password`, `_vhost`, `_exchange` | removed |

**New function:** `_resolve_pubsub_defaults(tenant)` — looks up tenant's active `MQConfig` with `provider="google_pubsub"`, falls back to any global active Pub/Sub config, returns `pubsub_project_id` and `pubsub_credentials_json`.

**New docstring:** Full Pub/Sub flow documented at module level (steps 1-5).

### `dose/signals.py` — `_on_trafficlog_created` handler

Same three changes as the batch service:
- `executescript = "EndpointDataExtractorService"` on Instructions
- `provider = "google_pubsub"` + Pub/Sub fields on MQOutput
- Uses `_resolve_pubsub_defaults()` to pull credentials from tenant MQConfig

---

## Pre-Requisites for Live Publishing

Before the first real Pub/Sub message can be published, configure:

1. **MQConfig record** (Django admin → MQ Configurations → Add):
   - Provider: `Google Pub/Sub`
   - `pubsub_project_id`: your GCP project ID
   - `pubsub_credentials_json`: service account JSON key
   - `is_active`: checked
   - Tenant: target tenant (e.g. Oliver Enterprises)

2. **GCP Pub/Sub topic** must exist in the project (or auto-create enabled). Topic names follow: `{trigger}-{path-slug}`, e.g. `odoo-web-dataset-call_kw`.

3. **`google-cloud-pubsub` pip package** must be installed (`pip install google-cloud-pubsub`).

---

## Verification

- `python manage.py check` — 0 issues (0 silenced)
- Path matching logic traced: substring match confirmed working for `/pt/admin/...` URLs
- Service registry auto-scan confirmed: `EndpointDataExtractorService` registers via `execute_and_save` method
- `PubSubAdapter.publish()` signature confirmed: accepts `topic` kwarg

---

## Topic Naming Convention

| Trigger Path | POST Path | Topic Name |
|--------------|-----------|------------|
| `odoo` | `/web/dataset/call_kw` | `odoo-web-dataset-call_kw` |
| `dolibarr` | `/api/index.php/contacts` | `dolibarr-api-index-php-contacts` |
| `erp-next` | `/api/resource/Customer` | `erp-next-api-resource-Customer` |

---

## Note on Existing Records

Instruction and MQOutput records created **before** this change still have empty `executescript` and `provider = "rabbitmq"`. They will not auto-publish. Options:
- Run `create_stream_actions_for_all_sniffed(tenant)` again (uses `get_or_create`, won't duplicate but also won't update existing)
- Manually update existing records in Django admin
- Write a one-time migration to update `executescript` and `provider` on all sniffer-generated records
