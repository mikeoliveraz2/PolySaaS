# Pricing consistency — staging (source of truth for this pass)

Align WordPress marketing with subscribe/product behavior:

| Item | Canonical |
|------|-----------|
| Plan names | **Starter** ($29) · **Team** ($49) · **Unlimited** ($99) · **Founders Beta** ($10/mo × 6) |
| Volume discounts | Users **2–10** → 10% · **11–20** → 20% · **21+** → 30% (was wrongly 31+) |
| App slots | WordPress & PolySysMon count as **2** slots each (matches `PLAN_BUNDLED_APP_SLOTS`) |
| External BYOL | Consumes plan slots; bring-your-own-license. Not a separate “+$10/mo” product fee on Unlimited. |
| Unlimited | Unlimited application slots (bundled + external BYOL) — not “all externals free” while also saying +$10/ea |

Note: Django `PLAN_PRICES['polysaas-1']` is currently **$26** in settings while marketing shows **$29**. This pass keeps marketing at $29/$49/$99; confirm Stripe/live display separately.
