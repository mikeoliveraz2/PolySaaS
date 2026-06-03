# Post-Demo Render to GCP Cutover Plan

Date: 2026-06-03
Owner: PolySaaS platform team
Scope: Odoo, Nextcloud, Mattermost container workloads

## Intent

This plan defers infrastructure migration until after the demo and video capture, then moves bundled app workloads from Render to GCP in controlled phases with explicit rollback gates.

## Current-State Rule (Until Demo Completes)

1. Keep Render as production runtime for Odoo, Nextcloud, and Mattermost.
2. Allow only stability fixes that reduce demo risk.
3. Freeze contract surfaces now so migration does not require app behavior changes later:
   - Environment variable names
   - Passthrough trigger paths
   - Health endpoints
   - Callback/webhook URLs (where possible)

## Target-State Rule (After Demo)

1. Runtime shifts to GCP for Odoo, Nextcloud, and Mattermost containers.
2. Secret source of truth shifts to GCP Secret Manager.
3. Render remains available only as rollback runway until validation is complete.

## Migration Principles

1. One app at a time, never all three at once.
2. Blue/green style cutover with DNS or endpoint switch only after verification.
3. Keep rollback path pre-tested before each cutover.
4. No schema-destructive changes during migration windows.

## Proposed Sequence

1. Mattermost first
2. Nextcloud second
3. Odoo last

Reasoning:
1. Mattermost path and auth are currently high-touch and should be stabilized early in GCP.
2. Nextcloud has simpler passthrough requirements than Odoo.
3. Odoo is the most stateful and risky; migrate after patterns are proven.

## Phase 0 - Pre-Cutover Preparation

1. Confirm immutable image tags for each app.
2. Build and push images to Artifact Registry.
3. Create GCP runtime services and private networking.
4. Define secret sets in GCP Secret Manager using existing env key names.
5. Add runbooks for start, stop, health check, and rollback per app.

Exit criteria:
1. Services start in GCP with placeholder traffic.
2. Health checks pass in private test route.
3. Secret injection verified end-to-end.

## Phase 1 - Secret Management Transition

1. Set policy: Secret Manager is canonical.
2. Keep local .env for development only.
3. Use explicit manual publish for .env changes (no automatic write-back on every commit).
4. Keep encrypted .env.enc as fallback backup while transition is in progress.

Operational policy:
1. Pull path: Secret Manager to local .env.
2. Publish path: local .env to Secret Manager via approved allowlist and confirmation.
3. Audit path: store last sync timestamp and changed key names (values redacted).

## Phase 2 - Mattermost Cutover

1. Deploy Mattermost image in GCP.
2. Mirror required env vars and integration tokens from Secret Manager.
3. Validate passthrough paths and Team Not Found recovery behavior.
4. Validate bot/webhook dispatch and mention responses.
5. Switch endpoint to GCP and monitor.

Rollback trigger examples:
1. Passthrough auth loops or Team Not Found regression.
2. WebSocket instability above acceptable threshold.
3. Bot mention response failure in smoke test.

Rollback action:
1. Repoint endpoint back to Render target.
2. Keep GCP instance running for forensic logging.

## Phase 3 - Nextcloud Cutover

1. Deploy Nextcloud in GCP.
2. Verify endpoint scheme and passthrough behavior.
3. Validate login/session and file operations smoke test.
4. Switch endpoint to GCP.

Rollback trigger examples:
1. 502 or scheme mismatch behavior returns.
2. Auth/session persistence fails.

Rollback action:
1. Repoint endpoint back to Render.

## Phase 4 - Odoo Cutover

1. Deploy Odoo in GCP with matched DB/network assumptions.
2. Validate login flow, callback/orchestration paths, and key tenant actions.
3. Switch endpoint to GCP after successful smoke plus tenant verification.

Rollback trigger examples:
1. Login or route-render failures.
2. Tenant data access issues.
3. Callback/automation failures.

Rollback action:
1. Repoint endpoint back to Render.

## Validation Matrix (Per App)

1. Health endpoint green.
2. UI loads from passthrough trigger.
3. Login/auth succeeds.
4. Critical app workflow succeeds.
5. Logs show no sustained error bursts.
6. Synthetic smoke test passes twice (pre-switch and post-switch).

## Cutover Window Checklist

1. Change window opened.
2. Rollback owner assigned.
3. Monitoring dashboard open.
4. Baseline metrics captured.
5. Endpoint switch performed.
6. Post-switch smoke test completed.
7. Decision recorded: keep or rollback.

## Post-Cutover Stabilization

1. Keep Render instance idle but intact for defined fallback period.
2. Compare error rates, latency, and auth success against baseline.
3. Remove temporary debug flags introduced during cutover.
4. After stability period, retire Render services in reverse order of dependency.

## Deferred Work Notes

1. Do not execute this migration before the demo/video milestone is complete.
2. During demo period, focus only on reliability and deterministic behavior.
3. Update this document with actual service names, runbook links, and cutover timestamps once execution begins.
