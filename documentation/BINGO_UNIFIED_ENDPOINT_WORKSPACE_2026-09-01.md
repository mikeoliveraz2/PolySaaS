# BINGO: Unified Endpoint Workspace

**Date:** 2026-09-01  
**Declared by:** Michael + Shela + Gemini (approved 2026-09-01)  
**Commit:** See push below  

---

## What was verified

**One model, two trigger sources** — unified Odoo, HubSpot, Slack endpoints. Proxy observation and
webhooks/user clicks now both fire the same pipeline: Instruction match → Atomic Service → standard
envelope → CallBackData + UI widget.

- **Data envelope** (`dose/endpoint_data/envelope.py`): one shape for every panel. No per-vendor keys.
- **Generic publisher** (`dose/endpoint_actions/list_publisher.py`): five hardcoded publishers → one `ListSpec`.
- **Endpoint Profile** (`EndpointActionAdapter.profile()`): declarative UI contracts. View no longer branches on app name.
- **Column-driven renderer** (`dose/static/admin/js/endpoint_table.js`): one renderer, column metadata drives layout. XSS fixed (every value through `esc()`).
- **Browse** fixed: HubSpot and base default now correctly return `external` (real app URL) for non-proxied SPAs.
- **Regions reordered:** Identity → Bar → Data (body) → Actions → Wiring (collapsed). Data is now the workspace, not Producers/Consumers.
- **Defects fixed:** chip clipping (176px width), `Inv Invoices` icon concatenation, light-pane contrast (#86efac/#fbbf24 on light panes), chip labels (Dynamic service → API/upload).

## Test coverage

**41 new tests** (envelope contract, publisher, profile, regions, portlet XSS). **88 total pass** across nine affected suites.
Pre-existing tests exercise the deprecated private names through the new publisher — behavior-preservation proof.

**Full suite:** 211 tests, same 10 failures + 9 errors as before work started (verified by stash + rerun).
Not caused by this work; unrelated to endpoint workspace.

## Files frozen

Following freeze rules in `.cursor/rules/bingo-freeze.mdc`:

### Code (source)
- `dose/endpoint_actions/base.py`
- `dose/endpoint_actions/odoo.py`
- `dose/endpoint_actions/hubspot.py`
- `dose/endpoint_actions/list_publisher.py` (new)
- `dose/endpoint_data/__init__.py` (new)
- `dose/endpoint_data/envelope.py` (new)
- `dose/views/endpoint_home.py`
- `dose/services/hubspot_portlet_services.py`
- `dose/tests/test_endpoint_home.py`
- `dose/tests/test_endpoint_envelope.py` (new)

### Markup & styles
- `dose/templates/dose/endpoint_home.html`
- `dose/templates/dose/hubspot_user_context.html`
- `dose/templates/polysniffer/slack_wireframe.html`
- `dose/static/admin/css/endpoint_home.css`
- `dose/static/admin/js/endpoint_home.js`
- `dose/static/admin/js/endpoint_table.js` (new)

### Documentation
- `documentation/POLYSAAS_ENDPOINT_WORKSPACE_MODEL.md` (new, authoritative)
- `documentation/ACTIVE_HANDOFF.md`
- `documentation/ASSET_LOADING_ARCHITECTURE.md` (marked SUPERSEDED)
- `documentation/BINGO_POLYSNIFFER_2.0_PASSTHROUGH_IFRAME_2026-06-24.md` (marked SUPERSEDED)
- `documentation/BINGO_MATTERMOST_SLUG_IDENTITY_SSO_WORKING_2026-08-02.md` (marked SUPERSEDED)
- `documentation/architecture/PolySaaS-Architecture.md` (marked SUPERSEDED)

## Known boundaries

**Not in scope (intentionally untouched):**
- `dose/passthrough/handlers/*` (Mattermost, Odoo, Nextcloud, Slack native)
- `dose/passthrough/forwarding.py`
- `dose/passthrough/orchestration_hook.py`
- `dose/admin.py`

These remain BINGO'd from prior sessions. Passthrough behavior (Browse, capture, token injection) is
unchanged. This work is UI convergence only.

**Pre-existing failures (not caused by this work):**
- `test_tenant_membership` (9 errors)
- `test_hubspot_session` (8 failures)
- `test_polysniffer_locked_architecture` (1 failure)
- `test_slack_native_sniff` (1 failure)

---

## Deployment notes

Hard-refresh endpoint homes (Ctrl+F5) to see new layout. CSS cache `?v=20260901-1`, JS `?v=20260901-1`.

Data region now sits directly under the orch bar. Wiring is collapsed. Create chips moved to overflow.

Deprecated names (`_publish_list_*`, `list_kind`, legacy rows keys) kept for one release; switch to
`envelope` when updating other endpoints.

---

## Next work

- UI review: confirm regions, chip sizes, contrast, CallBackData rendering
- Migrate remaining endpoints to the profile + envelope (repeat pattern from Odoo/HubSpot)
- Retire deprecated names when all endpoints are unified
- Investigate pre-existing test failures (separate session, not this work)
