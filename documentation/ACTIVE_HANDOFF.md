# Active Handoff

This file is the canonical startup and end-of-day handoff.
Every agent must read this file before editing or answering.

**Date:** 2026-09-21 (Monday)
**Session:** Stripe webhook 404 fix + topic/mailbox architecture alignment
**Branch:** main

## Done
- Wired `stripe_webhook` back at `/dose/webhook/stripe/` (was missing from urls → Stripe 404s).
- Earlier: SNMP Type2/Type1 demo pipe + week feeds (see prior handoff notes).
- Architecture alignment: topic = typed temp queue; consumer drains to reporting table;
  shared WebhookMailbox dump is not the long-term shape.

## Next
1. Deploy Django on Hostinger so `/dose/webhook/stripe/` is live.
2. Stripe Dashboard: endpoint URL =
   `https://app.prod-polysaas.cloud/dose/webhook/stripe/`
3. Confirm `STRIPE_WEBHOOK_SECRET` on Hostinger; redeliver failed events.
4. Topic-first Admin + consumer drain (when go) — SNMP or inventory first.

## Do not
- Put tenant-owned rows in `public`.
- Treat WebhookMailbox as permanent mixed storage for all sources.
