Read and follow the rules in `AI_RULES.md` before every edit. Pay special attention to the PolySniffer no-iframe rule and the PostgreSQL schema architecture rule.

## Daily multi-machine synchronization

- At the start of every workday, fetch/pull the active branch and read the canonical `HANDOFF.md` before making changes.
- If local WIP makes a pull unsafe, fetch first, compare local and remote branch tips, preserve the WIP, and report the blocker instead of discarding or overwriting work.
- `HANDOFF.md` is the only active handoff and the current source of truth. Never create a dated or task-specific handoff file; Git history preserves prior handoff states.
- If another handoff document exists, reconcile its current information into `HANDOFF.md` and retire the duplicate before implementation.
- At the end of every workday, update `HANDOFF.md` with completed work, current WIP, validation evidence, blockers, and the exact next step.
- Commit all worktree WIP, including unfinished work and the updated handoff, then push the active branch so another machine can resume from the same state.
- Never omit WIP from the daily synchronization merely because it is incomplete. Clearly label incomplete or unvalidated work in the handoff and commit message.
