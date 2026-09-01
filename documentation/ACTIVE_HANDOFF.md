<!-- THIS CODE IS FROZEN — NO CHANGES TO THIS CODE ARE ALLOWED WITHOUT THE OWNER'S PERMISSION -->
<!-- BINGO: Slack → Odoo + HubSpot dual-feed — 2026-08-28 -->

# PolySaaS Active Handoff

This file is the canonical startup and end-of-day handoff for the repo.
Every agent — Copilot, Cursor, and Windsurf — must read it before work.

## Status

- Date/session: **2026-09-01 — Unified Endpoint Workspace (Phases 1–3 complete)**
- Branch: `cursor/polysniffer-slack-native-capture`
- **Not a BINGO.** Awaiting stakeholder review of the new layout.
- Model doc: `documentation/POLYSAAS_ENDPOINT_WORKSPACE_MODEL.md` (new, authoritative)

### Unfreeze scope (owner-approved 2026-09-01, Michael + Shela + Gemini)

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
