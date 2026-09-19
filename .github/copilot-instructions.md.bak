# Copilot Instructions for PolySaaS

Read and follow `AI_RULES.md` before every edit. Pay special attention to the
PolySniffer no-iframe rule and the PostgreSQL schema architecture rule.

## Always read first

Before editing or answering, read the current handoff and the active rules:

- `documentation/ACTIVE_HANDOFF.md`
- `AGENTS.md`
- `.cursor/rules/process-rules.mdc`
- `.cursor/rules/passthrough-no-iframes.mdc`
- `.windsurf/workflows/push.md`

## Required workflow

1. Read the latest handoff at startup.
2. Check the latest repo state and recent changes.
3. Validate the repo sync contract with `python scripts/check_agent_sync.py`.
4. Ask before editing anything that may be active or recently modified.
5. Prefer the current approved architecture and prior documented fixes.
6. For end-of-day work, update the handoff before the final commit.

## Protection rules

- No iframe-based passthrough by default.
- Keep the architecture and rules aligned across Copilot, Cursor, and Windsurf.
- Do not silently diverge from the documented project process.
- Do not leave a session without a handoff summary and clear next steps.

## EOD requirement

Every end-of-day commit must include a handoff update in `documentation/ACTIVE_HANDOFF.md`.

`documentation/ACTIVE_HANDOFF.md` is the only active handoff. Never create a
dated or task-specific handoff file; Git history preserves prior states.

Commit all worktree WIP, including unfinished work and the updated handoff,
then push the active branch so another machine can resume from the same state.
Never omit WIP merely because it is incomplete; label incomplete or
unvalidated work clearly in the handoff and commit message.

If local WIP makes a pull unsafe, fetch first, compare local and remote tips,
checkpoint all WIP, and then integrate the remote work. Never discard or
overwrite WIP to force synchronization.
