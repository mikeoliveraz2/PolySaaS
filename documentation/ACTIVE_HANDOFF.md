<!-- THIS CODE IS FROZEN — NO CHANGES TO THIS CODE ARE ALLOWED WITHOUT THE OWNER'S PERMISSION -->
<!-- BINGO: Slack → Odoo + HubSpot dual-feed — 2026-08-28 -->

# PolySaaS Active Handoff

This file is the canonical startup and end-of-day handoff for the repo.
Every agent — Copilot, Cursor, and Windsurf — must read it before work.

## Status

- Date/session: **2026-08-28 — Canada laptop BINGO → office**
- Branch: `cursor/polysniffer-slack-native-capture`
- **BINGO:** Slack → Odoo + HubSpot dual-feed (`documentation/BINGO_SLACK_HUBSPOT_DUAL_FEED_2026-08-28.md`)
- Prior BINGO certs (still frozen):
  - `documentation/BINGO_SLACK_ODOO_FORMS_2026-08-25.md` (`b28be615`)
  - `documentation/BINGO_SLACK_PRODUCER_CONSUMER_2026-08-24.md` (`28b07da0`)
- Agent sync check: passed
- Tenant of record: **OLIENTR** / schema `olient`
- Not leaving WIP unpushed

## Completed this session (BINGO)

1. Odoo list bookmarks: Contacts / Sales / Invoices → CallBackData panel.
2. HubSpot dual-feed consumers: `HubSpotCreateContact` + `HubSpotCreateDeal` on Slack paths (alongside Odoo).
3. HubSpot list bookmarks: Contacts / Sales.
4. Env hydrate: `HUBSPOT_PRIVATE_APP_TOKEN` → TenantApp (requires `contacts.write` + `deals.write`).
5. Slack sale form: Amount + HubSpot stage fields.
6. Odoo partner `customer_rank=1` so Contacts bookmark shows Slack-created customers.
7. Live proof: Contact Moon both systems; Moon Rocks sale Odoo S00004 + HubSpot deal.

## Office after pull

```powershell
git pull origin cursor/polysniffer-slack-native-capture
.\runall.ps1
python manage.py setup_slack_hubspot_consumers --schema olient
# Ensure .env has HUBSPOT_PRIVATE_APP_TOKEN (write scopes); never commit .env
```

Hard-refresh endpoint homes (`?v=20260828-1`).

## Next

1. Optional: backfill older HubSpot deals display / associations.
2. Later (not this bingo): HubSpot ↔ Odoo bidirectional.
3. Do not edit BINGO-frozen files without owner unlock.

## Leave alone

- Browse / orch READY / Pair-Run prior BINGOs unless unlocked.
- Do not invent Mattermost fillers.

## Commit exclusions

**Exclude:** Capital Raise assets, `polysniffer-auth.json`, evidence, `tmp/_probe_*`, `.env`.
