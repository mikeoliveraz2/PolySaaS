# PolySaaS documentation (internal)

Index of high-signal docs. **Not** the public marketing site.

## Multi-tenant invariant (PostgreSQL)

Never treat the PostgreSQL **`public`** schema as a tenant. Shared registry tables (for example **`dose_tenant`**) live in **`public`**; tenant-isolated application data lives in each row’s **`Tenant.schema_name`**, and the active workspace is **`request.session['tenant_id']`** (middleware sets `search_path` to that schema with `public` only as a fallback for shared tables). Do not add a `Tenant` with `schema_name='public'`, and do not read or write tenant-owned models through `public` as if it were a customer org.

## Product & concept drafts

| Doc | Purpose |
|-----|---------|
| [product/ML-PLATFORM-CONCEPT-AND-TABLES.md](product/ML-PLATFORM-CONCEPT-AND-TABLES.md) | Internal draft: ML/AI platform vision, `MLEngine` / `MLTaxonomy` / `MLDataset` schema, API/admin pointers. **Do not** use for public Features copy until reviewed. |
| [website/ML-DRAFT-PAGE-WP-ADMIN.md](website/ML-DRAFT-PAGE-WP-ADMIN.md) | WP inner pages: draft workflow, paste-ready HTML, **standard pattern** (recreate from repo; theme footer vs pasted footer). |
| [website/machine-learning-page-content.html](website/machine-learning-page-content.html) | Paste-ready HTML: **banner + ML icon**, body copy + **standard site footer** (or omit footer if theme already provides it). |
| [website/assets/](website/assets/) | `ml-icon.svg`, `ml-banner-pattern.svg` — optional Media Library uploads. |
| [bingo/2026-03-24-wordpress-machine-learning-home-footer-sync.md](bingo/2026-03-24-wordpress-machine-learning-home-footer-sync.md) | **BINGO:** ML page hero, home teaser + footer sync scripts, `.env.wordpress.example`. |

## Deployment

| Doc | Purpose |
|-----|---------|
| [deployment/render/RENDER-DEPLOYMENT-PLAN.md](deployment/render/RENDER-DEPLOYMENT-PLAN.md) | Render-first plan and operator checklist (§7). |
| [BINGO_RENDER_FOUNDATION_AND_REMAINING.md](BINGO_RENDER_FOUNDATION_AND_REMAINING.md) | Certified foundation vs remaining P1–P6 work. |
| [BINGO_RENDER_ADMIN_JAZZMIN_TILES_AND_DIAGNOSTICS.md](BINGO_RENDER_ADMIN_JAZZMIN_TILES_AND_DIAGNOSTICS.md) | **BINGO:** Render `/admin/` empty tiles → superuser, command placement, `testserver` Host, `promote_superuser` / `diagnose_admin_dashboard`, `ADMIN_INDEX_DIAG`. |

## Collaboration

See [collaboration/README.md](collaboration/README.md) for cross-machine / process notes.
