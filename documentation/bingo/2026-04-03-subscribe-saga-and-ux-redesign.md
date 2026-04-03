# Bingo: Subscribe Saga Pattern & UX Redesign

**Date:** 2026-04-03
**Status:** Tested and verified end-to-end

## What Was Done

### 1. Saga Transaction Pattern (`subscription_views.py`)

Restructured the subscription API (`POST /dose/api/subscriptions/`) from a fragile
linear flow into a proper saga with five phases:

| Phase | What | Rollback |
|-------|------|----------|
| 1 — Validate | Input checks, duplicate detection, plan/slot math | Pure — early 400, nothing to undo |
| 2 — Stripe | `Customer.create` + `Subscription.create` | `_compensate_stripe()` cancels sub / deletes customer |
| 3 — DB atomic | `transaction.atomic()` wrapping User, Tenant, UserProfile, Subscription, dj-stripe sync, OAuth apps | PostgreSQL rollback; except block fires Stripe compensation |
| 4 — Login | `login(request, user_obj)` | Only runs after successful commit |
| 5 — Celery | `transaction.on_commit()` with `_safe_enqueue` wrapper | Never enqueued if txn rolls back; broker errors logged, not raised |

Key fixes:
- **djstripe optional:** `import djstripe.models` guarded with try/except so subscribe works when djstripe isn't installed.
- **Celery safe enqueue:** `_safe_enqueue` wrapper catches broker connection errors (e.g. Redis missing) so a committed subscription doesn't become a 500.
- **`selected_apps` field:** Added `JSONField` to `Subscription` model (was in DB but missing from model). Migration 0032 generated and faked.

### 2. Subscribe Page UX Redesign (`subscribe.html`)

Reversed the page flow from plan-first to apps-first:

**Old flow:** Choose plan → fill form → pick apps (constrained by plan) → pay
**New flow:** Fill tenant/account info → pick apps freely → plan auto-suggested → pay

Features:
- Slot counter updates in real time as apps are checked.
- Advisory messages: >3 slots shows orange warning ("select fewer for a cheaper plan"), 2–3 shows blue info, 1 shows "fits PolySaaS-1".
- Cheapest fitting plan auto-selected with green "Recommended" badge.
- Plans too small for current selections are greyed out and unclickable.
- Amount field auto-fills from selected plan.
- Subscribe button disabled until all fields valid + plan selected.

### 3. Stripe Price Setup

Created Stripe test-mode product and prices via API:

| Tier | Price/mo | Price ID |
|------|----------|----------|
| polysaas-1 | $26 | `price_1THuAkPQWnaGoDqyqW9KlPQI` |
| polysaas-3 | $49 | `price_1THuAlPQWnaGoDqyDKQ8QG9e` |
| polysaas-unlimited | $99 | `price_1THuAlPQWnaGoDqyQkUX2SDL` |
| storage (per GB) | $0.12 | `price_1THuBBPQWnaGoDqy0fcecW1a` |

All added to `.env` as `STRIPE_PRICE_ID_*` variables.

### 4. Cleanup Command Hardened (`cleanup_subscribe_test_artifacts.py`)

- **djstripe FK chain:** Raw SQL cleanup follows `subscriptionitem → subscription → customer → auth_user` with savepoints for speculative deletes.
- **Generic FK discovery via pg_catalog:** Handles any new public table referencing `auth_user`.
- **Savepoints:** Each speculative DELETE wrapped in `transaction.atomic()` (nested savepoint) so a failed statement doesn't poison the PostgreSQL transaction.

### 5. Login Link on Duplicate Username

When subscribe returns "username already taken", the API now includes `login_url` and the UI renders a clickable "Sign in here" link.

## Test Evidence

Full end-to-end subscribe tested with:
- Tenant: PolySaaS Online LLC / polysaas-llc
- User: PSOllie (michael.oliver@polysaas.online)
- Plan: PolySaaS-Unlimited ($99/mo)
- Apps: Odoo, Nextcloud, Mattermost, WordPress, Liferay, PolySysMon
- Stripe: Customer + Subscription created in test mode
- DB: User, Tenant, UserProfile, Subscription all committed atomically
- Celery: Enqueue failed gracefully (no Redis broker), logged but did not crash response
- Cleanup: Full removal including djstripe chain verified

## Files Changed

- `dose/subscription_views.py` — saga pattern, djstripe guard, safe Celery enqueue, login_url
- `dose/templates/dose/subscribe.html` — apps-first UX, auto plan suggestion, login link
- `dose/models/subscription.py` — added `selected_apps` JSONField
- `dose/migrations/0032_add_selected_apps_to_subscription.py` — migration (faked, column pre-existed)
- `dose/management/commands/cleanup_subscribe_test_artifacts.py` — djstripe chain, savepoints
- `.env` — Stripe price IDs (not committed)
