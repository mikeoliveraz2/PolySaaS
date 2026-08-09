# PolySniffer board handoff — 2026-08-09

## STATUS
- Step A DONE: PolySniffer unmounted from DOSE (`/dose/sniff/` include removed
  from `dose/urls.py`). Admin-only architecture test green.
- Locked architecture tests: 7 run, 3 pass, 4 intentional failures remain
  (endpoint IDs, Native rewrite import, legacy numeric happy-path tests).
- Board frozen except the single authorized step below.
- No isolation mechanism chosen. No Native rewrite work. No generator work.

## LOCKED RULES (non-negotiable)
1. PolySniffer exists ONLY in Admin — not DOSE, not `/pt/dose/`, not end-user PT.
2. Identity = endpoint string only (`PassThroughEndpoint.endpoint_url` / host).
   No endpoint ID in PolySniffer URLs, UI, session keys, capture names,
   commands, manifests, or tests as public identity. DB PKs internal only.
   `public` never participates in endpoint lookup, fallback, or merging. The
   eight bundled apps are valid only after their rows are copied into and
   owned by the tenant schema.
3. Native = raw: no production handler resolve, no processors, no HTML/string
   rewrite before capture. Learn then generate — not assume then navigate.
4. Viewport isolation required; mechanism UNDECIDED (not iframe by default).
5. Piccolo passo: one authorized change → validate → stop. No drive-by scope.

## WORKFLOW (the product contract)
1. Admin → PassThrough Endpoint row
2. Click PolySniffer
3. Workspace opens for THAT row’s `endpoint_url`
4. User navigates wherever they want
5. Capture browser traffic
6. Done

## AUTHORIZED NEXT STEP — B ONLY
Admin “PolySniffer” on the endpoint row opens the single workspace using
that row’s `endpoint_url`; user navigates and captures.

## IN SCOPE
- Smallest change so Admin click → workspace for clicked endpoint’s URL string
- Only what that open path strictly requires

## OUT OF SCOPE FOR B (do not do)
- 15-route host migration / comprehensive exploration plan
- Host→id translation layer as the design center
- Dual identity (keep id routes forever + host routes)
- Chrome extension, draft generation, frozen-file strategy rewrites
- Native rewrite removal, isolation/iframe/Playwright shell
- Template redesign

## DONE WHEN
- From Admin, click PolySniffer on an endpoint → workspace opens for that
  endpoint’s URL
- Files changed listed
- Locked architecture suite re-run; report pass/fail
- STOP — no further steps without new authorization

## REMAINING AFTER B (not authorized yet)
- Native purity (no rewrite on forward path)
- Isolation boundary (mechanism TBD by owner)
- Browser-level HAR (Playwright/CDP) when authorized
- Handler generation from selected Native session only
- Certify Odoo, then Zoho same workflow

Owner: Mike Oliver. Implementation peer must not expand scope.

_______________________________________________________________
The steps 1-7
**Anticipated Step B**

1. **Synchronize**
   - Pull `main`.
   - Confirm no newer handoff or conflicting work from Shela.

2. **Trace the existing Admin action**
   - Follow the “PolySniffer” link from the `PassThroughEndpoint` admin row to the workspace.
   - Identify the smallest remaining place where the database ID is used as public identity.

3. **Change the open path**
   - Build the Admin link from that row’s `endpoint_url` host.
   - Route using the endpoint host string, never the row ID or slug.
   - Resolve the exact endpoint inside the active tenant schema.
   - Return 404 for an unknown endpoint instead of falling back or translating to an ID.

4. **Open the existing workspace**
   - Supply the selected row’s unchanged `endpoint_url` to the current workspace.
   - Preserve the current workspace UI and navigation behavior.
   - Do not touch Native rewriting, isolation, capture generation, or unrelated routes.

5. **Add focused coverage**
   - Admin link contains the endpoint host, not its PK.
   - Clicking it opens the workspace for the correct `endpoint_url`.
   - Changing the row ID or slug does not change the link.
   - Unknown or cross-tenant endpoint hosts are rejected.

6. **Validate**
   - Run the focused Admin-to-workspace tests.
   - Run all seven locked architecture tests.
   - Report exactly which tests pass and which intentional failures remain.

7. **Hand back**
   - List changed files.
   - Update HANDOFF.md with Step B’s result.
   - Commit and push.
   - Stop before any next architectural step.