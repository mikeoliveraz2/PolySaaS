# BINGO — HubSpot WordPress Page, Bundled Apps Count, Pricing, and Home Page Updates

**Date:** July 10, 2026  
**Status:** COMPLETE — Live on production WordPress  
**Site:** `https://polysaas.online`

---

## Summary

Delivered a new live **HubSpot** child page under **Bundled Applications**, then updated the surrounding marketing surfaces so the site consistently reflects the current offer:

1. **New HubSpot page published** under Bundled Applications
2. **Bundled Applications page updated** from eight to nine applications and linked to HubSpot
3. **Pricing page updated** with Additional Users per tenant discounts
4. **Home page updated** to show nine applications, a HubSpot `(BYOL)` card, and the new Additional Users pricing block

---

## 1. HubSpot Child Page

### Goal
Create a proper WordPress marketing page for HubSpot under the Bundled Applications section instead of leaving HubSpot only implied by platform/product docs.

### Result
Published a new child page at:

`https://polysaas.online/bundled-applications/hubspot/`

### Content added
- HubSpot CRM positioning inside PolySaaS
- Tenant-scoped HubSpot connection messaging
- Native UI vs User Context Manager explanation
- Use-case bullets for pipeline follow-up, onboarding, support escalation, and executive review
- CTA back to Bundled Applications and Schedule Demo

### Repo-backed assets created
- `documentation/website/hubspot-page-content.html`
- `documentation/website/HUBSPOT-DRAFT-PAGE-WP-ADMIN.md`
- `scripts/wp_sync_hubspot_page.py`

---

## 2. Bundled Applications Page

### Problem
The page still described the platform as having **eight** bundled applications and had no direct HubSpot entry.

### Result
Updated the live Bundled Applications page to:
- change the headline from **Eight** to **Nine** enterprise-grade applications
- add a new **HubSpot CRM — Customer Pipeline & Context** capability block
- add a direct HubSpot page link in the Applications footer list
- change integration copy from **all eight** to **all nine**

### Live verification
Verified on:

`https://polysaas.online/bundled-applications/`

### Repo source updated
- `build_all_inner_pages.py`

---

## 3. Pricing Page

### Goal
Add a new section below the three main plan options for extra tenant users and their discounts.

### Result
Added a new section titled:

**Additional Users Per Tenant**

With these bullets:
- **Users 2-10** — Each user gets a discount of 10%
- **Users 11-20** — Each user gets a discount of 20%
- **Users 31+** — Each user gets a discount of 30%

### Live verification
Verified on:

`https://polysaas.online/pricing/`

### Repo source updated
- `build_pricing_page.py`

---

## 4. Home Page

### Problem
The homepage still showed the old bundled-app count and did not surface HubSpot in the application card grid.

### Result
Updated the live homepage to:
- change the bundled application heading from **Eight** to **Nine**
- add a **HubSpot (BYOL)** card linking to the new HubSpot page
- add the **Additional Users Per Tenant** pricing block beneath the three home-page pricing cards

### Live verification
Verified on:

`https://polysaas.online/`

### Note
The homepage changes were applied directly in the live WordPress page editor. This repo does not currently have a single clean homepage source-of-truth file comparable to the new HubSpot page HTML.

---

## Technical Notes

- WordPress edits were applied against the live block editor using raw code-editor content
- For large HTML payloads, direct editor-store save operations were more reliable than manual UI typing alone
- The HubSpot page is positioned as **BYOL** on the homepage card while the dedicated page uses richer CRM/orchestration copy

---

## Files Changed In Repo

- `build_all_inner_pages.py`
- `build_pricing_page.py`
- `documentation/website/hubspot-page-content.html`
- `documentation/website/HUBSPOT-DRAFT-PAGE-WP-ADMIN.md`
- `scripts/wp_sync_hubspot_page.py`
- `documentation/BINGO_HUBSPOT_WORDPRESS_PRICING_HOME_2026-07-10.md`

---

## Verification

- `python -m py_compile build_all_inner_pages.py`
- `python -m py_compile build_pricing_page.py`
- Public page verification performed in-browser for:
  - `/bundled-applications/hubspot/`
  - `/bundled-applications/`
  - `/pricing/`
  - `/`