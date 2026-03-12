# Plan: Stripe Bank Routing & Plan Upgrades

**Date:** 2026-03-09  
**Updated:** 2026-03-10 — Shela confirmed USAA + Wise workflow  
**Status:** Approved by Shela — awaiting implementation  
**Decision makers:** Michael + Shela

---

## Queue Item 1: Stripe Payouts — Option C (Single US Account)

### Decision

Single US-based Stripe account linked to **USAA bank account** as primary payout destination. PH distribution handled via **Wise** (existing workflow Michael has used for years).

### Rationale

- Simplest setup for seed stage — no doubled compliance, no multi-entity tax headaches.
- Most PolySaaS revenue will be in USD regardless of customer location.
- Stripe handles currency conversion to USD automatically for non-USD charges.
- PH transfer costs are low via Wise (~0.4–1% FX + small fixed fee) and can be done on a schedule.
- Revisit multi-currency settlement or Stripe Connect if PH-local volume grows.

### Why USAA + Wise Is the Right Fit (Shela's Analysis, 2026-03-10)

- **Stripe payouts land cleanly in USAA** as USD via free/fast ACH (typically 2 business days). No conversion needed on Stripe's end — all card charges globally settle as USD.
- **Wise handles the PH side seamlessly**: Michael already has an established USAA → Wise → PH bank pipeline. Low fees (~0.4–1%), mid-market rates, quick transfers. No new workflows to learn.
- **US-registered Stripe accounts only support US-based banks for USD payouts** — you cannot add a PH bank directly to a US Stripe account. This makes the USAA + Wise approach not just the simplest option but effectively the correct one.
- **No auto geo-split needed**: Revenue comes in USD regardless of customer location → all to USAA → Michael decides how much / what frequency to push to PH via Wise. Keeps Stripe account simple (one bank), compliance easy, manual effort minimal.
- **Cost reality**: Stripe payouts to US banks = free (standard ACH). Wise PH transfers = cheap (~0.4–1%). Early stage burn stays low.

### Action Items

| # | Task | Owner | Notes |
|---|------|-------|-------|
| 1 | Create live Stripe account (or activate existing test account) | Michael | US-registered, linked to USAA |
| 2 | Move Stripe secret key from hardcoded `subscription_views.py:13` to environment variable | Dev | Security — must happen before going live |
| 3 | Move Stripe publishable key from hardcoded `subscribe.html:267` to Django template context | Dev | Same — no keys in source code |
| 4 | **Stripe Dashboard setup** (https://dashboard.stripe.com/settings/payouts) | Michael | See checklist below |
| 5 | Continue using existing Wise workflow for USD→PHP transfers | Michael | Already established — no new setup needed |
| 6 | Configure Stripe webhooks for production URL | Dev | `invoice.paid`, `invoice.payment_failed`, `customer.subscription.updated`, `customer.subscription.deleted` |

### Stripe Dashboard Checklist (Item 4 Detail)

1. Confirm USAA account is added/verified as payout destination.
2. Set default settlement currency to USD (if not already).
3. **Skip** adding any other banks or currencies for now — avoids verification hassles.
4. Set payout schedule: automatic daily or weekly (Michael's preference for cash flow visibility).

### Test Flow (Once Test Charges Work)

1. Make a test payment in Stripe test mode.
2. Trigger a payout (or wait for auto-payout).
3. Verify it hits USAA.
4. Transfer a portion via Wise to PH as usual — confirms end-to-end pipeline.

### Future Revisit Triggers

- PH-based customers exceed 20% of revenue → consider enabling PHP settlement (may require separate PH-registered Stripe account).
- PolySaaS becomes a marketplace (vendors/resellers) → evaluate Stripe Connect.
- FX/transfer costs exceed $200/mo → automate or switch to multi-currency settlement.
- **Alternative future option**: Link a Wise Business borderless USD account directly to Stripe (Wise provides US routing/account details), letting Wise handle multi-currency internally. But USAA + Wise already works great — no rush.
- **Wise internal wallet advantage**: Once PolySaaS has steady cash flow, keeping funds in the Wise USD wallet (instead of transferring out immediately) lets you pay PH bills directly from the Wise balance — avoids transfer fees entirely. Wise supports direct bill pay and local PH transfers from the wallet. Worth switching to once revenue is predictable.

### What NOT to do

- Do NOT create a second Stripe account for PH yet.
- Do NOT use Stripe Connect just for personal payout routing — it's designed for platforms with third-party sellers.
- Do NOT try to add a PH bank to the US-registered Stripe account — it won't work (Stripe requires bank country to match settlement currency country).

---

## Queue Item 2: Plan Upgrades (1-User → 3-Users → Unlimited)

### Current State

- `Subscription` model: flat, no tier field, single `STRIPE_PRICE_ID`.
- Subscribe page: single hardcoded amount ($29.99/mo).
- No user-count enforcement per tenant.

### Target State

Three subscription tiers with self-service upgrade path:

| Tier | Max Users | Monthly Price | Stripe Price ID |
|------|-----------|---------------|-----------------|
| Starter | 1 | $29.99 | `price_starter` (create in Dashboard) |
| Team | 3 | TBD (e.g. $79.99) | `price_team` (create in Dashboard) |
| Unlimited | No limit | TBD (e.g. $199.99) | `price_unlimited` (create in Dashboard) |

Upgrade path: Starter → Team → Unlimited (no downgrades in v1).

### Implementation Plan

#### Phase 1: Model & Stripe Setup

1. **Add `plan_tier` field to `Subscription` model**
   ```python
   PLAN_TIER_CHOICES = [
       ('starter', 'Starter (1 user)'),
       ('team', 'Team (3 users)'),
       ('unlimited', 'Unlimited'),
   ]
   plan_tier = models.CharField(max_length=20, choices=PLAN_TIER_CHOICES, default='starter')
   ```

2. **Add `max_users` to `Tenant` model** (or derive from subscription tier)
   - Starter: 1, Team: 3, Unlimited: null/unlimited.
   - Alternatively, keep a `MAX_USERS_BY_TIER` dict in settings — no model change needed.

3. **Create 3 Stripe Prices in Dashboard (test mode first)**
   - Product: "PolySaaS Subscription"
   - Three recurring monthly prices attached to that product.
   - Store all three Price IDs in `settings.py`:
     ```python
     STRIPE_PRICE_IDS = {
         'starter': 'price_...',
         'team': 'price_...',
         'unlimited': 'price_...',
     }
     PLAN_MAX_USERS = {
         'starter': 1,
         'team': 3,
         'unlimited': None,  # unlimited
     }
     ```

4. **Run migration** for `plan_tier` field on `Subscription`.

#### Phase 2: Subscribe Flow Update

5. **Update `subscribe.html`**
   - Add plan selection UI (radio cards or toggle) above the payment form.
   - Dynamically update the `amount` field and displayed price based on selection.
   - Pass selected plan tier in the form payload.

6. **Update `subscription_views.py` (`create` method)**
   - Read `plan_tier` from request data.
   - Look up the correct `STRIPE_PRICE_IDS[plan_tier]` when creating the Stripe subscription.
   - Save `plan_tier` on the `Subscription` record.

#### Phase 3: Upgrade Flow

7. **New view: `upgrade_subscription`**
   - Accessible from tenant dashboard / account settings.
   - Shows current plan and available upgrades.
   - On confirm: calls `stripe.Subscription.modify()` to swap the Price:
     ```python
     stripe.Subscription.modify(
         subscription.stripe_subscription_id,
         items=[{
             'id': stripe_sub['items']['data'][0].id,
             'price': new_price_id,
         }],
         proration_behavior='create_prorations',
     )
     ```
   - Stripe auto-calculates proration (credit for unused time on old plan, charge for new).
   - Update `plan_tier` in local DB after successful Stripe call.

8. **New template: `upgrade.html`**
   - Plan comparison cards with current plan highlighted.
   - "Upgrade" button on higher tiers, disabled/greyed on current and lower.
   - Confirmation modal before processing.

9. **URL routing**
   - `dose/upgrade/` → `upgrade_subscription` view.
   - Link from dashboard sidebar / account dropdown.

#### Phase 4: Enforcement & Webhooks

10. **User limit enforcement**
    - In user invite / user creation flow: check `subscription.plan_tier` against `PLAN_MAX_USERS`.
    - If at limit, show message: "Upgrade your plan to add more users."
    - Apply check in both the admin panel and any API-based user creation.

11. **Webhook handler for `customer.subscription.updated`**
    - Sync `plan_tier` and `active` status from Stripe event data.
    - Handles edge cases: failed payment downgrades, Stripe-side changes, etc.

12. **Webhook handler for `customer.subscription.deleted`**
    - Mark subscription inactive.
    - Optionally trigger grace period / data retention flow.

### Effort Estimate

| Phase | Effort | Risk |
|-------|--------|------|
| Phase 1: Model + Stripe setup | 2–3 hours | Low |
| Phase 2: Subscribe flow update | 3–4 hours | Low |
| Phase 3: Upgrade flow | 4–6 hours | Medium (Stripe proration testing) |
| Phase 4: Enforcement + webhooks | 3–4 hours | Medium (webhook reliability) |
| **Total** | **~1.5–2 days** | |

### Testing Strategy

- All Stripe work in **test mode** first (test keys, test card numbers).
- Test proration by upgrading mid-cycle and verifying invoice amounts.
- Test enforcement by trying to exceed user limits.
- Test webhooks using Stripe CLI (`stripe listen --forward-to localhost:8000/dose/webhooks/stripe/`).
- Only switch to live keys after full end-to-end test pass.

### Files Touched

| File | Change |
|------|--------|
| `dose/models/subscription.py` | Add `plan_tier` field |
| `mysite/settings.py` | Add `STRIPE_PRICE_IDS`, `PLAN_MAX_USERS` |
| `dose/subscription_views.py` | Plan-aware creation, move keys to env vars |
| `dose/templates/dose/subscribe.html` | Plan selector UI |
| `dose/templates/dose/upgrade.html` | New upgrade page |
| `dose/views/` | New upgrade view |
| `dose/urls.py` | Add upgrade URL |
| `dose/context_processors.py` | Expose current plan to templates |
| `dose/webhooks.py` | New webhook handler (or add to existing) |

---

## Priority Order

1. **Stripe key security** (move hardcoded keys to env vars) — do this first regardless.
2. **Phase 1–2 of upgrades** (model + subscribe flow) — foundational.
3. **Stripe live activation** (Option C setup) — when ready to accept real payments.
4. **Phase 3–4 of upgrades** (upgrade flow + enforcement) — can ship shortly after.
