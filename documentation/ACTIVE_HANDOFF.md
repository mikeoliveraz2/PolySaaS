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

## Locked orchestration trigger model

- Every orchestration requires a user or system trigger.
- Passthrough receives a direct action-path trigger observed on proxied HTTP traffic.
- A webhook is a delivery pipe for a trigger that occurred in another system's UI or API; it is not spontaneous.
- An outbound API call is made by an already-running Instruction and returns its result.
- The orchestration bar displays progress and results for all modes.
- Instruction matching remains `(action_path, method, direction)`. For webhook/API mode, `action_path` may be a normalized logical event key rather than a browser URL.

## Current blockers

- Slack native sniff remains unvalidated end to end.
- A staff-side request to `/dose/sniff/6/native/sign_in` returned HTTP 404 because endpoint ID 6 in active schema `t104` resolved to Dolibarr, not Slack.
- The Slack WIP uses endpoint-ID `/dose/sniff/` routing and response rewriting, while the earlier PolySniffer architecture handoff documented host-identified Admin-only raw Native capture. Resolve this architecture mismatch before treating the 404 as only an endpoint-row problem.
- The WIP checkpoint includes unfinished and unvalidated changes across PolySniffer, Nextcloud, Odoo services/tests, startup scripts, backup files, and probes.

## Next actions

- Pull this feature branch on the next machine and run `python scripts/check_agent_sync.py`.
- Trace the active Admin PolySniffer endpoint-row action through workspace launch and session identity.
- Decide whether the Slack native capture must be adapted to host-identified Admin-only raw Native capture or whether the owner explicitly supersedes that architecture.
- Validate the exact Slack endpoint host in the correct tenant schema before editing production code.
- Review the broad checkpoint commit before promoting any unfinished WIP as completed behavior.

## Session summary for this EOD

- Synchronized the office-machine feature branch with the laptop's `origin/main` workflow commit.
- Committed every local tracked and untracked file before merging; no WIP was omitted.
- Consolidated handoff ownership into this canonical file and removed the dated Slack handoff.
- Kept incomplete work clearly labeled instead of claiming behavior validation.
- Locked and documented the shared orchestration trigger-delivery model in `AI_RULES.md` and this handoff.

## Validation

- Ran: `d:\PolySaaS\venv\Scripts\python.exe d:\PolySaaS\scripts\check_agent_sync.py`
- Result: `Agent sync validation passed: repo policy files are aligned.`
- Exit code: `0`
- Checked shared policy files for unresolved merge markers: none found.
- Product behavior tests were not run for checkpoint `434ef226`; it is explicitly unvalidated WIP.

## Blockers / risks

- Slack endpoint/tenant identity and the current PolySniffer architecture conflict remain unresolved.
- The checkpoint intentionally includes `.bak`, temporary, generated, and potentially incomplete files under the full-WIP synchronization rule.
- Do not delete or rewrite checkpointed WIP without reviewing its purpose first.

## Next session

- Read this handoff first on startup.
- Run `python scripts/check_agent_sync.py` before making edits.
- Pull `cursor/polysniffer-switch-object-to-iframe` and resume from the pushed repo state.
- Start with the Admin host-identity trace described under Next actions.

## Commit info

- Branch: `cursor/polysniffer-switch-object-to-iframe`
- Main workflow commit integrated: `36048d89`
- Full WIP checkpoint: `434ef226`
- Merge commit: `ea4b7fc9`
- Trigger-delivery architecture rule: included in the next commit after `4b5e8f19`
- Latest repo sync validation: passed
- Final push status: pending trigger-rule commit and push

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
