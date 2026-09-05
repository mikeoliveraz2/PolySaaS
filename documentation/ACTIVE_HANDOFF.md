<!-- THIS CODE IS FROZEN — NO CHANGES TO THIS CODE ARE ALLOWED WITHOUT THE OWNER'S PERMISSION -->
<!-- BINGO: Slack → Odoo + HubSpot dual-feed — 2026-08-28 -->

# PolySaaS Active Handoff

This file is the canonical startup and end-of-day handoff for the repo.
Every agent — Copilot, Cursor, and Windsurf — must read it before work.

## Status

- Date/session: **2026-09-06 — Slack → Odoo Contact Creation Flow**
- Branch: `cursor/polysniffer-slack-native-capture`
- Latest commit before this session: `acd5e1f7` `Fix Geronimo LLM model availability (claude-sonnet-4-6)`
- Current session: included in the commit containing this handoff
- Validation: `python scripts/check_agent_sync.py`, `python manage.py check`, and 18 new tests all pass

### Current Work (2026-09-06): Slack → Odoo Contact Creation Flow

**Objective:** Implement webhook-driven flow where Slack message triggers Odoo contact creation.

**Design:** Deterministic parsing (no LLM in hot path), producer/consumer pattern, green bar feedback, error display.

**Message format:** `New contact: Name, email, Company` (case-insensitive, whitespace-tolerant)

**Components built:**
1. **Webhook endpoint** (`dose/views/slack_events_webhook.py`) — handles Slack Events API, URL verification, signature verification, contact parsing
2. **Envelope builder** (`dose/webhook_events.py`) — `build_slack_contact_envelope`, `publish_slack_contact_event`
3. **URL routing** (`mysite/urls.py`) — `/hooks/slack/events/`
4. **Instruction seeding** (`dose/management/commands/seed_slack_contact_orchestration.py`) — creates `slack.message.contact` instruction
5. **Enhanced feedback** (`dose/messaging.py`) — Slack → Odoo narrative in green bar
6. **Comprehensive tests** (`dose/tests/test_slack_contact_creation.py`) — 18 tests, all passing

**Integration:** Reuses frozen `OdooCreatePartner` atomic service (BINGO 2026-08-28). Follows existing producer/consumer pattern. Mailbox consumer processes envelopes.

**Files changed:**
- `dose/views/slack_events_webhook.py` (new, 184 lines)
- `dose/webhook_events.py` (+ `.bak`)
- `mysite/urls.py` (+ `.bak`)
- `dose/management/commands/seed_slack_contact_orchestration.py` (new, 140 lines)
- `dose/messaging.py` (+ `.bak`)
- `dose/tests/test_slack_contact_creation.py` (new, 400+ lines, 18 tests)
- `documentation/SLACK_CONTACT_CREATION_FLOW.md` (new, comprehensive guide)

**Validation:**
- `python manage.py check` — No issues
- `python manage.py test dose.tests.test_slack_contact_creation --keepdb --noinput` — 18/18 passed
- All new code follows frozen-file protection rules (no edits to frozen services)

**Next steps:**
1. Run `python manage.py seed_slack_contact_orchestration olient` to create instruction
2. Configure Slack Events API subscription to `message.channels`
3. Set webhook URL to `https://your-domain/hooks/slack/events/`
4. Test with: `New contact: Jane Doe, jane@acme.com, Acme Corp`
5. Verify green bar shows: `✓ Slack → Odoo: created contact 'Jane Doe' (jane@acme.com) — partner #42`

---

### Previous session (2026-09-04): Geronimo LLM model fix

**Issue:** Geronimo was configured for unavailable model `claude-sonnet-4-20250514`, causing 404 errors from Anthropic API.

**Fix:** Updated `mysite/settings.py` `LLM_ROUTER_ADMIN_CHAT_MODEL` default from `claude-sonnet-4-20250514` → `claude-sonnet-4-6` (verified available in account via `/v1/models` endpoint).

**Files changed:** `mysite/settings.py` (+ `.bak`)

---

### Previous session (2026-09-03): Geronimo visual refinement

- Replaced the oversized single watermark treatment with a shared 18px repeating `Geronimo AI` SVG pattern.
- Applied the same watermark directly to the panel, response region, input region, and footer so opaque child backgrounds no longer hide it.
- Set the response region darker than the input region and restored dark response text for readability.
- Removed the Standard / ML Studio radio controls from the compact Geronimo dock.
- The dock now always submits `mode: "standard"`; the full-page AI interface and backend ML Studio support were not changed.
- Files: `dose/templates/admin/includes/polysaas_ai_chat_dock.html` and its required `.bak`.
- Human check: hard-refresh an endpoint home and confirm watermark density, response/input contrast, and the absence of mode radio buttons.

- Date/session: **2026-09-02 — Geronimo Chat Integration (Phases 1–5 complete)**
- Branch: `cursor/polysniffer-slack-native-capture`
- Previous BINGO: 8cdd6306 `BINGO: Unified Endpoint Workspace — 2026-09-01`
- Latest commit: 7b9fff95 `Geronimo Chat Integration — Endpoint Homes (Phases 1–5)`
- Docs: `documentation/GERONIMO_CHAT_INTEGRATION.md` (new, comprehensive guide)
- Chat dock integrated into endpoint homes; 170+ preset prompts; page context enhanced; 15 tests pass

### Current Work (2026-09-02): Geronimo Chat Integration

**Phases 1–5 complete.** Chat dock now appears on Odoo/Nextcloud/Mattermost endpoint homes with curated preset prompts.

Changes:
- New files: `dose/ai_prompts/{__init__,prompt_library}.py`, `test_geronimo_integration.py`, `GERONIMO_CHAT_INTEGRATION.md`
- Modified: `base.py` (added `chat_prompts()`, `chat_context_hint()`), `odoo.py` (populate prompts), `views/endpoint_home.py`
  (pass to template), `endpoint_home.html` (include dock), `polysaas_ai_page_context.js` (endpoint context collection)
- All files frozen with BINGO banners (Geronimo Chat Integration — 2026-09-02)
- 9 files changed, 1000+ insertions
- Tests: 15 new (all pass). Full suite clean (same pre-existing failures as before).

**Preset prompts:** Odoo (invoices/contacts/sales), Nextcloud (files), Mattermost (channels/teams).
**Data flow:** User clicks preset or types query → JS collects endpoint context → LLM responds grounded in visible data.
**Next:** Expand to HubSpot, Slack, full Nextcloud/Mattermost coverage (same pattern).

### Previous Unfreeze scope (owner-approved 2026-09-01, Michael + Shela + Gemini)

Authorized to edit, under four standing conditions:

- `dose/views/endpoint_home.py`, `dose/endpoint_actions/registry.py`, `dose/endpoint_actions/odoo.py`,
  `dose/templates/dose/endpoint_home.html`, `dose/static/admin/css/endpoint_home.css`,
  `dose/static/admin/js/endpoint_home.js`
- plus `dose/endpoint_actions/hubspot.py` (added mid-session: it holds the Browse bug and 2 of the 5 duplicated publishers)

Conditions: no edits to `dose/passthrough/handlers/*`, `forwarding.py`, `orchestration_hook.py`, or `admin.py`;
Slack Browse stays top-level; Wiring not promoted to a peer region; `.bak` before every edit, one slice at a time.

**Edited this session:** `endpoint_actions/{odoo,hubspot,base}.py`, `views/endpoint_home.py`,
`templates/dose/endpoint_home.html`, `static/admin/css/endpoint_home.css`, `static/admin/js/endpoint_home.js`,
plus (not frozen, `.bak` taken) `services/hubspot_portlet_services.py`,
`templates/dose/hubspot_user_context.html`, `templates/polysniffer/slack_wireframe.html`,
`tests/test_endpoint_home.py`. `endpoint_actions/registry.py` needed no change.

### Completed (Phases 1–2)

1. **One data envelope** — new `dose/endpoint_data/envelope.py`: `status, title, object_type, count,
   columns[], rows[], empty_message, detail, error`, plus a column catalog transcribed from the three
   JS table builders it will replace, and `validate_envelope()`.
2. **One generic publisher** — new `dose/endpoint_actions/list_publisher.py` (`ListSpec` + `publish_list`).
   Replaces five near-identical `_publish_list_*` functions (3 Odoo, 2 HubSpot). Adapters now declare a spec.
3. **Browse destination fixed** — `HubspotEndpointActionAdapter.browse_mode` `passthrough` → `external`
   (HubSpot login needs the browser-only `csrf.app` cookie a proxy cannot supply). `EndpointActionAdapter.browse_mode`
   default `passthrough` → `external` so API-class adapters stop inheriting proxy Browse by accident.
4. **Endpoint Profile** — `EndpointActionAdapter.profile()` exposes `actions[]`, `panels[]`, `browse_mode`.
   Panels derive from `direct_event` bookmarks. **Not yet consumed by the view/template** (that is Phase 3).
5. **Backward compatibility** — legacy per-vendor rows keys (`invoices`/`contacts`/`sales`), `list_kind`, and the
   old private names (`_publish_list_*`, `_list_*_payload`) are kept as deprecated aliases for one release, so the
   current renderer and the pre-existing tests work unchanged.

### Completed (Phase 3 — UI convergence)

6. **One renderer** — new `static/admin/js/endpoint_table.js` (`window.PolySaaSTable`), column-driven.
   `resolveListKind()` and the three hardcoded table builders are gone from `endpoint_home.js`.
7. **XSS closed** — the HubSpot portlet page built table HTML from raw API keys and values and assigned it
   to `innerHTML`. It now calls the shared renderer, which escapes every value including header labels.
8. **Region reorder** — Identity → Bar → **Data** → Actions → Wiring. Data is the page body. Wiring is a
   `<details>` **collapsed by default**, so auto-provisioned producers no longer lead the page. Create chips
   moved into a collapsed `Create…` overflow.
9. **Defects fixed** — chip sizing (`flex: 0 0 176px; width: 176px` → `flex: 0 0 auto; width: auto;
   min-width: 176px`), the `Inv Invoices` icon+title concatenation (icon span dropped from chips), and the
   two ambiguous chips renamed `Dynamic service — API` / `Dynamic service — upload` (renamed rather than
   deleted: both routes still work).
10. **Contrast** — audited all 14 `#86efac` and the `#fbbf24`. **Only 2 were broken**
    (`.polysaas-consumer-list__meta`, `__fed`, on light panes) → `#15803d` / `#b45309`. The other 12 sit on
    `#111`/`#1a1a1a` in the orch bar and CallBackData panel, which are BINGO'd terminal-green; a blanket
    recolour would have damaged them. A test now locks both sides.
11. **Cache** — `endpoint_home.css?v=20260901-1`, `endpoint_home.js?v=20260901-1`, `endpoint_table.js?v=20260901-1`.

### Validation

- `dose.tests.test_endpoint_envelope` — **41 new tests** (envelope, publisher, Browse, profile, regions, portlet).
- Affected suites (9 modules): **88 passed, 0 failed**. The pre-existing tests still import the deprecated
  private names and now run through the new publisher — that is the behavior-preservation proof.
- All three changed templates compile via `get_template()`.
- Full `dose.tests` (`--keepdb`): 199 tests, 10 failures + 9 errors — **all pre-existing**. Verified by
  `git stash`-ing this session's changes and re-running the same four modules: byte-identical failure list
  (`test_tenant_membership`, `test_hubspot_session`, `test_polysniffer_locked_architecture`,
  `test_slack_native_sniff`). Not caused by this work; worth a separate look.

### Needs a human eye

The layout changed. Hard-refresh (Ctrl+F5) an endpoint home and confirm: Data sits directly under the orch
bar, Wiring is collapsed, chips are not clipped, and the CallBackData table still renders on click.

### Docs

- New: `documentation/POLYSAAS_ENDPOINT_WORKSPACE_MODEL.md`.
- `SUPERSEDED` headers added to `architecture/PolySaaS-Architecture.md`, `ASSET_LOADING_ARCHITECTURE.md`,
  `BINGO_POLYSNIFFER_2.0_PASSTHROUGH_IFRAME_2026-06-24.md`,
  `BINGO_MATTERMOST_SLUG_IDENTITY_SSO_WORKING_2026-08-02.md`. No history deleted.

### Deferred, do not action

The `AI_RULES.md` §3 vs `.cursor/rules/bak-before-edit.mdc` `.bak` contradiction stays **open**. This session
followed `.bak`. The 424 already-tracked `.bak` files were left alone and the rule file was not deleted.

---

## Previous session

- Date/session: **2026-08-31 — office chrome glass + Geronimo width**
- Branch: `cursor/polysniffer-slack-native-capture`
- Prior BINGO (still frozen unless owner unlocks):
  - `documentation/BINGO_SLACK_HUBSPOT_DUAL_FEED_2026-08-28.md` (`7d74bf55`)
  - `documentation/BINGO_SLACK_ODOO_FORMS_2026-08-25.md` (`b28be615`)
  - `documentation/BINGO_SLACK_PRODUCER_CONSUMER_2026-08-24.md` (`28b07da0`)
- Agent sync check: passed
- Tenant of record: **OLIENTR** / schema `olient`
- **Not a BINGO.** Visual chrome only. Stakeholder liked the chrome-framed glass chips.

## Completed this session (office)

1. **Chrome-framed royal-blue glass chips** — replaced clear translucent capsules with skeuomorphic chrome rim + glossy blue glass (white labels, top sheen). Create / bookmarks / Browse / Slack mock actions / Pair / pair-dialog use blue; **Run** uses the same chrome treatment in green.
2. **Geronimo full width** — inline dock no longer capped at 840px. Spans the content column with a chrome dividing bar on top. Pop-out mode unchanged.
3. Punched aluminum field, dark trays, header title, green orch bar + CallBackData panel **unchanged**.
4. Cache: `endpoint_home.css?v=20260831-1`. Tests: `dose.tests.test_endpoint_home` (12 passed).

## Files

- `dose/static/admin/css/endpoint_home.css` (+ `.bak`)
- `dose/templates/dose/endpoint_home.html` (+ `.bak`)
- `dose/tests/test_endpoint_home.py` (+ `.bak`)
- `dose/templates/admin/includes/polysaas_ai_chat_dock.html` (+ `.bak`)

## After pull

```powershell
git pull origin cursor/polysniffer-slack-native-capture
# hard-refresh endpoint homes: Ctrl+F5  (?v=20260831-1)
```

## Next

1. Stakeholder keep / tweak / BINGO the chrome if approved.
2. Still open from Canada BINGO: HubSpot deal backfill / bidirectional later; create-chip `role=` / `custom_endpoint=1` not wired in frozen `admin.py`.

## Leave alone

- Browse / orch READY / Pair-Run **behavior** (BINGO) unless unlocked — this pass only restyled chips and the Geronimo dock width.
- Do not invent Mattermost fillers.
- Do not restack the aluminum on multiple wrappers (causes overlapping holes).

## Commit exclusions

**Exclude:** Capital Raise, `polysniffer-auth.json`, evidence, `tmp/*`, `Lesson1.py`, `mona1.py`, leftover `custom_sidebar_head.html.bak` / jazzmin `index.html.bak`, `.env`.
