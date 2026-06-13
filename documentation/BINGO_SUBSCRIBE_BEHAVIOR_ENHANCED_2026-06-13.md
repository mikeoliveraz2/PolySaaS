# BINGO — Subscribe Behavior Enhanced (Provisioning Wait Modal)

**Date:** 2026-06-13  
**Declared by:** Michael  
**Commit:** `(filled after commit)`  
**Baseline:** BINGO `fd9febb8` — PolySaaS AI context-aware chat (Geronimo)  
**Test URL:** `http://localhost:8000/dose/subscribe/`

---

## What Was Achieved

After **Subscribe & Pay**, subscribers see a blocking modal while Stripe tokenization and synchronous tenant/app provisioning run. The UI sets expectations (“just a few moments longer”) instead of leaving the form idle during a long POST to `/dose/api/subscriptions/`.

### Certified behaviors

| Feature | Status |
|---------|--------|
| Modal appears immediately after valid submit (post-validation) | ✓ |
| Button shows **Processing…** and is disabled while in flight | ✓ |
| Spinner + “Setting up your account” + patience copy | ✓ |
| Modal stays visible through Stripe token + provisioning API call | ✓ |
| Modal closes on success before login redirect message | ✓ |
| Modal closes on any error; button restored to **Subscribe & Pay** | ✓ |
| Body scroll locked while modal visible | ✓ |
| Accessible: `role="dialog"`, `aria-modal`, labelled title/body | ✓ |

---

## How It Works

```
User clicks Subscribe & Pay (form valid)
    → showProvisioningModal()
    → stripe.createToken(card)
    → POST /dose/api/subscriptions/ (sync provisioning saga)
    → hideProvisioningModal()
    → success: login redirect message | error: inline feedback
```

---

## Files in This BINGO

| File | Change |
|------|--------|
| `dose/templates/dose/subscribe.html` | Provisioning modal HTML/CSS/JS |
| `dose/templates/dose/subscribe.html.bak-provisioning-modal` | Backup before edit |

**Unchanged (existing saga):** `dose/subscription_views.py` — synchronous provisioning after Stripe + DB commit.

---

## Verification Steps

1. Open `/dose/subscribe/`
2. Complete tenant, account, app, plan, and test card fields (e.g. Stripe test `4242…`)
3. Click **Subscribe & Pay**
4. Confirm modal appears with spinner and provisioning patience message
5. Wait for completion — modal closes; success shows login link / redirect
6. Optional error path: invalid card — modal closes, error shown, button re-enabled

---

## Out of Scope (by design)

- Progress percentage or per-app provisioning steps in the modal
- Async/Celery-only provisioning UX (backend may still queue some work; modal covers the synchronous POST window)
