# BINGO — Odoo Passthrough Regression (Post–Nextcloud Handler Work)

**Date:** 2026-04-09  
**Certified by:** Michael (manual test, first pass)  
**Context:** After Nextcloud display-shell fixes (commit `5947746` and related work), verify Odoo was not regressed.

---

## What Was Tested

- Incognito (or clean session), PolySaaS display shell Phase 1
- Passthrough URL: `/pt/admin/odoo/` (standard trigger path)
- **UI:** Odoo Apps dashboard fully visible — purple Odoo chrome, search/filter (“1–55 / 55”), category sidebar, app grid (Sales, CRM, Invoicing, Website, etc.)
- **Containment:** Odoo renders cleanly inside the shell (no Nextcloud-style background leak in this view)
- **Regression claim:** Odoo handler and shim paths unchanged by Nextcloud commits; behavior matches pre-refactor expectations

---

## Result

**GREEN on first pass.** No code changes required for this certification.

---

## Notes

- Full module navigation (open Sales, CRM, etc.) can be extended in a later regression pass if desired; this bingo certifies the primary Apps shell load after the Nextcloud work landed.
- Nextcloud styling polish remains a separate follow-up item.
