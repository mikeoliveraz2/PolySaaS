# BINGO: Render Jazzmin `/admin/` model tiles + diagnostics (April 2026)

Operational record for PolySaaS-Core on Render: the Django admin home showed **no Jazzmin model cards** (empty `app_list` in practice), while the same code worked locally. This doc captures what was wrong, what we shipped, and how to verify or recover next time.

## Symptoms

- `/admin/` after login: **Recent actions** and chrome rendered, but **no per-app model tiles** (or only the orchestration CTA strip dominated the layout).
- Shell: `registry_len` in the high tens (e.g. **84**) proved models **were registered**; the gap was **who** was logged in and **how** we diagnosed it.

## Root causes (in order of discovery)

1. **Missing runtime dependencies in the slim image** (separate from tiles): `gunicorn` and `whitenoise` were not in `requirements.txt` while `Dockerfile.django` / `settings_render` expected them → boot failures until added.
2. **Superuser / staff on the Render database**: the Google-style username (`Michael.Oliver@polysaas.online`) had **`is_staff=True`** but **`is_superuser=False`**. Django’s admin index builds `app_list` from permissions; without superuser (or broad model perms), **the list is empty** even with 84 registered models.
3. **`promote_superuser` not discoverable**: first implementation lived under `mysite/management/commands/`, but **`mysite` is not in `INSTALLED_APPS`**, so Django never registered the command. **Fix:** move the command to `dose/management/commands/promote_superuser.py`.
4. **Email vs allauth**: some accounts store the address on **`allauth.account.EmailAddress`** while **`User.email`** differs. **Fix:** `promote_superuser --email` resolves **User.email first**, then **EmailAddress**; also sets **`is_active=True`** when needed.
5. **`diagnose_admin_dashboard` false negative on Render**: the test `Client` uses **`Host: testserver`**, which production **`ALLOWED_HOSTS` rejects** → `DisallowedHost` / HTTP 400 → no template context, so **`app_list` looked missing**. **Fix:** send a valid **`HTTP_HOST`** (from `RENDER_EXTERNAL_URL`, `localhost`, or `ALLOWED_HOSTS`), with optional **`--http-host`**.

## UX / naming (same rollout)

- **`templates/jazzmin/admin/index.html`**: render **Jazzmin model tiles first** (`{{ block.super }}`), then the **orchestration workspace** CTA below, with copy that states it is **not** the same as model administration.
- **`dose/context_processors.py`**: sidebar labels **Admin home (models)** / **Dose workspace** instead of ambiguous “Dashboard (Admin)”.

## Commands (Render Shell, PolySaaS-Core)

Use the same service/env as the web process (`DATABASE_URL`, `DJANGO_SETTINGS_MODULE=mysite.settings_render`).

```bash
# Grant staff + superuser (+ active) — email matches User.email or allauth EmailAddress
python manage.py promote_superuser --email you@example.com

# After deploy of diagnose fix: GET /admin/ in-process with valid Host header
python manage.py diagnose_admin_dashboard --email you@example.com
```

Optional: **`POLYSAAS_SUPERUSER_EMAILS`** (comma-separated) still promotes matching accounts on **Google** login via `dose.adapters`.

## Runtime diagnostics (logs)

- **`ADMIN_INDEX_DIAG=1`** on the web service appends **`mysite.admin_index_diag.AdminIndexDiagMiddleware`** (see `mysite/settings.py`). Each successful **`GET /admin/`** index logs **`dose.admin_index_diag`** with `app_list_len`, `registry_len`, `is_superuser`, `schema_name`, etc. Turn off when finished.
- **`DoseConfig.ready()`** prints **`[admin_registry_diag] ready() registry_len=...`** to compare registration at import time vs request time.

## Env / blueprint pointers

- **`render.yaml`**: `PolySaaS-Core` includes **`ADMIN_INDEX_DIAG`** for structured index logs during bring-up (set to **`0`** when stable).
- **`.env.example`**: documents `promote_superuser`, `diagnose_admin_dashboard`, and `POLYSAAS_SUPERUSER_EMAILS`.

## Verification (“Bingo”)

- Browser: `/admin/` shows **Jazzmin cards** for Accounts, Auth, Dose Tenant Management, OAuth toolkit, etc., with **Admin home (models)** selected in the custom sidebar.
- Shell: **`diagnose_admin_dashboard`** reports **HTTP 200**, non-zero **`app_list len`**, and non-zero **Jazzmin `card mb-3`** count in HTML.

## Related files (for code search)

- `dose/management/commands/promote_superuser.py`
- `dose/management/commands/diagnose_admin_dashboard.py`
- `mysite/admin_index_diag.py`
- `dose/apps.py` (startup `registry_len` log)
- `requirements.txt` (`gunicorn`, `whitenoise`)
- `templates/jazzmin/admin/index.html`
- `dose/context_processors.py` (sidebar labels)
