# Mapping Model Schema - Implementation

**Date:** 2026-03-21
**Status:** Implemented and verified
**Files changed:**
- `dose/models/mapping.py` (new)
- `dose/services/mapping_engine.py` (new)
- `dose/models/__init__.py` (updated)
- `dose/admin.py` (updated)
- `dose/services/endpoint_data_extractor.py` (updated)
- `dose/services/odoo_customer_sync.py` (updated)
- `dose/migrations/0024_merge_20260321_1554.py` (auto-generated merge)
- `dose/migrations/0025_add_mapping_and_instruction_mapping.py` (auto-generated)

---

## Purpose

Move field extraction and transformation logic out of hard-coded Python services and into configurable, reusable, database-driven mappings. This makes `EndpointDataExtractorService` and `OdooCustomerSyncService` generic -- they no longer need code changes when a new app integration is added, only new Mapping records in the admin.

The hard-coded catalog (`app_endpoint_catalog.py`) and the hard-coded `_map_to_odoo_partner` method are preserved as fallbacks. If no Mapping records are attached to an Instruction, existing behavior is unchanged.

---

## Architecture

```
Instruction (existing)
    |
    |-- InstructionMapping (new, order=1)
    |       |
    |       +-- Mapping "Dolibarr POST -> Normalized Customer"
    |           direction: SOURCE_TO_NORMALIZED
    |           field_mappings: { "name": "request.POST.name|strip", ... }
    |
    |-- InstructionMapping (new, order=2)
            |
            +-- Mapping "Normalized Customer -> Odoo Partner"
                direction: NORMALIZED_TO_TARGET
                field_mappings: { "name": "payload.name", "email": "payload.email|lower", ... }
```

When an Instruction fires, the attached service checks for InstructionMappings. If found, the Mapping engine resolves expressions against the request/payload context. If not found, the original hard-coded logic runs.

---

## Models

### Mapping (`dose_mapping`)

| Field | Type | Description |
|-------|------|-------------|
| `name` | CharField(200) | Human-readable name |
| `slug` | SlugField(120) | Unique reference key |
| `description` | TextField | Optional notes |
| `direction` | CharField(25) | `SOURCE_TO_NORMALIZED` or `NORMALIZED_TO_TARGET` |
| `source_endpoint` | FK to PassThroughEndpoint | Optional: source system |
| `target_endpoint` | FK to PassThroughEndpoint | Optional: target system |
| `field_mappings` | JSONField (dict) | `{target_field: source_expression}` |
| `transformations` | JSONField (list) | Post-mapping rules |
| `version` | PositiveSmallIntegerField | For tracking revisions |
| `is_active` | BooleanField | Enable/disable without deleting |
| `tenant` | FK to Tenant | Multi-tenant isolation (inherited from TenantAwareModel) |
| `created_at` | DateTimeField | Auto-set on creation |
| `updated_at` | DateTimeField | Auto-set on save |

**Unique constraint:** `(slug, direction)` -- same slug can have both directions.

### InstructionMapping (`dose_instructionmapping`)

| Field | Type | Description |
|-------|------|-------------|
| `instruction` | FK to Instruction | The instruction this mapping belongs to |
| `mapping` | FK to Mapping | The mapping to apply |
| `order` | PositiveSmallIntegerField | Execution order (lower = first) |
| `enabled` | BooleanField | Toggle without removing |

**Unique constraint:** `(instruction, mapping)` -- each mapping attached once per instruction.

---

## Expression Syntax

Expressions are strings in the `field_mappings` dict values. They resolve against a context dict containing `request`, `payload`, `POST`, `GET`, etc.

### Path Resolution

| Expression | Resolves to |
|------------|-------------|
| `request.POST.name` | Django request POST field "name" |
| `request.GET.page` | Django request GET parameter "page" |
| `payload.email` | Top-level key in a dict payload (MQ message) |
| `payload.address.city` | Nested dict key |

### Literals and Functions

| Expression | Result |
|------------|--------|
| `'CUSTOMER'` | The literal string "CUSTOMER" |
| `now:iso` | Current UTC datetime in ISO format |

### Pipe Operators

Pipes are chained left to right: `payload.name|strip|lower|default:Unknown`

| Pipe | Effect |
|------|--------|
| `\|strip` | `str.strip()` |
| `\|lower` | `str.lower()` |
| `\|upper` | `str.upper()` |
| `\|int` | Cast to integer (None if fails) |
| `\|int:1:0` | Truthy -> int(1), falsy -> int(0) |
| `\|bool` | Python truthy check |
| `\|bool:yes:no` | Truthy -> "yes", falsy -> "no" |
| `\|default:value` | Fallback if None or empty string |
| `\|prefix:MR-` | Prepend string |
| `\|suffix:-END` | Append string |
| `\|truncate:120` | Cap string to max length |
| `\|email` | Validate email format, None if invalid |
| `\|if:path.to.check` | Return value only if another context field is truthy, else None |
| `\|coalesce:path.fallback` | Use value if non-empty, else resolve fallback path from context |

### Special Meta-Fields

When used in `EndpointDataExtractorService`, these meta-fields in the mapping output control message routing:

| Key | Purpose | Example |
|-----|---------|---------|
| `_topic` | MQ topic/routing key | `polysaas.dolibarr.customer.created` |
| `_source_app` | Source application name | `dolibarr` |
| `_entity` | Entity type | `customer` |
| `_action` | Action type | `created` |

These are stripped from the normalized data before publishing.

### Transformations

Post-mapping rules applied to the result dict. Defined as a JSON list:

```json
[
  {"field": "full_address", "concat": ["street", "zip", "city"], "separator": ", "},
  {"field": "type", "value": "customer"}
]
```

| Key | Type | Description |
|-----|------|-------------|
| `field` | string | Target field name in result |
| `value` | any | Set field to a fixed value |
| `concat` | list of strings | Concatenate named fields |
| `separator` | string | Separator for concat (default: space) |

---

## Example: Dolibarr Customer -> Normalized

**Mapping record:**
- Name: `Dolibarr Thirdparty -> Normalized Customer`
- Slug: `dolibarr-customer-to-normalized`
- Direction: `SOURCE_TO_NORMALIZED`
- Source Endpoint: Dolibarr PassThroughEndpoint

**field_mappings:**
```json
{
  "name": "request.POST.name|strip",
  "email": "request.POST.email|lower|strip",
  "phone": "request.POST.phone|strip|default:None",
  "address": "request.POST.address|strip",
  "zip": "request.POST.zip|strip",
  "town": "request.POST.town|strip",
  "country_code": "request.POST.country_code|upper",
  "_topic": "'polysaas.dolibarr.customer.created'",
  "_source_app": "'dolibarr'",
  "_entity": "'customer'",
  "_action": "'created'"
}
```

## Example: Normalized -> Odoo Partner

**Mapping record:**
- Name: `Normalized Customer -> Odoo Partner`
- Slug: `normalized-to-odoo-partner`
- Direction: `NORMALIZED_TO_TARGET`
- Target Endpoint: Odoo PassThroughEndpoint

**field_mappings:**
```json
{
  "name": "payload.name",
  "email": "payload.email",
  "phone": "payload.phone",
  "street": "payload.address",
  "zip": "payload.zip",
  "city": "payload.town",
  "_country_code": "payload.country_code",
  "customer_rank": "'1'|int",
  "is_company": "'True'|bool"
}
```

---

## Service Integration

### EndpointDataExtractorService

`execute_and_save` flow:

1. Extract raw data from request body / POST / MQ message
2. Call `_try_mapping_engine(instruction_row, request, raw_data)`
   - Checks if InstructionMappings exist for this instruction
   - If yes: builds context, runs `apply_mappings_for_instruction`, extracts meta-fields
   - If no: returns None (triggers fallback)
3. If step 2 returned None: fall back to `app_endpoint_catalog.match_endpoint` + `normalize_data`
4. Publish to MQ, save CallBackData as before

### OdooCustomerSyncService

`execute_and_save` flow:

1. Extract message data from MQ mock request
2. Call `_map_with_engine_or_fallback(instruction_row, normalized, raw_data)`
   - Checks if InstructionMappings exist for this instruction
   - If yes: builds context from normalized data, runs mapping engine
   - If no: falls back to `_map_to_odoo_partner` (hard-coded field map)
3. Sync to Odoo via XML-RPC as before

---

## Admin Interface

### Mapping Admin

- **List view:** name, slug, direction, source/target endpoints, active status, version, updated date
- **Filters:** direction, is_active, source_endpoint, target_endpoint
- **Search:** name, slug, description
- **Fieldsets:** grouped into Basic Info, Endpoints (collapsible), Field Mappings, Transformations (collapsible), Timestamps (collapsible)
- **Slug auto-populated** from name

### InstructionMapping Inline

Appears on the Instruction change form as a tabular inline. Fields: mapping (autocomplete), order, enabled. Allows attaching one or more Mappings to any Instruction directly from the Instruction edit page.

---

## Migration Notes

- Migration `0024` merges two conflicting 0023 branches
- Migration `0025` creates `dose_mapping` and `dose_instructionmapping` tables
- Tables were applied directly via SQL due to the multi-tenant migration system failing on a pre-existing `oauth_application_id` column conflict. The migration was then recorded in `django_migrations` to keep the ORM in sync.

---

## Debug Mode

Add `"_debug": "true"` to any Mapping's `field_mappings` JSON. When the mapping engine processes that mapping, it logs every expression resolution to the Django logger at INFO level:

```
[MappingEngine:DEBUG] Mapping 'dolibarr-thirdparty-post-to-normalized' context keys: {'payload': 'dict'}
[MappingEngine:DEBUG]   name = 'payload.name|strip' -> 'Test Sync 2026'
[MappingEngine:DEBUG]   email = 'payload.email|strip|lower|email' -> 'testsync@example.com'
```

Remove `_debug` (or set to anything other than `"true"`) to disable.

---

## Validation Command

`test_mapping` management command for offline validation of Mapping records.

### List all mappings:
```
python manage.py test_mapping --list
```

### Test a single mapping against a JSON file:
```
python manage.py test_mapping --slug dolibarr-thirdparty-post-to-normalized --file sample.json
```

### Test a single mapping against inline JSON:
```
python manage.py test_mapping --slug dolibarr-thirdparty-post-to-normalized --payload '{"name":"Test"}'
```

### Test all mappings on an Instruction chain:
```
python manage.py test_mapping --instruction-id 5 --file sample.json
python manage.py test_mapping --instruction-path /societe/card.php --file sample.json
```

### Verbose mode (enables _debug on all tested mappings):
```
python manage.py test_mapping --slug my-mapping --file sample.json --verbose
```

Output includes:
- Input payload summary
- Resolved output with None/empty warnings
- Payload fields NOT referenced in the mapping (helps catch unmapped fields)
- For instruction chains: step-by-step results and final merged output

---

## What's Next

1. **Sniff Dolibarr** traffic to identify the exact POST path for new customer creation
2. **Generate Dolibarr handler** from sniffer output for proper passthrough rendering
3. **Create Mapping records** in admin for the Dolibarr -> Normalized and Normalized -> Odoo flows
4. **Create Instructions** that reference these Mappings via InstructionMappings
5. **Test end-to-end:** create customer in Dolibarr via passthrough, verify it appears in Odoo
