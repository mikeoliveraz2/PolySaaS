<!-- THIS CODE IS FROZEN — NO CHANGES TO THIS CODE ARE ALLOWED WITHOUT THE OWNER'S PERMISSION -->
<!-- BINGO: Slack → Odoo + HubSpot dual-feed — 2026-08-28 -->

# BINGO — Slack → Odoo + HubSpot dual-feed (contacts & sales) — 2026-08-28

## Certified (live olient)

- Slack **New contact** → `OdooCreatePartner` **and** `HubSpotCreateContact` (mailbox runs both Instructions on the same path).
- Slack **New sale** → `OdooCreateQuotation` **and** `HubSpotCreateDeal`.
- Proven live: Contact Moon in Odoo + HubSpot; sale **Last try — Moon Rocks** as Odoo `S00004` + HubSpot deal.
- Odoo home bookmarks: **Contacts**, **Sales**, **Invoices** → CallBackData panel (`odoo.list_*`).
- HubSpot home bookmarks: **Contacts**, **Sales** → CallBackData panel (`hubspot.list_*`).
- Slack sale form collects **Amount** + **HubSpot stage** for deal write.
- HubSpot Private App token via `HUBSPOT_PRIVATE_APP_TOKEN` in `.env` (hydrates `TenantApp.extra_config`; never commit `.env`).
- `customer_rank=1` on Slack→Odoo partner create so Contacts bookmark shows new customers.

## Seed / ops

```powershell
python manage.py setup_slack_hubspot_consumers --schema olient
# Token: set HUBSPOT_PRIVATE_APP_TOKEN in .env (scopes: contacts.write + deals.write), then .\runall.ps1
```

## Explicitly not this bingo

- HubSpot ↔ Odoo bidirectional sync.
- HubSpot home redesign / Companies object.
- Changing Producer/consumer Pair-Run BINGO UX (`28b07da0`).

## Validation

- `python scripts/check_agent_sync.py` — passed
- `python manage.py test dose.tests.test_hubspot_slack_dual_feed dose.tests.test_odoo_list_contacts dose.tests.test_odoo_list_sales dose.tests.test_odoo_list_invoices dose.tests.test_slack_wireframe_webhooks` — OK
- Browser: dual-feed contact + sale; Odoo and HubSpot list bookmarks

## Commit

- Branch: `cursor/polysniffer-slack-native-capture`
- Hash: _(filled after commit)_
- Date: 2026-08-28

## Frozen source files (this bingo)

See `git show --name-only <hash>` — every source file in the commit carries the freeze banner.
