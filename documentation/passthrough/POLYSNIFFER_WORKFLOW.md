# PolySniffer Workflow

**Owners:** Michael and Shela  
**Updated:** 2026-08-09  
**Status:** Architecture Steps 0-6 implemented; Odoo certification not yet started

## Identity Boundary

PolySniffer and production passthrough routing never use a database ID:

```text
/pt/admin/<endpoint-host>/<path>
```

The unique tenant `PassThroughEndpoint.endpoint_url` supplies `<endpoint-host>`
and the upstream origin. An integer ID, offset, slug, or trigger must never be
accepted as production passthrough identity.

PolySniffer has one canonical, admin-only screen keyed by endpoint host:

```text
/dose/sniff/<endpoint-host>/?schema=<tenant-schema>
```

Exactly two buttons open this same screen: one in the Passthrough Endpoint list
and one on the endpoint edit-details page. There is no separate PolySniffer
screen or route for either button. The entry identity is `(tenant schema,
endpoint host)`. Once the entry resolves, PolySniffer binds the request and
session to that tenant.
An explicit invalid schema or missing endpoint returns `404`; it never falls
back to the active session tenant.

## Fixed Workspace

Every endpoint and both modes use the same PolySniffer control screen:

- One toolbar and mode selector.
- Top-level application browser navigation; no iframe.
- One directly rendered capture panel.
- No endpoint-specific workspace template or layout branch.
- No upstream `<head>`, CSS, scripts, or body inserted into the tool document.

Endpoint content never enters the PolySniffer document. Applications that set
`X-Frame-Options` or CSP `frame-ancestors` therefore work normally. The external
host sees an ordinary top-level browser. Native evidence comes from Playwright
HAR and CDP, not injected JavaScript, a PolySaaS Native proxy, or rewritten HTML.

## The Two Modes

### Native

Native establishes the evidence baseline. It must:

1. Open the selected tenant endpoint's unchanged `endpoint_url` directly in a
   top-level browser page.
2. Begin at that row's `starting_uri` only.
3. Send the requested URL without endpoint-specific mutation.
4. Preserve upstream body and redirect location values.
5. Avoid the production handler registry, processors, orchestration, and string
   replacement.
6. Associate observations with the selected Native capture session.

Native does not prove passthrough correctness. It records what the real
application does before PolySaaS interpretation.

### Passthrough

Passthrough is the comparison branch. It must:

1. Resolve the installed handler from the exact tenant endpoint row.
2. Exercise only the real endpoint-host `/pt/admin/` route.
3. Apply handler rewriting, authentication, cookies, and orchestration only in
   this branch.
4. Record its own capture source so Native and Passthrough can be compared.

Native behavior must never be copied into Passthrough as an app-specific
shortcut, and Passthrough behavior must never leak backward into Native.

The shared control screen opens Passthrough as a top-level browser page on the real
`/pt/admin/<endpoint-host>/<starting_uri>` route. It does not use
`/pt/polysniff/` or `/pt/dose/`. The
workspace shell does not resolve a handler; the production host route performs
the exact tenant endpoint lookup and installed-handler resolution.

## Handler Workflow

For each external application:

1. Add its unique `PassThroughEndpoint` row in the owning tenant schema.
2. Open PolySniffer from either admin button. Confirm both open the same URL
   containing the endpoint host and `schema=<tenant-schema>`, with no ID.
3. Start a new Native capture session.
4. Navigate the application and complete the representative login and business
   workflow without a production handler or string replacement.
5. Stop and select that exact completed Native session.
6. Generate a handler **draft** from only that session.
7. Review the draft. Generation must never register or overwrite a handler
   silently.
8. Install the reviewed handler.
9. Run the Passthrough branch through the real endpoint-host routes.
10. Compare Native and Passthrough requests, redirects, cookies, response
    families, and visible behavior.

## Handler Draft Generation

Generation requires one explicit, completed Native capture session. The
control screen displays its capture-session ID while recording; that number
identifies the evidence session, not the endpoint. The admin endpoint's
**Generate Handler Draft** action asks for the ID and rejects active,
Passthrough, missing, or endpoint-mismatched sessions.

The analyzer reads only `TrafficLog` rows whose `capture_session` is that exact
session and whose `capture_source` is `native`. It does not search by URL,
endpoint label, substring, most-recent session, or any other fuzzy fallback.

Generated passthrough prefixes come from the unique endpoint host:

```text
/pt/admin/<endpoint-host>/
```

The response includes the tenant schema, endpoint host and URL, capture-session
ID and name, analysis, and Python code. The result has `draft` status and opens
for review. Generation does not update `discovered_subpaths`, write a handler
file, register a class, overwrite an installed handler, or otherwise affect
production routing. Installation remains a separate reviewed action during
Odoo certification.

Browser-level Playwright/CDP capture is required before this workflow is
certified. Python `requests` traffic is not a substitute for browser HAR.
WebSocket handshakes and frames must be recorded as separate evidence because
standard HAR does not fully represent WebSocket traffic.

## Browser Evidence Capture

Step 5 uses Chromium through Playwright. It records HTTP traffic with the
browser context's HAR recorder and subscribes to Chrome DevTools Protocol
`Network.webSocket*` events. The WebSocket event stream is written to a
separate JSON file and is never inserted into the HAR.

Install Chromium once for the active virtual environment:

```powershell
.\venv\Scripts\python.exe -m playwright install chromium
```

Create authenticated PolySaaS browser state. Sign in as the staff user in the
opened browser, then close it:

```powershell
.\venv\Scripts\playwright.exe codegen `
   --save-storage=polysniffer-auth.json `
   http://127.0.0.1:8000/admin/login/
```

Start the Native session in the invariant workspace and use the returned
capture ID explicitly:

```powershell
.\venv\Scripts\python.exe manage.py capture_polysniffer_browser `
   --schema <tenant-schema> `
   --endpoint-host <endpoint-host> `
   --capture-session-id <native-capture-id> `
   --mode native `
   --storage-state polysniffer-auth.json `
   --headed `
   --duration 120
```

After the reviewed handler is installed, start a separate Passthrough session
and run the same command with its own capture ID and `--mode passthrough`.
Native opens the unchanged external `endpoint_url` directly; Passthrough opens
the real `/pt/admin/<endpoint-host>/...` route. Neither mode uses an iframe.

Each run emits three files under `polysniffer_evidence/`:

- `*.har`: HTTP browser evidence generated by Playwright.
- `*.websockets.json`: CDP WebSocket handshakes, frames, closes, and errors.
- `*.manifest.json`: tenant schema, endpoint host and URL, explicit capture ID,
   mode, application URL, artifact paths, and WebSocket event count.

The command requires the selected capture to remain active. Before navigation,
it binds the authenticated Django browser session to that explicit capture ID
and mode so browser HAR evidence and server-side observations cannot drift into
different sessions. It fails closed when the tenant, endpoint, capture session,
mode, authentication file, or Django session cookie does not match. The
authentication state file can contain live cookies and must not be committed.

## Odoo Certification Gate

Odoo is the baseline and must be completed before any Zoho onboarding.

Certification evidence must include:

- Screenshot of the invariant workspace before either mode starts.
- Screenshot of Odoo in Native with the same workspace chrome visible.
- Selected Native browser HAR and capture-session identifier.
- Reviewed generated-handler draft tied to that exact Native session.
- Screenshot and capture evidence for `/pt/admin/<odoo-host>/...`.
- Native/Passthrough comparison showing expected URL, cookie, redirect, and
  protocol behavior.
- Passing architecture and Odoo regression tests.

After Michael and Shela accept that evidence, freeze it as the PolySniffer Odoo
baseline.

## Zoho Gate

Do not begin Zoho until the Odoo baseline is frozen. Zoho must follow the same
steps with no endpoint-specific workspace, Native processor, manual capture
selection shortcut, fuzzy traffic lookup, or silent handler installation.

## Implementation Progress

- **Step 0:** Architecture contracts added.
- **Step 1:** Shared iframe-free admin control screen complete.
- **Step 2:** Native raw path complete.
- **Step 3:** Schema plus endpoint-host entry binding complete.
- **Step 4:** Passthrough-only production host-route boundary complete.
- **Step 5:** Browser-level Playwright HAR plus separate CDP WebSocket evidence complete.
- **Step 6:** Exact completed-Native-session handler draft generation complete.
- **Step 7:** Odoo certification pending.
- **Step 8:** Zoho onboarding blocked by the Odoo gate.