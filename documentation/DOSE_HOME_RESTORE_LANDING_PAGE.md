# DOSE: Restore /dose/ Home Page to Landing Page

## Summary
The `/dose/` landing route was updated to render the classic DOSE home experience (`dose/landing_page.html`) to match existing training videos and user expectations.

## Behavior
- Unauthenticated users are redirected to `/accounts/login/?next=/dose/`.
- Authenticated users without a tenant context are redirected to `dose:select_tenant`.
- Authenticated users with a tenant context are served `dose/landing_page.html`.

## Implementation
- `dose/views/main.py`
  - `index()` now:
    - redirects to tenant selection when `tenant_prompt` is set in the landing context
    - otherwise renders `dose/landing_page.html`
