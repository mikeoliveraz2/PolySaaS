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

- The `public` schema is for shared/global tables only:
  - `auth_user`
  - `dose_tenant`
  - `dose_userprofile`
  - `dose_usertenantmembership`
  - subscriptions and public site config
- Everything else lives in tenant-specific schemas.
- Admin `ModelAdmin` for user/tenant must force `public` schema.
- All other model admins must use `TenantAwareModelAdmin` and set `search_path` to the tenant schema.

## 3. General guardrails

- Do not create `.bak` files or temporary test files in source directories.
- Frozen files (`# THIS CODE IS FROZEN`) may not be changed without owner permission.
- Prefer minimal upstream fixes over downstream workarounds.
- For passthrough apps, route all asset URLs through the existing proxy; do not hotlink upstream hosts.

## 4. Orchestration Action Points

- An "Action Point" is an HTTP request (commonly a GET) where the user is expected to take an action.
- Instructions are matched and executed at Action Points using **only**:
  - `action_path`
  - HTTP `method` (GET, POST, PATCH, PUT, DELETE)
  - `direction` (request or response)
- Do not mutate the request or response to force an instruction match.
- No model or code changes are allowed to make an instruction match outside of `(action_path, method, direction)`.

## 5. Slack integration — API ONLY, except native sniff capture

- Default rule: Slack is **NOT** a passthrough app. Do **NOT** build scrapers, proxy `slack.com`, or put Slack in the PolySniffer workspace UI pane unless this is an explicit native-sniff capture flow for a signed-in browser session.
- Slack integration is API-only via a Slack App unless a dedicated native-sniff capture is intentionally requested for browser traffic capture.
- For native browser capture, PolySniffer may open the upstream Slack sign-in flow through its native sniff proxy, log the requests/responses to TrafficLog, and rewrite only the minimal asset/auth paths needed to keep the browser session stable; no Slack scraper UI or workspace embed is required.
- The next build target is the **inbound slash-command webhook** (`/hooks/slack/commands/`) that receives `/poly`, verifies the Slack Signing Secret, and acks.
- Only after the inbound webhook is wired should we add the Odoo write atomics (`OdooCreatePartner`, `OdooCreateSale`) and connect them through an Instruction.
- Posting back to Slack (`chat.postMessage`) is a later optional step — do not build it first.
