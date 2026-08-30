<!-- THIS CODE IS FROZEN — NO CHANGES TO THIS CODE ARE ALLOWED WITHOUT THE OWNER'S PERMISSION -->
<!-- BINGO: Slack → Odoo + HubSpot dual-feed — 2026-08-28 -->

# PolySaaS Active Handoff

This file is the canonical startup and end-of-day handoff for the repo.
Every agent — Copilot, Cursor, and Windsurf — must read it before work.

## Status

- Date/session: **2026-08-30 — office chrome pass → stakeholder review**
- Branch: `cursor/polysniffer-slack-native-capture`
- Prior BINGO (still frozen unless owner unlocks):
  - `documentation/BINGO_SLACK_HUBSPOT_DUAL_FEED_2026-08-28.md` (`7d74bf55`)
  - `documentation/BINGO_SLACK_ODOO_FORMS_2026-08-25.md` (`b28be615`)
  - `documentation/BINGO_SLACK_PRODUCER_CONSUMER_2026-08-24.md` (`28b07da0`)
- Agent sync check: passed
- Tenant of record: **OLIENTR** / schema `olient`
- **Not a BINGO.** Visual chrome only. Michael is checking with stakeholder.

## Completed this session (office)

Shared endpoint-home chrome on Slack / Odoo / HubSpot / Mattermost (same template + CSS):

1. **Punched aluminum field** — one staggered hexagonal tile (`dose/static/admin/img/punched-aluminum.svg`), **one layer only** on `.dose-content-col` (no stacked/overlapping grids). Tile size `28×24`. Inner Jazzmin wrappers are transparent.
2. **Glass capsules** — clear pills (backdrop blur, end highlights, rim, drop shadow). Chip labels light on a **dark charcoal tray** so the glass reads. Browse / Pair keep a light blue wash.
3. **Smaller + uniform chips** — 32×176px buttons; tighter pane padding and 12px corners.
4. Header title stays next to the icon (dark text on a light header pane). Green orch bar + CallBackData panel **unchanged**.
5. Cache: `endpoint_home.css?v=20260830-7`. Tests: `dose.tests.test_endpoint_home` template assertion updated.

## Files

- `dose/templates/dose/endpoint_home.html` (+ `.bak`)
- `dose/static/admin/css/endpoint_home.css` (+ `.bak`)
- `dose/static/admin/img/punched-aluminum.svg` (+ `.bak`)
- `static/admin/img/punched-aluminum.svg` (STATICFILES_DIRS copy)
- `dose/tests/test_endpoint_home.py` (+ `.bak`)

## After pull

```powershell
git pull origin cursor/polysniffer-slack-native-capture
# hard-refresh endpoint homes: Ctrl+F5  (?v=20260830-7)
```

## Next

1. Stakeholder review of aluminum + glass chrome.
2. After review: keep, tweak, or BINGO the chrome if approved.
3. Still open from Canada BINGO: HubSpot deal backfill / bidirectional later; create-chip `role=` / `custom_endpoint=1` not wired in frozen `admin.py`.

## Leave alone

- Browse / orch READY / Pair-Run **behavior** (BINGO) unless unlocked — this pass only restyled glass chips, not pairing logic.
- Do not invent Mattermost fillers.
- Do not restack the aluminum on multiple wrappers (causes overlapping holes).

## Commit exclusions

**Exclude:** Capital Raise, `polysniffer-auth.json`, evidence, `tmp/*`, `Lesson1.py`, `mona1.py`, leftover `custom_sidebar_head.html.bak` / jazzmin `index.html.bak`, `.env`.
