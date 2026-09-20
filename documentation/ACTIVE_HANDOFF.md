# Active Handoff

This file is the canonical startup and end-of-day handoff.
Every agent must read this file before editing or answering.

**Date:** 2026-09-20 (Sunday)
**Session:** Mailbox records visible — open the right row
**Branch:** main

## Status
Live dump proves capture works:
- Rows with `product.template/web_search_read` have **records=10** (real inventory).
- Rows with `/odoo/action-384` are navigate-only (**records=None**) — ignore those.
- SEED row has records=3.

Admin now returns **plain text** published records (no HTML) so Jazzmin shows them.
List Payload column labels navigate rows as `no records (navigate only)`.

## Next
Rebuild → open mailbox row whose Payload says `10 record(s)` or `3 record(s)`,
NOT `no records (navigate only)`.
