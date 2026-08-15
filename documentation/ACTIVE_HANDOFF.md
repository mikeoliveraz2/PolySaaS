# PolySaaS Active Handoff

This file is the canonical startup and end-of-day handoff for the repo.

Every agent — Copilot, Cursor, and Windsurf — must read this file at the start of every session.

## Status

- Date: 2026-08-15
- Branch: `cursor/polysniffer-switch-object-to-iframe`
- Repo state: `origin/main` commit `36048d89` merged locally in `ea4b7fc9`
- Latest validated handoff: this file
- Policy: end-of-day work requires a handoff update before the final commit is considered complete

## Last session summary

- Fetched and read the shared workflow commit `36048d89` from `origin/main`.
- Read `ACTIVE_HANDOFF.md`, `AGENTS.md`, Cursor rules, Windsurf workflow, and Copilot instructions before integration.
- Preserved all office-machine changes in WIP checkpoint `434ef226`: 55 files, including unfinished source, tests, `.bak` files, temporary probes, and capital-raise artifacts.
- Merged `origin/main` into the feature branch as `ea4b7fc9`.
- Resolved the sole merge conflict in `.github/copilot-instructions.md` by keeping the shared cross-agent contract and the stronger all-WIP preservation rule.
- Retired the dated Slack handoff. This file is the only active handoff.

## Critical local facts to record before EOD

Every session must capture the facts that are only available on the current machine, especially when the work is not yet committed or pushed:

- endpoint URL and hostname under test
- tenant / schema / user context
- browser or local-session state that affects the route
- the exact failing symptom or last working state
- what is still uncommitted or local-only
- what must be reproduced on the other machine before continuing

Example for Slack/HubSpot work:

- endpoint URL under test
- tenant membership / active tenant
- working vs failing path
- current admin or browser login context
- whether the result was proven in the browser or only server-side
- whether a follow-up requires the office machine or laptop machine

## Current priorities

- Maintain rule synchronization across Copilot, Cursor, and Windsurf.
- Keep the handoff current and reviewable at startup.
- Continue to prefer proxy/rewrite passthrough patterns over iframes.
- Keep both machines synchronized at the worktree/repo level instead of recreating local-only state.
- Apply the locked trigger-delivery model: passthrough observes direct HTTP triggers; webhooks deliver externally observed UI/API triggers; outbound APIs run from existing Instructions; all results can surface on the orchestration bar.
- Live-validate the completed Slack `/poly` webhook slice against the configured tenant RabbitMQ and Slack app.
- Treat `documentation/architecture/SLACK_WEBHOOK_ORCHESTRATION_DESIGN.md` as the formal design specification for the Slack webhook slice.

## Locked orchestration trigger model

- Every orchestration requires a user or system trigger.
- Passthrough receives a direct action-path trigger observed on proxied HTTP traffic.
- A webhook is a delivery pipe for a trigger that occurred in another system's UI or API; it is not spontaneous.
- An outbound API call is made by an already-running Instruction and returns its result.
- The orchestration bar displays progress and results for all modes.
- Instruction matching remains `(action_path, method, direction)`. For webhook/API mode, `action_path` may be a normalized logical event key rather than a browser URL.

## Current blockers

- Slack Native is validated through a real top-level Chromium browser. The old `<object>` approach delivered one HTTP 200 document but Slack produced no follow-up requests because its client bootstrap cannot run under the PolySaaS object origin.
- The WIP checkpoint includes unfinished and unvalidated changes across PolySniffer, Nextcloud, Odoo services/tests, startup scripts, backup files, and probes.
- The Slack webhook slice is unit-tested but has not received a signed request from a real Slack workspace or published through the live RabbitMQ configuration.

## Next actions

- Pull this feature branch on the next machine and run `python scripts/check_agent_sync.py`.
- Create or verify one Instruction with the exact triple `/events/slack/command/poly` + `POST` + `REQ` and the intended atomic service.
- Confirm the tenant Slack `TenantApp.extra_config` has `slack_team_id` and `signing_secret`, and that the tenant has an active RabbitMQ `MQConfig`.
- Send a real `/poly` command and verify fast ephemeral ack, one consumer execution, `CallBackData`, and tenant-visible `DoseMessage` feedback.
- Trace the active Admin PolySniffer endpoint-row action through workspace launch and session identity.
- Use Start Native to launch the persistent Chromium profile, interact with Slack in that browser, monitor requests in Live capture, then click Stop capture or close Chromium to finalize the HAR.
- Review the broad checkpoint commit before promoting any unfinished WIP as completed behavior.

## Session summary for this EOD

- Synchronized the office-machine feature branch with the laptop's `origin/main` workflow commit.
- Committed every local tracked and untracked file before merging; no WIP was omitted.
- Consolidated handoff ownership into this canonical file and removed the dated Slack handoff.
- Kept incomplete work clearly labeled instead of claiming behavior validation.
- Locked and documented the shared orchestration trigger-delivery model in `AI_RULES.md` and this handoff.
- Implemented the approved Slack-only webhook slice: signature verification and team mapping, canonical trigger envelope, RabbitMQ publication before fast ack, exact Instruction matching, atomic execution, durable per-tenant event dedup, `CallBackData`, and tenant-visible `DoseMessage` feedback.
- Routed trigger envelopes through the existing MQ monitor while leaving legacy `/mq/` processing and `generic_inbound_webhook` unchanged.
- Added `pika==1.3.2` to the primary requirements and installed it in the active venv.
- Added the formal Slack webhook architecture specification at `documentation/architecture/SLACK_WEBHOOK_ORCHESTRATION_DESIGN.md`.
- Replaced the ambiguous endpoint-ID Native pane launch with a schema-qualified, host-identified route under `/admin/polysniffer/sniff/<host>/native/`.
- Kept configured endpoint paths exact, retained same-origin redirects inside Native capture, and prevented internal `schema`/`ps_sniff` parameters from leaking upstream.
- Corrected `polysaasonline` endpoint 6 from Slack's obsolete `/sign_in` URL to `https://polysaasworkspace.slack.com` with starting path `/`.
- Replaced the blank Slack `<object>` Native flow with an asynchronous headed Chromium session on Slack's real origin.
- Added a persistent per-tenant/host Chromium profile, full HAR recording, live Playwright response snapshots into tenant `TrafficLog`, and Stop capture signaling.
- Kept Passthrough in the workspace pane; only Native launches the real browser required for upstream origin, cookies, scripts, and API traffic.

## Validation

- Ran: `d:\PolySaaS\venv\Scripts\python.exe d:\PolySaaS\scripts\check_agent_sync.py`
- Result: `Agent sync validation passed: repo policy files are aligned.`
- Exit code: `0`
- Checked shared policy files for unresolved merge markers: none found.
- Product behavior tests were not run for checkpoint `434ef226`; it is explicitly unvalidated WIP.
- Slack webhook and adjacent atomic-selector tests: `20/20` passed.
- Editor diagnostics: no errors in the new webhook module, Slack view, MQ monitor, tests, or requirements file.
- Runtime dependency check: `pika 1.3.2` imports successfully.
- Live Slack and RabbitMQ end-to-end validation: not run.
- Slack Native and PolySniffer architecture tests: final suite `27/27` passed.
- Django system check: passed with no issues.
- Real Slack Native capture 34: `60` responses across `30` distinct paths, including HTTP 200 from `POST /api/signin.findWorkspaces`.
- Normal `runall.ps1` stack restarted successfully on port 8000 with the real-browser capture implementation.

## Blockers / risks

- Native Chromium profiles and HAR files are local runtime artifacts under `MEDIA_ROOT/polysniffer/native`; protect them because they can contain authenticated browser data.
- `media/polysniffer/` is intentionally gitignored and must never be included under the all-WIP commit rule.
- The checkpoint intentionally includes `.bak`, temporary, generated, and potentially incomplete files under the full-WIP synchronization rule.
- Do not delete or rewrite checkpointed WIP without reviewing its purpose first.
- The existing RabbitMQ adapter acknowledges a consumed message before dispatcher execution; a worker crash after consume could lose that delivery. This pre-existing adapter behavior was not expanded in the locked slice and should be reviewed before production hardening.

## Next session

- Read this handoff first on startup.
- Run `python scripts/check_agent_sync.py` before making edits.
- Pull `cursor/polysniffer-switch-object-to-iframe` and resume from the pushed repo state.
- Continue from the validated real-browser Native flow; do not restore Slack to an embedded object/iframe.

## Commit info

- Branch: `cursor/polysniffer-switch-object-to-iframe`
- Main workflow commit integrated: `36048d89`
- Full WIP checkpoint: `434ef226`
- Merge commit: `ea4b7fc9`
- Trigger-delivery architecture rule: `37d47924`
- Slack webhook slice: `00ddd80a`
- Formal Slack webhook design: `99bd7b8f`
- Slack Native host-identity fix: `40a21d8c`
- Slack real-browser Native capture: pending commit
- Latest repo sync validation: passed
- Final push status: pending real-browser Native capture commit and push

## Handoff template

Use this structure for each end-of-day handoff:

### Session summary
- What was finished
- What remains uncertain
- What changed since last session

### Validation
- Tests or checks run
- Results
- Any follow-up required

### Blockers / risks
- Known blockers
- Open risks
- Questions needing user decision

### Next session
- Specific next actions
- Files to review
- Pending branch/commit status

### Commit info
- Branch
- Latest commit hash
- Final push status

---

This is the current handoff-of-record for PolySaaS. Read it before continuing work.
