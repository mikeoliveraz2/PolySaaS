---
description: Mattermost passthrough login working inside PolySaaS admin
---

# BINGO: Mattermost Passthrough Login Working

**Date**: 2026-05-06
**Status**: DONE
**Branch**: main
**Location**: Condo → Office

## What Was Done

- Recovered Mattermost admin access via direct login with `mikeoliveraz` / `PolySaaS2026!`
- Verified Mattermost passthrough proxy is functional end-to-end
- Created Django superuser `mmadmin@polysaas.online` / `PolySaaS2026!`

## Verification

Clicking "Mattermost" in the PolySaaS admin sidebar loads the full Mattermost UI:
- Town Square renders
- Channels sidebar visible
- Direct messages work
- Static assets load through `/pt/admin/mattermost/static/...` proxy
- API calls route through proxy correctly

## Known Non-Blocking Issues

| Issue | Impact | Notes |
|-------|--------|-------|
| WebSocket "unreachable" banner | Cosmetic | Render free tier doesn't support WS; MM falls back to HTTP polling |
| Plugin bundles 404 | Non-critical | github, playbooks, nps, calls plugins don't load; core chat works |
| External telemetry CORS | None | `pdat.matterlytics.com` blocked by CORS; unrelated to passthrough |

## Pending for Future Sessions

- Auto-login via `MMAUTHTOKEN` injection (needs tenant app `extra_config`)
- Fix plugin static asset routing through proxy
- WebSocket passthrough support

## Files Changed

- `documentation/COORDINATION_README.md`
- `documentation/BINGO_Mattermost-Passthrough-Working.md` (this file)

## Follow-ups

- Test on desktop in office (already synced to GitHub)
