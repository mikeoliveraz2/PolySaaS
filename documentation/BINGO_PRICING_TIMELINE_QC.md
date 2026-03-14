# Bingo: Pricing Page, Timeline, Scott Headshot, QC Audit & Whitespace Reduction

**Date:** 2026-03-15  
**Status:** Complete & Tested  
**Snapshot:** `snapshot_20260315_073855_Bingo_-_pricing__timeline__Scott_headsho.json`

---

## Summary

This session addressed multiple updates to the Azure staging site (azure-nightingale-589250.hostingersite.com):

1. **Pricing Page** — Built from scratch using content from polysaas.online production site
2. **Futures Timeline** — Corrected Q1-Q4 2026 sequence on About Us page
3. **Scott Chate Headshot** — Uploaded and added to Board of Advisors
4. **Stephen Bird Removal** — Removed from advisors per client agreement restrictions
5. **Architecture Diagram** — Uploaded PolySaaS architecture image to Architecture page
6. **Roadmap Image** — Uploaded Q1-Q4 roadmap graphic to About Us Futures Timeline
7. **QC Audit** — Full site-wide consistency audit (25/25 pages pass all checks)
8. **Whitespace Reduction** — Aggressive top padding/margin reduction across all pages
9. **5 Blank Pages Set to Draft** — cta-templates, external-applications, for-parners-resellers-and-large-enterprises, for-resellers-of-liferay-and-django-customization, sign-up

---

## Pricing Page

Built with content matching polysaas.online production:

- **Starter** — $29/user/mo, choose 1 application
- **Growth** (Most Popular) — $49/user/mo, choose 3 applications
- **Unlimited** — $99/user/mo, unlimited applications

Includes dark mode CSS, toggle with hover tooltip, standard header logo size, responsive grid (3-column desktop, 1-column mobile), "Get Started" CTAs linking to /sign-up/.

### Scripts
- `get_pricing.py` — Scraped pricing content from polysaas.online
- `build_pricing_page.py` — Built initial pricing page
- `fix_pricing_css.py`, `fix_pricing_v2.py` — Fixed dark mode CSS injection
- `fix_pricing_logo2.py` — Added standard header logo CSS

---

## Futures Timeline (About Us)

Replaced old Q1 2025-based timeline with corrected 2026 sequence:

| Quarter | Status | Milestones |
|---------|--------|------------|
| Q1 2026 | In Progress | Dynamic Orchestration (Complete), GCP Deployment, AI As Peers, All Bundled Apps, Google Cloud Startup Application (Pending), User Guide |
| Q2 2026 | Upcoming | Marketing Campaign Launch, Apps As Peers, Developer Guide (Django/Liferay), White Label Version |
| Q3 2026 | Planned | Shared Annotations, Mobile App Version |
| Q4 2026 | Vision | Enterprise Maturity & Expansion (TBD) |

### Scripts
- `fix_timeline.py` — Timeline content definition
- `update_aboutus.py` — Applied timeline replacement + Scott headshot
- `check_aboutus_blocks.py`, `check_aboutus_raw.py` — Diagnostics

---

## Board of Advisors Updates

### Scott Chate
- Headshot uploaded (media id=2384)
- Title: VP Partner & Market Development, Corent Technology, Inc
- Scripts: `combined_aboutus_fix.py`, `fix_scott_proper.py`, `fix_scott_title.py`

### Stephen Bird — Removed
- Removed due to current client agreement restrictions
- Scripts: `remove_stephen.py`, `fix_stephen_removal.py`

### Remaining Advisors
- Scott Chate — with headshot
- Feyzi Fatehi — placeholder initials (headshot pending)
- Francis Uy — placeholder initials (headshot pending)

---

## Architecture & Roadmap Images

- **Architecture diagram** (media id=2378) — PolySaaS multi-tenant architecture showing users, SaaS applications, DB, and data flow
- **Roadmap timeline** (media id=2379) — Q1-Q4 visual roadmap graphic

Script: `batch_updates.py`

---

## QC Audit Results

Full site-wide audit checking 11 attributes across all published pages:

| Check | Result |
|-------|--------|
| Logo CSS (60px) | 25/25 pass |
| Root CSS vars (--ps-primary) | 25/25 pass |
| Dark mode CSS (body.dark-mode) | 25/25 pass |
| Toggle button | 25/25 pass |
| Toggle script (localStorage) | 25/25 pass |
| Toggle hover tooltip | 25/25 pass |
| Top padding CSS | 25/25 pass |
| Menubar light grey (#F1F5F9) | 25/25 pass |
| Menubar dark blue (#1E293B) | 25/25 pass |
| Nav dark mode font | 25/25 pass |
| Content present (>200 chars) | 25/25 pass |

5 blank pages set to Draft: cta-templates, external-applications, for-parners-resellers-and-large-enterprises, for-resellers-of-liferay-and-django-customization, sign-up.

Script: `qc_audit.py`, `mark_unused_pages.py`

---

## Whitespace Reduction

Applied aggressive CSS overrides to all 25 pages targeting Kadence theme containers:
- `content-area`, `entry-content-wrap`, `entry-hero-container-inner`, `site-main`, `entry-header`, `kadence-page-hero`, `wp-block-post-title`, `entry-title` — all set to `margin-top: 0; padding-top: 0;`
- Homepage-specific: H2 padding reduced, empty `<p><br></p>` spacers removed, `.wp-block-group` and `.wp-block-image` margins zeroed

Scripts: `fix_whitespace_aggressive.py`, `fix_homepage_gap3.py`

---

## Published Pages (25 total)

home, about-us, architecture, portal, dynamic-orchestration, atomic-services, polysniffer, apps-as-peers, openapi-2, ai-as-peers, bundled-applications, odoo, nextcloud, mattermost, wordpress-3, liferay-2, dolibarr-3, monitor-logger-4, polysysmon, pricing, blog, gallery-images, gallery-videos, schedule-demo, 1319-2

---

## Pending Items
- Feyzi Fatehi headshot (awaiting from advisor)
- Francis Uy headshot (awaiting from advisor)
- Pricing page value proposition section (from polysaas.online — to be added below pricing tiers)
- Timeline dates to be verified by Mike and Shela
