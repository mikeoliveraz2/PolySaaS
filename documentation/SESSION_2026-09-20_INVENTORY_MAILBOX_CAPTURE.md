# Inventory → Webhook mailbox capture (verified 2026-09-20)

**Status:** Working on Hostinger (PolySaaS Online / `polysaas`)  
**Branch:** `main`  
**Verified by:** Michael — “Hooray!” after Published inventory records banner showed product rows

## What this proves

Passthrough Inventory list load captures the **same product rows Odoo uses to render the list**, writes them to `WebhookMailbox`, and Admin can browse them as a point-in-time history.

Flow:

```
User opens Odoo Inventory → Products (via /pt/admin/odoo/…)
  → POST …/call_kw/product.template/web_search_read
  → CapturePostResponse (Instruction, direction=RES)
  → normalize result.records
  → WebhookMailbox.envelope.payload.records[]
  → Admin list: “N record(s) — …”
  → Change form banner: Published inventory records table
```

## What was wrong before

| Symptom | Cause |
|--------|--------|
| Mailbox empty / FK errors | Shadow `dose_tenant` + Tenant FK on mailbox; fixed by dropping FK (schema isolation) |
| Navigate-only rows | Capture on `/odoo/action-384` has no list body |
| “Payload not useful” | Admin showed JSON / Jazzmin hid HTML; detail had no visible table |
| Truncation dropped rows | Large responses became `_preview` without `records[]` |

## Key commits (2026-09-20)

| Commit | Note |
|--------|------|
| `f3f3e2ff` | Drop `WebhookMailbox.tenant` FK |
| `a56e9a1a` | Restore `db_table = webhook_mailbox` |
| `612b236d` | `CapturePostResponse` + inventory Instruction paths |
| `502478b6` | Keep `records[]` on truncate; diagnose `--seed`/`--dump` |
| `90015500` | Change-form banner; click Payload column |

## Hostinger ops (already done for verify)

```bash
python manage.py migrate
python manage.py setup_odoo_inventory_capture --schema polysaas
python manage.py diagnose_webhook_mailbox --schema polysaas --seed
python manage.py diagnose_webhook_mailbox --schema polysaas --dump
```

Open Admin → Webhook mailboxes → click Payload **`N record(s) — …`** (not `get_response` / action-384).

## Demo tip

Ignore navigate rows (`/odoo/action-384`, Payload `get_response` / “navigate only”).  
Use `product.template/web_search_read` (or product.product / stock.quant) rows for the inventory snapshot story.

## Tomorrow — #2 (async pull)

Capture + browse (#1) is done. Next:

**Pull API** — subscribers fetch mailbox payloads by topic / mailbox id asynchronously until `expires_at` (claim optional), so “anyone signed up gets the data until TTL” is a real API, not only Admin.

Not started yet. Leave CapturePostResponse / Instructions as-is unless pull design needs status tweaks (`available` vs `processed`).
