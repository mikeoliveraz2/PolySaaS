# Laptop ↔ Desktop coordination

Notes between **Laptop Cursor** and **Desktop Claude** for PolySaaS (canonical repo: `mikeoliveraz2/PolySaaS`).

---

## Two-machine sync (storage & workflow)

**Storage (as of 2026-02):**

| Machine   | Drive / storage              | PolySaaS path   | Notes                                      |
|-----------|------------------------------|-----------------|--------------------------------------------|
| **Laptop**  | D: internal SSD (512 GB partition) | `D:\PolySaaS`   | Healthy; daily backups go to `D:\backups`  |
| **Desktop** | Imation 1TB HD               | (your path)     | Stable, in use >1 year; CrystalDiskInfo OK  |

**Sync workflow (Rule 4):**

- **Before starting work (either machine):** `git pull origin main`
- **When done or before switching machines:** commit changes, then `git push origin main`
- **Morning:** run `.\go.ps1` — it does pull, daily backup (skip if same day), then starts services.

Source of truth is **GitHub**; no external clone drive needed. Develop from either place as long as you pull first and push when done.

---

## How to use

- **Desktop:** Add or edit a note here (e.g. `notes-from-desktop.md`) when you leave work for the laptop.
- **Laptop:** Read the latest note, add a reply or `notes-from-laptop.md` when you hand back to desktop.

---

## Current status (laptop – 2026-02-28)

- Laptop: PolySaaS on **D:\PolySaaS** (internal SSD, healthy). Branch `main` up to date with `origin/main`.
- Desktop: PolySaaS on **Imation 1TB** (stable). Pull from `origin/main` to match laptop; push when desktop has commits.
- Old external (fake Seagate) no longer used; sync is laptop ↔ desktop via GitHub only.

---

*Last updated: 2026-02-28 (laptop).*
