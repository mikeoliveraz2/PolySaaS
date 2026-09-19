---
description: PolySaaS startup and end-of-day sync workflow for Copilot, Cursor, and Windsurf
alwaysApply: true
---

# PolySaaS Sync Workflow

## Startup checks (read before work)

At the beginning of every session, each agent must read in order:

1. `documentation/ACTIVE_HANDOFF.md`
2. `AGENTS.md`
3. `.cursor/rules/process-rules.mdc`
4. `.cursor/rules/passthrough-no-iframes.mdc`
5. `.windsurf/workflows/push.md`
6. `.github/copilot-instructions.md` if present

This ensures all tools are aligned to the current repo state and handoff.

## EOD requirement

At the end of each workday:

1. Update `documentation/ACTIVE_HANDOFF.md` with the final summary.
2. Confirm the repo state and any recent edits.
3. Run `python scripts/check_agent_sync.py`.
4. Stage and commit the work.
5. Push the branch if appropriate.
6. Leave a clear next-step summary for the next session.

No end-of-day commit is considered complete without a fresh handoff update and a passing repo sync check.

## Mandatory startup validation

Before doing any work, read the handoff and then run:

- `python scripts/check_agent_sync.py`

This keeps Copilot, Cursor, and Windsurf synchronized with the same content and process on both machines.

## Process rules

- Pull before continuing work whenever appropriate.
- Never silently diverge from the repo’s documented rules.
- No iframe-based passthrough by default.
- Ask before editing areas that may be active or recently modified.
- Keep Copilot, Cursor, and Windsurf synchronized on the same handoff and rules.

