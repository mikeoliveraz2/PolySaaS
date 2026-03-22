# BINGO: Cross-App Sync Demo + Mapping Engine + Instructions

**Date:** 2026-03-22
**Status:** Complete and tested
**Branch:** commit-changes

---

## What Was Done

### 1. Mapping Engine (New Infrastructure)
- Created `dose/models/mapping.py` with `Mapping` and `InstructionMapping` models
- Created `dose/services/mapping_engine.py` with expression parser and pipe operators
- Created `dose/management/commands/test_mapping.py` for offline validation
- Updated `dose/admin.py` with `MappingAdmin` and `InstructionMappingInline`
- Updated `dose/models/__init__.py` with new imports
- Migration: `0024_merge_20260321_1554.py`, `0025_add_mapping_and_instruction_mapping.py`

### 2. Atomic Service Integration
- Updated `dose/services/endpoint_data_extractor.py` to use Mapping Engine with fallback to hard-coded catalog
- Updated `dose/services/odoo_customer_sync.py` to use Mapping Engine with fallback
- Created `dose/services/app_endpoint_catalog.py` (extracted from endpoint_data_extractor)

### 3. Dolibarr Sniff and Configuration
- Sniffed Dolibarr 19.0.2 via PolySniffer -- captured 43 form fields from `/societe/card.php` POST
- Created 2 Mapping records (Dolibarr POST -> Normalized, Normalized -> Odoo partner)
- Created 2 Instructions in the **olient** tenant schema:
  - `/societe/card.php` POST -> EndpointDataExtractorService
  - `/mq/polysaas.crossapp.customer.created` POST -> OdooCustomerSyncService
- Validated both mappings with test data via `test_mapping` command

### 4. Passthrough Fix
- Fixed `dose/passthrough/forwarding.py` tuple return handling from handlers
- Fixed Unicode encoding errors in `dose/passthrough/middleware.py` and `dose/context_processors.py`

### 5. Tenant Isolation Rule
- Created `.cursor/rules/tenant-isolation.mdc` enforcing:
  - All records in tenant schema, never public
  - Migrations must hit all schemas
  - WordPress edits go to polysaas.online (not azure staging)

### 6. Docker Compose
- Created `docker-compose.demo-sync.yml` for Dolibarr, Odoo, RabbitMQ containers

### 7. Website (polysaas.online)
- Created Cross-App Sync page with 12 screenshots (Dolibarr sniff steps, Odoo result, Instruction admin)
- Added dark mode toggle and full dark mode CSS overrides
- Updated Dynamic Orchestration page with "See It In Action" link
- Updated PolySniffer page with "PolySniffer in Action" link

### 8. Documentation
- `documentation/Cross-App Sync Demo - Dolibarr to Odoo.md` -- architecture and setup guide
- `documentation/Dolibarr Sniff and Cross-App Mapping - 2026-03-22.md` -- sniff results, mappings, instructions, validation, Odoo result
- `documentation/Mapping Model Schema - Implementation.md` -- expression syntax, pipe operators, admin setup

---

## Files Modified (Source)

| File | Change |
|------|--------|
| `dose/admin.py` | MappingAdmin, InstructionMappingInline |
| `dose/models/__init__.py` | Import Mapping, InstructionMapping |
| `dose/passthrough/forwarding.py` | Tuple return fix |
| `dose/passthrough/middleware.py` | Unicode encoding fix |
| `dose/context_processors.py` | Unicode encoding fix |

## Files Created (Source)

| File | Purpose |
|------|---------|
| `dose/models/mapping.py` | Mapping + InstructionMapping models |
| `dose/services/mapping_engine.py` | Expression parser, pipe operators, apply_mapping |
| `dose/services/app_endpoint_catalog.py` | Hard-coded endpoint matching (fallback) |
| `dose/services/endpoint_data_extractor.py` | Mapping Engine integration |
| `dose/services/odoo_customer_sync.py` | Mapping Engine integration |
| `dose/management/commands/test_mapping.py` | Offline mapping validation |
| `dose/management/commands/setup_demo_sync.py` | Demo sync setup command |
| `dose/management/commands/setup_crossapp_sync.py` | Cross-app sync setup |
| `dose/migrations/0024_merge_20260321_1554.py` | Migration merge |
| `dose/migrations/0025_add_mapping_and_instruction_mapping.py` | Mapping tables |
| `docker-compose.demo-sync.yml` | Demo containers |
| `.cursor/rules/tenant-isolation.mdc` | Tenant isolation rule |

---

## Pending (Not in This Commit)

- Dolibarr passthrough handler (CSS/JS rewriting for `/pt/admin/dolibarr/`)
- End-to-end live test through passthrough
- `dose_trafficlog` table migration (PolySniffer persistence)
