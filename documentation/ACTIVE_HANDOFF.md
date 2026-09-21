# Active Handoff

This file is the canonical startup and end-of-day handoff.
Every agent must read this file before editing or answering.

**Date:** 2026-09-22 (Tuesday)  
**Session:** Slack + HubSpot PassThroughEndpoint setup (not install)  
**Branch:** main  

## Clarification

Capture contacts does **not** install Slack/HubSpot. Setup = tenant-schema **PassThroughEndpoint** rows with SaaS URLs so Control Panel appears, plus credentials on **TenantApp**.

## Done

- Extended `setup_default_passthrough_endpoints` with:
  - `--hubspot-url` default `https://app.hubspot.com`
  - `--slack-url` default `https://app.slack.com`
- Capture contacts actions already on all four apps (`cfb7fa1e`)

## Run per tenant

```text
python manage.py setup_default_passthrough_endpoints --tenant-slug polysaasonline
python manage.py setup_default_passthrough_endpoints --tenant-slug olient
```

(Use the actual Tenant.slug values for `polysaas` / `olient` schemas.)

## Credentials still required for Capture

| App | Needs |
|-----|--------|
| HubSpot | OAuth on TenantApp (`hs_access_token`) |
| Slack | `TenantApp.extra_config.bot_token` (xoxb-…) with users:read |

## Next

1. Run setup command on target tenants
2. Smoke-test Capture contacts from each Control Panel
3. Type 2 SNMP video
