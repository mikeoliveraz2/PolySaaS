# Note for Desktop-CC (from Laptop – 2026-03-08)

**GCP deployment plan and checklist**

We added a shared plan and todo checklist for GCP deployment so you, Michael, and I can track the same work:

- **File:** `documentation/deployment/GCP-Deployment-Readiness-and-Checklist.md`

**Readiness gate:** Deploy to GCP only after all bundled apps use OAuth2/SSO for users coming through PolySaaS (login once, no second login per app).

**Contents:**
- Readiness gate checklist (POL-1 … POL-5) and table of bundled apps with OAuth2/SSO status
- High-level GCP plan (pre-deploy → prep → deploy Django → deploy bundled apps → post-deploy)
- Todo checklist with IDs (R-*, G-*, D-*, B-*, P-*) and Owner column for Michael / Laptop / Desktop
- Short "who does what" for human vs agents

Please pull to get this file. When you pick up a task, mark it in the checklist and set the Owner so we stay in sync.

— Laptop Cursor

---

## Session note (laptop – 2026-03-09)

**Summary for Desktop-CC:** Laptop fixed runserver/go so the project runs **without** `django-oauth-toolkit` (oauth2_provider) installed. Desktop has the package; laptop does not. All changes are backward‑compatible: when oauth2_provider is installed, behavior is unchanged.

**Changes in this commit:**

1. **oauth2_provider optional everywhere**
   - **mysite/urls.py:** OAuth2 routes (`o/authorize/`, `o/`) only added when oauth2_provider imports successfully.
   - **mysite/settings.py:** `_oauth2_available` after filtering INSTALLED_APPS; `AUTHENTICATION_BACKENDS` and `MIDDLEWARE` include OAuth2 backend/middleware only when `_oauth2_available`.
   - **dose/models/tenant_app.py:** `oauth_application` OneToOneField defined only when `apps.is_installed('oauth2_provider')`.
   - **dose/admin.py:** `TenantAppAdmin.raw_id_fields` includes `oauth_application` only when oauth2_provider is installed.

2. **Migrations (load without oauth2_provider)**
   - **0022_tenantapp.py:** Removed `swappable_dependency(oauth2_provider)` and removed `oauth_application` from CreateModel so migration loads when the app is not installed.
   - **0023_tenantapp_oauth_application_optional.py:** New migration; RunPython adds `oauth_application_id` column only when oauth2_provider is installed (no dependency on that app so loader does not fail).

3. **go.ps1 / backup**
   - **go.ps1:** Single-quote for “App loads OK … backup runs when you exit runserver” (semicolon was breaking PowerShell). Blog refresh message: em dash replaced with semicolon. **Backup exclude:** `dose\website` so that tree is not backed up locally.
   - **backup.ps1:** Same backup exclude `dose\website`.

4. **Migrations Unicode (Windows cp1252)**
   - **dose/management/commands/migrate.py** and **migrate_all_schemas.py:** Replaced ✓/✗ with `[OK]` / `[FAIL]` so migrate runs without UnicodeEncodeError on Windows.

**What you should do after pull:** Nothing required. If you have django-oauth-toolkit installed, OAuth2 and TenantApp.oauth_application work as before. If you run on a machine without it, runserver and migrate both work.

— Laptop Cursor

---

## Cross-app sync page + docs (laptop – 2026-02-28)

**For Desktop-CC:** Michael recreated screenshots for the **Cross-Application Sync** POC and asked you to update the **WordPress page** and **documentation**. On this laptop:

- `git pull origin main` was **already up to date** — no commit from desktop with those updates yet.
- WordPress REST for slug `cross-app-sync` still shows **`modified_gmt`: 2026-03-22** (page id 2700). If you only replaced **media** files without clicking **Update** on the page, the API timestamp may not change.

**What we did on laptop to sync the repo:**

- Added **`documentation/website/cross-app-sync-poc.md`** and later **re-synced it to match the live WordPress page** (full tables, mapping rows, **12 screenshot URLs** `crossapp-*.png` / `.jpg`, alt text). The **page** is canonical for layout; the **markdown** should be updated whenever WP changes.
- Helper: **`documentation/website/_extract_cross_app_sync_wp.py`** — re-fetch image list from WP REST (writes local `_cross_app_sync_extract.txt`, gitignored).

**Please do when you’re back on desktop:**

1. After any WP edit, run the script (or pull) and align **`cross-app-sync-poc.md`** if needed, then **push**.

— Laptop Cursor
