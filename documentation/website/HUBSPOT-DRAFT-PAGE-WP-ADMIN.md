# HubSpot CRM - WordPress child page under Bundled Applications

Goal: keep the HubSpot marketing page repo-backed like the Machine Learning page, but create it in WordPress as a child page of Bundled Applications so the URL and page hierarchy stay clean.

Preferred hierarchy:
- Parent page: `Bundled Applications`
- Child title: `HubSpot CRM`
- Child slug: `hubspot`
- Preferred URL: `https://polysaas.online/bundled-applications/hubspot/`

## Option A - wp-admin only

1. Log in to `https://polysaas.online/wp-admin`.
2. Open `Pages -> Add New`.
3. Title: `HubSpot CRM`.
4. Slug: `hubspot`.
5. In page settings, set `Parent` to `Bundled Applications`.
6. Save as `Draft` first.
7. Add a `Custom HTML` block.
8. Paste the full contents of `documentation/website/hubspot-page-content.html`.
9. Publish only when the copy is approved.

## Option B - create or update from the repo

The repo includes `scripts/wp_sync_hubspot_page.py`.

Setup:

1. Copy `documentation/website/.env.wordpress.example` to repo root as `.env.wordpress`.
2. Fill `WP_BASE_URL`, `WP_USER`, and `WP_APP_PASSWORD`.
3. Optional parent controls:
   - `WP_PAGE_PARENT_SLUG=bundled-applications` (default)
   - or `WP_PAGE_PARENT_ID=<numeric id>` if you want to force the parent directly
   - or `WP_DISABLE_PARENT=1` if you want a top-level page temporarily

Run:

```powershell
python scripts\wp_sync_hubspot_page.py
```

Behavior:

- If the page does not exist, the script creates slug `hubspot`.
- If parent resolution is enabled, the page is created under `Bundled Applications`.
- If the page already exists, the script updates title and body from `documentation/website/hubspot-page-content.html`.
- Existing page status is preserved unless `WP_FORCE_STATUS` is set.

Useful env vars:

- `WP_PAGE_TITLE` default: `HubSpot CRM`
- `WP_PAGE_STATUS` default on create: `draft`
- `WP_FORCE_STATUS=publish` to publish during update

## Notes

- Keep the HTML source of truth in `documentation/website/hubspot-page-content.html`.
- The page is intended to sit beneath Bundled Applications in WordPress page hierarchy; whether it also appears in the site navigation is a separate header/menu decision.
- If the theme already provides the site footer, remove the pasted `<footer class="ps-hs-footer">...</footer>` block from the HTML file before final publish.