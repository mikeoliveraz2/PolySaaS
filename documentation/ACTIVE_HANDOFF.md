# PolySaaS Active Handoff

This file is the canonical startup and end-of-day handoff for the repo.
Every agent — Copilot, Cursor, and Windsurf — must read it before work.

## Status

- Date/session: **2026-08-27 — Canada laptop → office review**
- Branch: `cursor/polysniffer-slack-native-capture`
- Prior BINGO certs (still frozen unless owner unlocks):
  - `documentation/BINGO_SLACK_ODOO_FORMS_2026-08-25.md` (`b28be615`)
  - `documentation/BINGO_SLACK_PRODUCER_CONSUMER_2026-08-24.md` (`28b07da0`)
- Agent sync check: passed
- Tenant of record: **OLIENTR** / schema `olient` (Odoo db `odoo_olient`)
- Not a BINGO commit

## Completed this session

1. **Odoo Invoices bookmark** — CallBackData + panel under green orch bar (`?v=20260827-4` / panel CSS).
2. **Sample data** — `python manage.py seed_odoo_sample_data olient` (Big Guys Wharehouse, customers, invoices).
3. **Slack channel wireframe visible again** on Slack endpoint home — in-channel **New contact** / **New sale** (`endpoint_home.css` / template `?v=20260827-5`). Browse Slack remains real Slack (no CRM forms there).
4. **Plan drafted (not executed):** Slack → Odoo + HubSpot dual-feed (Big Guys Warehouse). Gate = HubSpot write proof. Shela to confirm Private App vs OAuth write scopes. Cursor plan: `slack_hubspot_dual_feed`.

## Office after pull

```powershell
git pull origin cursor/polysniffer-slack-native-capture
.\runall.ps1
python manage.py seed_odoo_sample_data olient
```

Hard-refresh Slack + Odoo homes (`?v=20260827-5`).

## Next (office + Shela)

1. Review HubSpot dual-feed plan — **go/no-go after write proof only**.
2. Shela: HubSpot portal + Private App token vs OAuth reconnect for `contacts.write` (+ `deals.write` if sale).
3. Confirm Slack home shows channel mock with New contact / New sale.
4. Confirm Odoo Invoices bookmark + seed data after `seed_odoo_sample_data`.

## Leave alone

- Browse / orch READY / Pair-Run BINGO-frozen unless unlocked.
- Do not invent Mattermost fillers; do not HubSpot-home redesign until gate is green.

## Commit exclusions

**Exclude:** Capital Raise assets, `polysniffer-auth.json`, evidence, `tmp/_probe_*`, unused SVG drafts.
