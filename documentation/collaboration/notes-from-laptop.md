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
