# BINGO: Signup Password Security Fix + Odoo Invoicing Trailing-Slash Fix

**Date:** 2026-08-02
**Verified by:** Michael + agent, end-to-end automated test (tenant `pso15`)

## What this certifies

Two independent, owner-approved fixes are tested and locked as of this commit:

1. **Odoo Invoicing "click nothing happens" fix** (`mysite/urls.py`)
2. **Signup password security fix** (`dose/subscription_views.py`, `dose/templates/dose/subscribe.html`)

---

## 1. Odoo Invoicing trailing-slash fix

**Symptom:** Clicking "Activate Invoicing" (and other Odoo action buttons that POST via JSON-RPC,
e.g. `/web/dataset/call_button/...`) silently did nothing.

**Root cause:** `pt/admin/<str:endpoint>/<path:subpath>/` and `pt/dose/<str:trigger>/<path:subpath>/`
required a trailing slash. Odoo's own JS commonly POSTs to paths *without* a trailing slash. Django's
`APPEND_SLASH` middleware tried to 301-redirect those, but redirects are refused for POST bodies,
producing a silent 500 that the button's fetch/XHR swallowed.

**Fix:** Dropped the trailing slash requirement from both subpath URL patterns in `mysite/urls.py`
so they match paths with or without a trailing slash. `forwarding.py` already normalizes the subpath
generically (prepends `/` if missing), so no other file needed to change.

**Verified:** Manually confirmed Odoo Invoicing actions now complete instead of silently failing.

---

## 2. Signup password security fix

**Trigger:** User asked *"seems like a security flaw, how does a password work once but then not
again?"* after `pso14` couldn't log in with the password they believed they'd set.

**Two problems found:**

1. **Plaintext password logging** — `dose/subscription_views.py` logged the raw signup password in
   a `[DEBUG] Creating user: ...` warning log line. Anyone with log access could read new users'
   passwords in plaintext.
2. **No confirm-password field** — `dose/templates/dose/subscribe.html` had a single password input.
   A typo, autocaps, or browser autofill mismatch would silently store a password different from
   what the user thought they typed, with no way to catch it before submit.

**Fixes:**

- `dose/subscription_views.py`: the debug log now records only `<redacted len=N>` instead of the
  raw password.
- `dose/templates/dose/subscribe.html`: added a required "Confirm Password" field with its own
  show/hide toggle, wired into the existing client-side validation (`checkFormFields`,
  `validateField`, `fieldIds`, and the submit handler) so submission is blocked client-side if the
  two fields don't match, or if either is empty.

### End-to-end verification (tenant `pso15`)

Ran a full signup → provision → login → UI-render cycle via Django's test `Client()` (equivalent
to what the real subscribe form posts to `/dose/api/subscriptions/`):

1. **Signup POST** — `201 Created`. Tenant `pso15`, admin user `PSO15`, Odoo enabled (plan bumped
   to `polysaas-3` since Odoo consumes 2 of `PLAN_MAX_APPS` — pre-existing plan rule, not a bug).
   Debug log confirmed: `password=<redacted len=12>` — no plaintext logged.
2. **Password correctness** — `authenticate(username='PSO15', password='Pso15Secure!')` succeeded;
   `authenticate(username='PSO15', password='WrongPassword!')` correctly returned `None`. The exact
   password submitted at signup is the one that logs in.
3. **Odoo provisioning** — `TenantApp.status == 'active'` for `pso15`/`odoo`. Real Odoo database
   `odoo_pso15` created, XML-RPC login succeeded, credentials stored. (Non-fatal notes: XML-RPC auth
   fell back to default `menu_id` during invoice-orchestration seeding, and the welcome email failed
   because `gmail_creds.json` isn't present in this dev environment — neither blocked provisioning.)
4. **Passthrough readiness UI (live)** — logged in as `PSO15`, fetched `/admin/`. Odoo sidebar card
   rendered as a clickable `<a>` with `class="pss-pt-card"` (no `--not-ready`) and a green
   `pss-pt-status-dot--ready` dot — confirming the readiness-UI feature (from the prior BINGO,
   `ca686a3f`) correctly reflects a freshly-provisioned, now-active app.

Provisioning in this codepath runs synchronously inside the signup request (not async/Celery), so
the sidebar was already green by the time the page loaded — there was no window to observe the
gray "provisioning" state live in this test.

Tenant `pso15` (user `PSO15` / password `Pso15Secure!`) was left in the database as a known-good
demo/test tenant.

---

## Files in this commit

- `mysite/urls.py`
- `dose/subscription_views.py`
- `dose/templates/dose/subscribe.html`
- `.bak` copies of the above (created before editing, per `bak-before-edit.mdc`)
- `documentation/BINGO_SIGNUP_PASSWORD_SECURITY_AND_ODOO_TRAILING_SLASH_2026-08-02.md` (this file)

All three source files carry the freeze banner and a `BINGO:` annotation line dated 2026-08-02.
