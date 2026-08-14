# PolySniffer native-browser handoff

Date: 2026-08-14
Branch: cursor/polysniffer-switch-object-to-iframe

## Current status

The native browser route is registered and available in Django, but the live workspace is still loading the wrong endpoint context. The current app load is hitting endpoint id 6 in the active tenant schema, which is Dolibarr in the current test tenant, not Slack.

Observed evidence from the live Django request:

- Request: GET /dose/sniff/6/native/sign_in
- Result: HTTP 404
- Active schema log showed: "- Dolibarr: http://localhost:8083 (id: 6, enabled: True)"
- This route is therefore failing before Slack’s native browser handler can render.

## What is already fixed

- Slack native-sniff detection and handler registration were added.
- Slack native rewrite support was added for the native browser flow.
- The workspace shell launch URL generation was corrected to the native Sniff path pattern.
- The Slack endpoint row was created in the target schema for native sniff usage.
- The route pattern exists in [dose/polysniffer/sniff_urls.py](dose/polysniffer/sniff_urls.py).

## Remaining blocker

The active tenant/session is still bound to the wrong endpoint row. The browser is being launched against the wrong workspace endpoint, so the request never reaches Slack’s native browser flow.

To complete the fix, the next operator must ensure the workspace is pointed at the Slack endpoint in the correct tenant schema, or switch the current tenant/schema so the active endpoint id matches the Slack registration.

## Recommended next steps

1. Open the active PolySniffer workspace in the correct tenant/schema.
2. Verify that the selected endpoint is the Slack endpoint (or update the endpoint row in the current schema).
3. Re-run the workspace launch and confirm Start Native loads the browser pane without a 404.
4. Confirm Live capture records the first request after the page loads.

## Evidence and files

- [dose/polysniffer/sniff_urls.py](dose/polysniffer/sniff_urls.py)
- [dose/polysniffer/views/sniff_v2_workspace.py](dose/polysniffer/views/sniff_v2_workspace.py)
- [dose/templates/polysniffer/sniff_workspace.html](dose/templates/polysniffer/sniff_workspace.html)
- [dose/passthrough/handlers/slack_handler.py](dose/passthrough/handlers/slack_handler.py)
- [dose/polysniffer/handlers/slack_native_sniff.py](dose/polysniffer/handlers/slack_native_sniff.py)
- [dose/tests/test_slack_native_sniff.py](dose/tests/test_slack_native_sniff.py)

## Final note

This is a ready handoff: route registration and Slack-specific native handling are in place, but the final live validation remains blocked on endpoint context selection in the active tenant.
