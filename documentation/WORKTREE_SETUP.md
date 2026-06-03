# PolySaaS Git Worktree (laptop + office)

## Layout

| Checkout | Path (laptop) | Branch | Role |
|----------|---------------|--------|------|
| **Main** | `F:\PolySaaS` | `main` | Pull, EOD `.env.enc`, BINGO merges land here |
| **WIP worktree** | `F:\PolySaaS-worktrees\wip` | `wip` | Daily edits; `go.ps1` runs Django here |

Office uses the same pattern; set `.worktree-path` locally (gitignored) to that machine's worktree directory.

## Laptop setup (done 2026-06-03)

```powershell
git worktree add F:\PolySaaS-worktrees\wip -b wip main
```

`.worktree-path` in repo root (gitignored):

```
F:\PolySaaS-worktrees\wip
```

Shared venv stays on main checkout (`F:\PolySaaS\venv`). After `go.ps1` decrypts `.env` on main, it copies `.env` and `.env.key` into the worktree.

## Daily use

- **Start:** `.\go.ps1` — pull, decrypt env, sync env to worktree, runserver from worktree.
- **Work:** Edit code in `F:\PolySaaS-worktrees\wip` (or open that folder in the IDE).
- **End:** `.\EOD.ps1` from **main** checkout — encrypt `.env`, commit/push WIP (including `.env.enc`).

## BINGO (planned)

When a feature is verified:

1. Commit/freeze BINGO in worktree (branch `wip`).
2. Merge `wip` into `main` on main checkout, push.
3. Remove old worktree; `git worktree add ... -b wip main` for a fresh WIP tree.

Post-BINGO experiments stay on `wip` only — rollback = reset `wip` without touching `main`.

## Commands

```powershell
git worktree list
git -C F:\PolySaaS-worktrees\wip status
git -C F:\PolySaaS-worktrees\wip add -A
git -C F:\PolySaaS-worktrees\wip commit -m "WIP: ..."
```

Or `cd F:\PolySaaS-worktrees\wip` and use git normally.
