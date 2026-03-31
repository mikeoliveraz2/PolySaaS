# BINGO: Stripe Plan Tiers & Upgrade Flow

**Date:** 2026-03-10  
**Session:** Stripe bank routing decision (Option C: USAA + Wise) + subscription plan tiers implementation  
**Approved by:** Michael + Shela

## What Was Done

### Stripe Key Security
- Moved hardcoded Stripe secret key from `subscription_views.py` to `.env` → loaded via `settings.STRIPE_SECRET_KEY`
- Moved hardcoded Stripe publishable key from `subscribe.html` to Django template context → `settings.STRIPE_PUBLISHABLE_KEY`
- Added `STRIPE_WEBHOOK_SECRET` env var placeholder for webhook signature verification

### Subscription Plan Tiers (Phase 1–2)
- Added `plan_tier` field to `Subscription` model with choices: `starter` (1 user), `team` (3 users), `unlimited`
- Added model helper methods: `get_max_users()`, `can_add_user()`, `get_price()`
- Added settings: `STRIPE_PRICE_IDS`, `PLAN_PRICES`, `PLAN_MAX_USERS` dicts
- Migration `0023_add_plan_tier_to_subscription` applied to `public` and `olient` schemas
- Updated `subscribe.html` with plan selection cards (Starter/Team/Unlimited) — dynamic pricing, hidden form field
- Updated `subscription_views.py` to read `plan_tier`, lookup correct Stripe Price ID per tier, save tier on record
- Updated `SubscriptionCreateSerializer` with `plan_tier` field

### Upgrade Flow (Phase 3)
- New view: `dose/views/upgrade.py` — login-required, shows current plan + upgrade options
- Uses `stripe.Subscription.modify()` with `proration_behavior='create_prorations'` for automatic mid-cycle proration
- Upgrade only (no downgrades in v1), confirmation prompt, error handling for card declines
- New template: `dose/templates/dose/upgrade.html` — plan comparison cards with Current Plan badge
- URL: `/dose/upgrade/`

### Stripe Webhook Handler (Phase 4a)
- New view: `dose/views/stripe_webhook.py` — CSRF-exempt, POST-only
- Handles: `customer.subscription.updated` (syncs tier + active status), `customer.subscription.deleted` (marks inactive), `invoice.paid` (reactivates), `invoice.payment_failed` (logs warning)
- Signature verification via `STRIPE_WEBHOOK_SECRET`
- Reverse price-to-tier lookup for automatic tier sync from Stripe events
- URL: `/dose/webhook/stripe/`

### User Limit Enforcement (Phase 4b)
- `check_user_limit()` utility in `dose/utils.py` — reusable `(allowed, message)` check
- `UserProfileAdmin.save_model()` blocks adding users beyond plan limit in Django admin
- Clear error messages with tier name and user count

### Stripe Bank Routing Decision (Documentation Only)
- Option C confirmed: Single US Stripe account → USAA bank → Wise for PH distribution
- Full decision rationale, action items, and future revisit triggers documented
- `documentation/PLAN_STRIPE_AND_UPGRADES.md` — comprehensive plan document

### Bug Fixes
- Fixed Unicode characters (checkmarks/crosses) in `migrate.py` and `migrate_all_schemas.py` management commands that crashed on Windows cp1252 encoding
- Fixed olient schema migration state (faked missing 0007–0022 migrations for pre-existing tables)

## Files Created
- `documentation/PLAN_STRIPE_AND_UPGRADES.md`
- `dose/views/upgrade.py`
- `dose/views/stripe_webhook.py`
- `dose/templates/dose/upgrade.html`
- `dose/migrations/0023_add_plan_tier_to_subscription.py`

## Files Modified
- `dose/models/subscription.py` — plan_tier field + helpers
- `dose/subscription_views.py` — plan-aware creation, env-based Stripe key
- `dose/templates/dose/subscribe.html` — plan cards UI, env-based publishable key
- `dose/views/main.py` — pass STRIPE_PUBLISHABLE_KEY + PLAN_PRICES to template
- `dose/serializers.py` — plan_tier on SubscriptionCreateSerializer
- `dose/urls.py` — upgrade + webhook URLs
- `dose/admin.py` — UserProfileAdmin user limit enforcement
- `dose/utils.py` — check_user_limit() utility
- `mysite/settings.py` — STRIPE_SECRET_KEY, STRIPE_PUBLISHABLE_KEY, STRIPE_WEBHOOK_SECRET, STRIPE_PRICE_IDS, PLAN_PRICES, PLAN_MAX_USERS
- `dose/management/commands/migrate.py` — Windows encoding fix
- `dose/management/commands/migrate_all_schemas.py` — Windows encoding fix

## Laptop Sync Notes (IMPORTANT)

After `git pull origin main` on the laptop, you MUST update the laptop's `.env` file manually — it is gitignored and does not sync via git.

Add these three lines to the bottom of the laptop's `.env`:

```
STRIPE_SECRET_KEY=sk_test_YOUR_KEY_HERE
STRIPE_PUBLISHABLE_KEY=pk_test_YOUR_KEY_HERE
STRIPE_WEBHOOK_SECRET=whsec_PLACEHOLDER_SET_FROM_STRIPE_CLI_OR_DASHBOARD
```

Then run migrations on the laptop DB:
```
python manage.py migrate_all_schemas
```

The migration `0023_add_plan_tier_to_subscription` will add the `plan_tier` column to the laptop's database schemas. If the laptop DB already has the column (unlikely unless you ran it there too), the migration will either apply cleanly or you can fake it.

## Manual Steps Remaining
1. Create Team ($79.99) and Unlimited ($199.99) prices in Stripe Dashboard (test mode)
2. Paste Price IDs into `STRIPE_PRICE_IDS` in `settings.py`
3. Set `STRIPE_WEBHOOK_SECRET` in `.env` (from `stripe listen` CLI or Stripe Dashboard)
4. Test full flow: subscribe with plan selection → upgrade → verify proration → webhook sync

## Verification
- `python manage.py check` — System check identified no issues (0 silenced)
- Migration applied to both `public` and `olient` schemas on desktop
- Zero linter errors on all modified files
