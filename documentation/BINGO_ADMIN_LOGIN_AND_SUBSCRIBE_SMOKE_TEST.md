# BINGO: Admin Login Fix + Subscribe Smoke Test

Date: 2026-04-27
Branch: main
Status: COMPLETE (BINGO)

## Summary
- Fixed admin login flow at `/accounts/login/` so valid credentials reliably result in an authenticated session and redirect (instead of re-rendering the login page with an “Invalid login” error).
- Added clearer backend debug output to distinguish user-not-found vs password-mismatch vs inactive-user cases.
- Performed a quick smoke test of the `/subscribe/` flow (GET renders subscribe page; POST renders social-connect step) to ensure it was not broken by login changes.

## Key Outcome
- Superuser login works through the browser against the Allauth login page (including `?next=/admin/`).
- Subscribe flow still renders correctly after the login fix.

## Changes Made
- `mysite/urls.py`
  - Route override: `path('accounts/login/', CustomLoginView.as_view(), name='account_login')` placed before `include('allauth.urls')`.
- `dose/views_custom_login.py`
  - Added `post()` override to authenticate using raw POST `login`/`password` and explicitly `login(request, user)` before redirecting to `get_success_url()`.
- `mysite/auth_backends_allauth.py`
  - Improved debug logging so failures are correctly categorized (no functional change).

## Smoke Test Evidence
Executed via Django test client:
- `GET /subscribe/` returned `200` and contained “subscribe” page markers.
- `POST /subscribe/` returned `200` and contained “social/google/connect” markers consistent with the connect-social step.

## Notes / Follow-ups
- The Allauth form was still reporting “Invalid login” even when backend authentication succeeded; the `CustomLoginView.post()` override ensures the authenticated session is established reliably.
- Consider removing/toning down debug prints once stable.
