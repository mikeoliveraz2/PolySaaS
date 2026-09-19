# PolySaaS Agent Sync Rules

This file is the shared source of truth for Copilot, Cursor, and Windsurf.

## Startup sync: read first

At the start of every session, every agent must read these in order:

1. `documentation/ACTIVE_HANDOFF.md`
2. `AGENTS.md`
3. `.cursor/rules/process-rules.mdc`
4. `.cursor/rules/passthrough-no-iframes.mdc`
5. `.windsurf/workflows/push.md`
6. `.github/copilot-instructions.md` (if present)

If the handoff is missing, stale, or not clearly recent, stop and create a new handoff before continuing.

## EOD handoff rule

Every end-of-day commit must include a handoff update in `documentation/ACTIVE_HANDOFF.md`.

This is a repo-wide requirement, not an optional habit. The same rule applies to Copilot, Cursor, and Windsurf on both machines.

## Required startup validation

Before any code changes or answers, run/confirm this check:

- `python scripts/check_agent_sync.py`

If it fails, stop and fix the repo-level rule files before continuing.

Required fields:

- date and session
- what was completed
- what changed in code/docs
- current status of tests or validation
- blockers or risks
- next actions for the next session
- current branch and latest commit

No final end-of-day commit is considered complete unless the handoff is updated and committed with the same session work.

## Daily startup rule

Every startup must include reading the latest handoff and the current rules before making code changes, answering questions, or proposing edits.

This keeps Copilot, Cursor, and Windsurf synchronized on the same current state and avoids invalidating prior work.

## Project process rules

- No unilateral changes to working code without explicit approval.
- If a file appears recently changed, check recency before editing.
- No iframes by default in passthrough flows; use proxy/rewrite approaches first.
- UI & navigation: `documentation/POLYSAAS_UI_NAVIGATION_AND_EVENTS.md`.
- Orchestration: `documentation/POLYSAAS_ORCHESTRATION_MODEL.md`.
- Primary endpoint UI is mock + bookmarks; the real app opens in a top-level
  browser; Native/passthrough remain specialized tools.
- Pull before continuing work, then commit and push when changes are ready.
- Never leave finished work uncommitted or unpushed without explicit note.
- Use the repo’s freeze and backup rules as applicable.

## Handoff ownership

The latest handoff file is the handoff of record. If an agent sees conflicting evidence, the latest dated handoff wins until superseded by a new one.
