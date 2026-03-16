# BINGO: Standard Footer Added to All Pages

**Date:** 2026-03-16
**Status:** Complete
**Snapshot:** `snapshot_20260316_135013_bingo_standard_footer_all_pages.json`

## Summary

Discovered that the site-wide footer (contact info, application links, feature links, gallery links, copyright bar with Privacy Policy / Terms of Service / Disclaimer) was only present on 2 of 25 pages (Home and About Us). The footer was embedded in page content, not a theme widget. Extracted the footer and added it to all 23 missing pages.

## Audit Results

- **Before:** 2/25 pages had the standard footer (Home, About Us)
- **After:** 25/25 pages have the standard footer

## Footer Contents

The standard footer includes:
1. **CTA Section:** "Stop Managing Tools. Start Orchestrating Them." with "Sign Up for a Demo" button
2. **Contact Info:** 5900 Balcones Drive Suite 100, Austin TX 78731 / michael.oliver@polysaas.online / phone numbers
3. **Applications Links:** Liferay, MatterMost, NextCloud, Odoo, PolySysMon, WordPress, Dolibarr, Monitor Logger
4. **Features Links:** Bundled Applications, External Applications, AI As Peers, Apps As Peers, PolySniffer, Dynamic Orchestration, Atomic Services, OpenAPI, Portal, Architecture
5. **Gallery Links:** Images, Videos
6. **Copyright Bar:** © 2026 PolySaaS Online with Privacy Policy, Terms of Service, Disclaimer links

## Root Cause

The footer was hardcoded into page content (HTML within `<!-- wp:html -->` blocks) rather than implemented as a Kadence theme footer widget. Only the Home and About Us pages had it manually added during initial page creation. All other pages were created without the footer section.

## Pages Updated (23)

1319-2, ai-as-peers, apps-as-peers, architecture, atomic-services, blog, bundled-applications, dolibarr-3, dynamic-orchestration, gallery-images, gallery-videos, liferay-2, mattermost, monitor-logger-4, nextcloud, odoo, openapi-2, polysniffer, polysysmon, portal, pricing, schedule-demo, wordpress-3

## Technical Note

The extracted footer has a minor div-balance of -1 (one extra `</div>`). This is inherited from the source About Us page structure. Browsers handle this gracefully and no visual issues were observed.

## Advisory

Consider migrating the footer to a Kadence theme footer widget in the future. This would ensure it appears on all pages automatically (including any new pages) without needing to embed it in page content manually.

## Scripts

- `audit_footers.py` — audits all pages for footer presence
- `add_footer_all_pages.py` — initial (incorrect) extraction
- `fix_footer_extraction.py` — corrected extraction and application
