# Stripe on Render (PolySaaS Django)

## Environment variables (web service)

| Variable | Purpose |
|----------|---------|
| `STRIPE_SECRET_KEY` | Server-side API (subscribe flow, webhooks) |
| `STRIPE_PUBLISHABLE_KEY` | Browser / Elements (front-end) |
| `STRIPE_WEBHOOK_SECRET` | Verifies `Stripe-Signature` on webhook POSTs |
| `STRIPE_PRICE_ID` | Default price (fallback) |
| `STRIPE_PRICE_IDS` | Set in code (`settings.py`) or extend settings to read JSON from env |

## Webhook URL

**Production:** `https://<your-Render-domain>/dose/webhook/stripe/`

In **Stripe Dashboard → Developers → Webhooks → Add endpoint**, use that URL and select events you handle in `dose/views/stripe_webhook.py` (e.g. `customer.subscription.updated`, `customer.subscription.deleted`, `invoice.paid`, `invoice.payment_failed`).

Copy the **Signing secret** into `STRIPE_WEBHOOK_SECRET`.

## OpenAPI / Swagger

Subscription APIs live under DRF viewsets; the Django function view `stripe_webhook` is **not** auto-listed in drf-yasg. To document payment flows for integrators:

- Describe checkout/subscribe endpoints in **Swagger** descriptions on the relevant `ViewSet` / `@swagger_auto_schema`, and
- Link to this file or Stripe’s docs for **webhook** setup (external caller is Stripe, not your API consumer).

## Local testing

Use Stripe CLI: `stripe listen --forward-to localhost:8000/dose/webhook/stripe/` and set `STRIPE_WEBHOOK_SECRET` to the CLI signing secret.
