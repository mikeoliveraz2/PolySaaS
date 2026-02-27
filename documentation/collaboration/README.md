# Laptop ↔ Desktop coordination

Notes between **Laptop Cursor** and **Desktop Claude** for PolySaaS (canonical repo: `mikeoliveraz2/PolySaaS`).

---

## How to use

- **Desktop:** Add or edit a note here (e.g. `notes-from-desktop.md`) when you leave work for the laptop.
- **Laptop:** Read the latest note, add a reply or `notes-from-laptop.md` when you hand back to desktop.

---

## Current status (laptop – 2026-02-25)

- Laptop was offline; desktop has been committing. **First priority: pull latest.**
- Laptop had local changes (e.g. `go.ps1`, `dbgo.ps1`, `gol.ps1`, 5433 defaults) — those were **stashed** earlier with message:  
  `laptop: go/dbgo/gol.ps1 5433 env docker docs config + staging images`
- Pull was attempted but **blocked by `.git/index.lock`** (another git/editor process using the repo).
- **Action for you (laptop):**  
  1. Close any other app using `F:\PolySaaS` (other Cursor/VS Code windows, Git UI, etc.).  
  2. Delete lock if it’s still there:  
     `Remove-Item "F:\PolySaaS\.git\index.lock" -Force -ErrorAction SilentlyContinue`  
  3. Pull:  
     `cd F:\PolySaaS; git restore .; git pull origin main`  
  4. Reapply laptop changes if desired:  
     `git stash list` then `git stash pop` (resolve conflicts if any).

---

*Last updated: 2026-02-25 (laptop).*
