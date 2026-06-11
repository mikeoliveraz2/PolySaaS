# BINGO — Passthrough Orchestration Bar + Instruction Embed Modal

**Date:** 2026-06-11  
**Declared by:** Michael  
**Commit:** `PENDING` (hash recorded in immediate follow-up commit)  
**Baseline:** BINGO `8293f54f` — Mattermost Composer Roles v45 (2026-06-11)  
**Test tenant:** PolySaaS Test 150 (`polysaast150`, team `polysaas-test-150`)  
**Test URL:** `http://localhost:8000/pt/admin/polysaas-mattermost.onrender.com/polysaas-test-150/channels/town-square`

---

## What Was Achieved

Subscribers can create and edit **Instructions** directly from any passthrough page (Mattermost Town Square, Odoo, Nextcloud) without leaving the wrapped admin shell.

### Certified behaviors

| Feature | Status |
|---------|--------|
| Green **POLYSAAS ORCHESTRATION ACTIVE** bar on passthrough pages | ✓ |
| **Action Path** reflects current browser path under `/pt/admin/...` | ✓ |
| Green **+ Insert Orchestration Instruction** button | ✓ |
| Modal iframe opens form-only Instruction add/change (not full admin chrome) | ✓ |
| Dark theme in modal matches parent session (Bootswatch + `orch_theme` / `orch_mode`) | ✓ |
| `requestpath`, `match_type`, `direction`, `requestmethod` prefilled from action path | ✓ |
| **Atomic Service** dropdown (registry-driven, tenant-scoped) | ✓ |
| Select2 dark-mode styling in embed modal | ✓ |
| **`parameters_json` auto-fill** with sample required fields on service selection | ✓ |
| Phase 1 **Capital Raise atomic services** registered and selectable | ✓ |
| API: match existing instruction vs create mode | ✓ |
| `postMessage` to parent on save (`ps-orch-instruction-saved`) | ✓ |
| `X-Frame-Options: SAMEORIGIN` on embed views | ✓ |

---

## User Flow (End-to-End)

```
Passthrough page (e.g. Mattermost Town Square)
    │
    ├─ Green orchestration bar shows Action Path: /polysaas-test-150/channels/town-square
    │
    └─ User clicks "+ Insert Orchestration Instruction"
            │
            ├─ JS: GET /dose/api/orchestration-instruction/<encoded-path>/?method=GET
            │       → { mode: "create"|"update", admin_url: embed add/change URL }
            │
            └─ Modal opens iframe → /dose/orchestration/instruction/add/?requestpath=...&orch_theme=...&orch_mode=...
                    │
                    ├─ EmbedInstructionAdmin (form-only template)
                    ├─ Atomic Service dropdown → on change fills parameters_json samples
                    └─ Save → redirect in iframe → postMessage to parent → modal can close
```

---

## Architecture

### Frontend (passthrough shell)

| Component | File | Role |
|-----------|------|------|
| Orchestration bar HTML | `dose/templates/admin/display.html`, `passthrough_embed.html` | Bar + script include |
| Bar + modal + API client | `dose/static/admin/js/orchestration_instruction_button.js` | Action path, CSRF, theme sync, iframe modal |
| Modal shell | `dose/templates/admin/includes/orchestration_instruction_modal.html` | Fixed overlay + iframe |

**DOM IDs (stable contract):**

- `#polysaas-orchestration-bar` — green bar container
- `#pss-action-path` — action path display
- `#pss-orch-status` — match status text
- `#pss-insert-instruction-btn` — green insert button
- `#ps-orch-instruction-modal` — modal root
- `#ps-orch-instruction-iframe` — embed target

**Theme propagation:** Parent reads `data-ps-theme`, `display_mode` cookie, and Jazzmin Bootswatch link; appends `orch_theme` and `orch_mode` to embed URLs so the iframe matches dark/light session.

### Backend (embed admin)

| Component | File | Role |
|-----------|------|------|
| Embed routes | `dose/urls.py` | `/dose/orchestration/instruction/add|change/` |
| Embed admin class | `dose/views/orchestration_instruction_embed.py` | `EmbedInstructionAdmin` — popup form, theme context |
| Form template | `dose/templates/admin/dose/instruction/embed_form.html` | Extends `admin/base.html` (not `base_site.html`) — no sidebar |
| Instruction admin | `dose/admin.py` | `InstructionAdmin`: executescript `<select>`, `parameters_json` in main fieldset, `_allow_sameorigin_iframe` |
| Match API | `dose/views/orchestration.py` | `get_orchestration_instruction` — uses `find_matching_instructions` |
| Match engine | `dose/passthrough/orchestration_hook.py` | Tenant-scoped instruction matching (unchanged contract, certified compatible) |

### Atomic services (Phase 1 — Capital Raise)

All subclass `AtomicServiceBase`, auto-register via `atomic_services_registry.py`, read config from `Instruction.parameters_json`:

| Service | Purpose |
|---------|---------|
| `PublishToPubSubService` | GCP Pub/Sub or MQ fallback |
| `EmailToSelfService` | Email alert to configured recipient |
| `AddToMLDatasetService` | Append JSONL training records |
| `ExportToRESTAPIService` | POST payload to external REST URL |
| `CreateGitHubIssueService` | Open GitHub issue via API |
| `NotifyAIPeersService` | Mattermost @peer notifications |
| `CreateCeleryTaskService` | Enqueue Celery task by name |
| `WriteToBigQueryService` | Insert row into BigQuery table |
| `GenerateImageAndExportService` | AI image generation + optional export |

Shared helpers: `dose/services/atomic_service_utils.py` (`instruction_config`, `request_snapshot`, `maybe_save_callback`, etc.)

### parameters_json sample auto-fill

| Component | File | Role |
|-----------|------|------|
| Sample catalog (Python SSOT) | `dose/services/atomic_service_param_samples.py` | Dict per service class name |
| API fallback | `dose/views/atomic_service_param_sample.py` | `GET /dose/api/atomic-service-param-sample/?service=...` |
| Inline embed | `param_samples_script.html` | `window.PS_ATOMIC_SERVICE_PARAM_SAMPLES` |
| Client logic | `instruction_atomic_service.js` | On `executescript` change → pretty JSON; treats `null`/`{}` as empty |
| Dark Select2 | `ps_instruction_form.css` | `.ps-instruction-select2-dark` dropdown styling |

**Bug fixed during certification:** `InstructionAdmin.Media` had `instruction_atomic_service.js?v=...` — Django static resolved the query string as part of the filename (`%3Fv%3D...`) → **404**, script never ran. Fixed by loading JS from templates without `?v=` in Media path.

---

## API Reference

### `GET /dose/api/orchestration-instruction/<path:action_path>/`

**Query:** `method` (default `GET`)

**Response (create):**
```json
{
  "status": "success",
  "mode": "create",
  "action_path": "/polysaas-test-150/channels/town-square",
  "admin_url": "/dose/orchestration/instruction/add/?requestpath=...&orch_theme=darkly&orch_mode=dark",
  "match_count": 0
}
```

**Response (update):** same shape with `mode: "update"`, `id`, `executescript`, `instruction_text`.

### `GET /dose/api/atomic-service-param-sample/?service=PublishToPubSubService`

Returns `{ "status": "ok", "sample": { ... } }`.

### Embed URLs

- Add: `/dose/orchestration/instruction/add/?requestpath=<path>&match_type=path&direction=REQ&requestmethod=GET&orch_theme=<theme>&orch_mode=<mode>`
- Change: `/dose/orchestration/instruction/<id>/change/?_popup=1&orch_theme=...`

---

## Handler Isolation Compliance

Orchestration bar logic lives in:

- Passthrough **templates** (bar markup + script tag only)
- **Dedicated views** (`orchestration.py`, `orchestration_instruction_embed.py`)
- **InstructionAdmin** (form field rendering)

No Mattermost/Odoo-specific branches were added to `forwarding.py`, `middleware.py`, or `registry.py`. Instruction matching reuses the existing `orchestration_hook.find_matching_instructions` tenant-scoped engine.

---

## Files In This BINGO Commit

| File | Change |
|------|--------|
| `dose/static/admin/js/orchestration_instruction_button.js` | Bar, modal, API, theme sync |
| `dose/static/admin/js/instruction_atomic_service.js` | Select2 dark + parameters_json auto-fill |
| `dose/static/admin/css/ps_instruction_form.css` | Dark Select2 + form styles |
| `dose/templates/admin/includes/orchestration_instruction_modal.html` | Modal HTML/CSS |
| `dose/templates/admin/dose/instruction/embed_form.html` | Iframe form-only template |
| `dose/templates/admin/dose/instruction/change_form.html` | Samples script + JS load order |
| `dose/templates/admin/dose/instruction/param_samples_script.html` | Inline sample JSON |
| `dose/templates/admin/display.html` | Orchestration bar |
| `dose/templates/admin/passthrough_embed.html` | Orchestration bar + modal include |
| `dose/views/orchestration.py` | `get_orchestration_instruction`, theme helpers, embed URLs |
| `dose/views/orchestration_instruction_embed.py` | `EmbedInstructionAdmin` |
| `dose/views/atomic_service_param_sample.py` | Sample API |
| `dose/admin.py` | `InstructionAdmin` fieldsets, executescript select, iframe decorator |
| `dose/urls.py` | Embed + API routes |
| `dose/passthrough/orchestration_hook.py` | Certified compatible (matching engine) |
| `dose/services/atomic_service_utils.py` | Shared atomic helpers |
| `dose/services/atomic_service_param_samples.py` | Sample parameters catalog |
| `dose/services/publish_to_pub_sub_service.py` | Phase 1 service |
| `dose/services/email_to_self_service.py` | Phase 1 service |
| `dose/services/add_to_ml_dataset_service.py` | Phase 1 service |
| `dose/services/export_to_rest_api_service.py` | Phase 1 service |
| `dose/services/create_github_issue_service.py` | Phase 1 service |
| `dose/services/notify_ai_peers_service.py` | Phase 1 service |
| `dose/services/create_celery_task_service.py` | Phase 1 service |
| `dose/services/write_to_bigquery_service.py` | Phase 1 service |
| `dose/services/generate_image_and_export_service.py` | Phase 1 service |
| `*.bak` | Pre-edit backups per `bak-before-edit` rule |

---

## Verification Checklist (Certified 2026-06-11)

1. Log in as staff user on tenant with Mattermost passthrough enabled.
2. Open Town Square passthrough URL (see test URL above).
3. Confirm green orchestration bar visible with correct action path.
4. Click **+ Insert Orchestration Instruction** — modal opens (not sad-face / not full admin).
5. Confirm dark theme readable (inputs, Select2 dropdown, labels).
6. Select **PublishToPubSubService** — `parameters_json` fills with sample topic/payload (not `null`).
7. Set `requestpath` to action path, save — instruction created in tenant schema.
8. Re-open modal on same path — API returns `mode: update` with instruction id.
9. Parent receives `postMessage` `{ type: 'ps-orch-instruction-saved' }` after save.

---

## Known Limitations

- Modal uses **iframe** (allowed: admin form embed on same origin, not passthrough SPA iframe).
- `parameters_json` overwrite prompts if field already edited when changing atomic service.
- Phase 1 atomic services require runtime credentials (GCP, GitHub token, etc.) via Parameters model or env — samples are templates only.
- Full admin Instruction change still available at `/admin/dose/instruction/` for power users.

---

## Restore Points

- **BINGO ZIP:** `D:\BINGO ZIPS\BINGO_ORCHESTRATION_BAR_INSTRUCTION_EMBED_2026-06-11.zip`
- **Git:** this commit on `main`

---

## Relationship to Prior BINGOs

- **Mattermost Composer v45 (`8293f54f`):** Passthrough shell and Town Square remain working; orchestration bar is additive UI on the same embed template stack.
- **Mattermost SSO BINGOs:** Shim/auth unchanged by this commit.
- **Odoo Layout Fix (`passthrough_embed.html` freeze):** Template updated for orchestration bar; freeze banner updated to include this BINGO.
