# PolySaaS AI Rules

All AI assistants working on this repository MUST read this file before making changes, especially when touching passthrough, embedding, tenant, or admin code.

## 1. PolySniffer embedding — NO IFRAMES

- NEVER use `<iframe>` for PolySniffer passthrough or workspace embedding.
- Allowed approaches:
  1. Server-side inline HTML scoping/rewriting (preferred for passthrough content).
  2. `<object type="text/html">` only where the template already uses it.
- If an `<iframe>` seems unavoidable, STOP and ask the user for explicit permission before writing code.
- Before changing `sniff_workspace.html`, `sniff_pt_embed.py`, `sniff_urls.py`, or `sniff_v2_workspace.py`, re-read this rule and confirm the chosen approach.

## 2. PostgreSQL schema architecture

**HARD RULE (owner):** No tenant-owned data should ever be stored in `public`.
Do not reintroduce `tenant_id`-based multi-tenancy in shared tables. Isolation is
**schema-per-tenant**, not row-level filtering in `public`. See
`.cursor/rules/tenant-isolation.mdc` and `.cursor/rules/public-shared-data.mdc`.

- The `public` schema is for shared/global **system** tables only:
  - `auth_user`
  - `dose_tenant`
  - `dose_userprofile`
  - `dose_usertenantmembership`
  - subscriptions and public site config
- Everything else (PassThroughEndpoint, TenantApp, Instructions, mappings, logs,
  bookmarks, etc.) lives in tenant-specific schemas — never in `public`.
- Admin `ModelAdmin` for user/tenant must force `public` schema.
- All other model admins must use `TenantAwareModelAdmin` and set `search_path` to the tenant schema.
- Never leave `search_path` on `public`-only before querying tenant-owned models
  (e.g. on `/pt/admin/<slug>/`). Restore `"<tenant>", public` after any temporary
  switch to `public`.

## 3. General guardrails

- Do not create `.bak` files or temporary test files in source directories.
- Frozen files (`# THIS CODE IS FROZEN`) may not be changed without owner permission.
- Prefer minimal upstream fixes over downstream workarounds.
- For passthrough apps, route all asset URLs through the existing proxy; do not hotlink upstream hosts.

## 4. Orchestration Action Points

- Every orchestration starts with a trigger. Nothing runs without a user or system action.
- In scraper/path mode, PolySaaS observes the triggering HTTP request directly through passthrough.
- In webhook/API mode, the external system observes its UI or API action and forwards that trigger to PolySaaS. Webhooks deliver triggers; they do not invent them.
- An outbound API call is made by an already-running Instruction; its response is a result, not a new spontaneous trigger.
- The orchestration bar is the shared feedback surface for progress, success, and failure from passthrough, webhook, and outbound API flows.
- An `action_path` may be a real captured/proxied HTTP path or a normalized logical event key for a forwarded webhook/API trigger.
- Instructions are matched and executed at Action Points using **only**:
  - `action_path`
  - HTTP `method` (GET, POST, PATCH, PUT, DELETE)
  - `direction` (request or response)
- Do not mutate the request or response to force an instruction match.
- No model or code changes are allowed to make an instruction match outside of `(action_path, method, direction)`.

## 5. Slack integration — API-first production + Native sniff discovery

- **Production orchestration:** Slack is API-first (slash command / webhooks → mailbox → consumer). See `documentation/POLYSAAS_ORCHESTRATION_MODEL.md`. Do not treat production Slack as a finished passthrough product.
- **Product UI:** Slack uses a PolySaaS-owned mock/bookmark home and opens real
  Slack in a normal top-level browser. Production must not depend on rendering
  the complete Slack SPA through PolySaaS.
- **PolySniffer Native (discovery):** Native remains a specialized forwarder/HAR
  tool where capture is supported. It is not the default Slack or vendor-SaaS
  product surface.
- Inbound `/hooks/slack/commands/` (`/poly`) remains the production trigger path.

## 6. UI and navigation

- Governing document:
  `documentation/POLYSAAS_UI_NAVIGATION_AND_EVENTS.md`.
- Primary UI for every endpoint: PolySaaS mock/screenshot surface + bookmarks.
- Secondary UI: unchanged real application in a normal top-level browser.
- Native/passthrough remain specialized discovery/validation tools.
- Bookmark actions must be declarative and allowlisted. Never store executable
  JavaScript or unrestricted absolute URLs. Real-app URLs may use only the
  endpoint's configured host and HTTP(S) policy.
- Browser-facing endpoint homes use the exact endpoint host resolved in the
  active tenant schema. Database row IDs are internal only.
- Tenant-owned bookmarks, events, and results live only in the active tenant
  schema; never silently fall back to `public`.
