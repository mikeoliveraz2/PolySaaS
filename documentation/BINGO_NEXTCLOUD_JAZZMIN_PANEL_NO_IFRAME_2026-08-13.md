<!-- THIS CODE IS FROZEN — NO CHANGES TO THIS CODE ARE ALLOWED WITHOUT THE OWNER'S PERMISSION -->
<!-- BINGO: Nextcloud in Jazzmin panel, no iframe — 2026-08-13 -->

# BINGO — Nextcloud in Jazzmin panel, no iframe

**Date:** 2026-08-13  
**Declared by:** Michael  
**Commit:** `49ddbb11`

---

## What this certifies

1. **No iframe passthrough.** Bundled apps load by HTML injection in `admin/display.html` or a top-level window. Leftover iframe shells were retired (stub only).
2. **Nextcloud in the Jazzmin panel.** Sidebar **Nextcloud** and PolySniffer **Start Passthrough** go to `/pt/admin/localhost:8888/apps/files/` in **this window** (Jazzmin chrome + injected Nextcloud HTML). SSO uses `TenantApp.extra_config` (`nc_login` / `nc_password`).
3. **Native sniff** still opens upstream in a separate top-level window (no iframe).

## Operator checklist

1. Restart Waitress (`.\runall.ps1` or equivalent) and hard-refresh.
2. Log in to PolySaaS admin (tenant `pso17`).
3. Sidebar → **PASSTHROUGH SERVICES** → **NextCloud** — Files should appear in the content panel, already signed in. No Nextcloud login form.
4. Or: PolySniffer workspace → **Start Passthrough** — same Jazzmin panel URL, same window.
5. Do **not** use Start Native if you want the panel; Native is raw `localhost:8888` (manual login, user `pso17` not `spo17`).

## Files (live behavior)

| File | Role |
|------|------|
| `dose/templates/polysniffer/sniff_workspace.html` | Passthrough = same-window Jazzmin; Native = new window; no iframe |
| `dose/passthrough/handlers/nextcloud_handler.py` | Display shell + SSO; PolySniffer prefix/SSO hooks |
| `dose/static/admin/js/orchestration_instruction_button.js` | Instruction form opens a new window (no modal iframe) |
| `dose/tests/test_polysniffer_architecture.py` | Shell is iframe-free; passthrough has no `target=_blank` |

Retired iframe templates (stubs only) are listed in git for this commit so they cannot be copied as the approved pattern.

## GOLD ZIP

`D:\BINGO ZIPS\BINGO_NEXTCLOUD_JAZZMIN_PANEL_NO_IFRAME_2026-08-13.zip`
