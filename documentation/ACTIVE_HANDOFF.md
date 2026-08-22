# PolySaaS Active Handoff

This file is the canonical startup and end-of-day handoff for the repo.
Every agent — Copilot, Cursor, and Windsurf — must read it before work.

## Status

- Date/session: 2026-08-22 EOD, Slack wireframe → live Odoo orchestration
- Branch: `cursor/polysniffer-slack-native-capture`
- Sync: pulled `origin/main`; merge recorded as `fcb6f73b`; source merged cleanly
- Commit status: final Slack wireframe/Odoo EOD commit follows this handoff update, then push to the tracked remote branch
- Agent sync check: passed at session startup
- Server: Waitress restarted after implementation; mailbox consumer started with 1-second polling
- Policy: Slack demo panes are PolySaaS HTML. Do not load `app.slack.com`, add a Slack iframe, or create a PolySaaS `/auth` workaround.

## Owner-approved delivery order

1. Three stable Slack wireframe surfaces
2. Real contact webhook + Odoo consumer
3. Real sale webhook + draft-quotation consumer
4. Messaging
5. Visual polish to resemble Slack

The first three items are complete. Messaging is next; visual polish remains deliberately last.

## Completed this session

### Three deterministic Slack surfaces

- PolySniffer Native: fake Slack discovery page, no orchestration bar.
- PolySniffer Passthrough: the same shell plus the green orchestration bar.
- Sidebar Passthrough: the same PolySaaS workspace, not a live Slack proxy.
- Slack-specific handler hooks own the behavior; shared passthrough layers remain app-neutral.
- Wireframe JavaScript was moved to a static file because inline script execution was blocked by admin CSP.

### Real contact webhook and consumer

- Wireframe action: `/events/slack/webhook/contact` (`POST`, `REQ`).
- Authenticated, CSRF-protected local trigger queues a canonical `polysaas.trigger.v1` envelope.
- Tenant is derived from the authenticated request/session; it is never accepted from posted JSON.
- Tenant Instruction #4 binds the action to `OdooCreatePartner`.
- Live proof in tenant `polysaasonline`: Odoo partner #8 created by direct pipeline proof; browser click later created partner #11.

### Real quotation webhook and consumer

- Wireframe action: `/events/slack/webhook/sale` (`POST`, `REQ`).
- New `OdooCreateQuotation` atomic service creates an Odoo `sale.order` in `draft` state.
- Tenant Instruction #5 binds the action to `OdooCreateQuotation`.
- The standard Odoo Sales module (`sale_management`) was installed in `odoo_polysaasonline`; it had been uninstalled and `sale.order` did not exist.
- Live proof: quotation S00001 created by direct pipeline proof; browser click later created draft quotation S00002.
- Idempotency now scopes existing-quotation reuse by client reference + customer + draft state, preventing another customer's order from being updated.

### Browser behavior

- Both wireframe buttons now perform a real same-origin POST, receive mailbox ID, poll tenant-safe mailbox status, and display the Odoo result.
- Verified in the sidebar Slack wireframe:
  - `Odoo contact ready — partner #11`
  - `Odoo draft quotation S00002`

## Primary files changed

- `dose/passthrough/handlers/slack_handler.py`
- `dose/polysniffer/views/sniff_v2_workspace.py`
- `dose/templates/polysniffer/sniff_workspace.html`
- `dose/templates/polysniffer/slack_wireframe.html`
- `dose/templates/admin/passthrough_embed.html`
- `dose/static/admin/js/slack_wireframe.js`
- `dose/views/slack_wireframe_webhook.py`
- `dose/webhook_events.py`
- `dose/urls.py`
- `dose/services/odoo_create_quotation.py`
- `dose/management/commands/setup_slack_wireframe_consumers.py`
- Slack/Odoo tests and required adjacent `.bak` files

The pull from `origin/main` also brought its existing stray-root relay and diagnostic work. Those merged source files were not rewritten during this session.

## Validation

- Final merged-tree suite: 40 focused Slack mailbox, wireframe, webhook, Odoo partner, and quotation tests passed.
- `python manage.py check`: no issues.
- IDE lint diagnostics: no errors in changed files.
- Live mailbox results: both actions `processed`, each matched exactly one Instruction, each atomic result returned `status=success`.
- Live Odoo readback confirmed partner #8 and draft quotation S00001; browser action confirmation produced partner #11 and S00002.
- Waitress restarted successfully on port 8000.

## Blockers / risks

- Messaging feedback exposes an existing schema defect: creating `DoseMessage` in `polysaasonline` fails because tenant-table FK `dose_dosemessage.user_id` references a tenant `auth_user` row that does not contain public user id 143. Atomic execution and mailbox completion still succeed. Resolve this tenant-safe user/message relationship before relying on messaging or toast feedback.
- `Instruction.pub_date` and `CallBackData.pub_date` still emit naive-datetime warnings. They do not block the pipeline but should be corrected deliberately.
- The first fixed-reference quotation proof was correctly deduplicated by `RequestLog`; unique browser/demo IDs avoid replay collisions.

## Next actions

1. Design and implement tenant-safe message feedback without moving tenant-owned data into `public`.
2. Add the Slack wireframe message composer and render consumer replies/results as messages.
3. Re-run contact and quotation actions through messaging and verify Odoo readback.
4. Only after messaging works, polish the wireframe to more closely resemble Slack.
5. Keep Native, PolySniffer Passthrough, and Sidebar Passthrough behavior separate and preserve the no-iframe/no-live-Slack decision.

## Commit scope / exclusions

Include the Slack wireframe, webhook, consumer, Odoo quotation, tests, handoff, and their `.bak` files. Exclude generated `__pycache__`/`.pyc`, local terminal output, and unrelated sanitized HAR diagnostics.
