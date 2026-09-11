# Active Handoff

This file is the canonical startup and end-of-day handoff for PolySaaS.
Every agent (Copilot, Cursor, Windsurf) must read it before work and update it at EOD.

**Date:** 2026-09-11 (Friday)  
**Session:** Hostinger VPS deploy package (phase 1 core stack)  
**Branch:** main  
**Latest commit:** `54773689`

## Completed (repo)

- Production target pivoted to **Hostinger KVM 4** VPS (DigitalOcean / AWS parked)
- Added [`deploy/hostinger/`](../deploy/hostinger/): Traefik + Django + mailbox-consumer + core Postgres + Redis + Mattermost + Odoo
- Scripts: `provision-vps.ps1` (hPanel checklist), `bootstrap-vps.sh`, bringup, DNS, dump/migrate, retarget, smoke
- Runbook: [`documentation/deployment/HOSTINGER_DEPLOY_RUNBOOK.md`](deployment/HOSTINGER_DEPLOY_RUNBOOK.md)
- Hostnames unchanged: `app` / `mm` / `odoo`.polysaas.online (apex WordPress unchanged)
- `Dockerfile.django` entrypoint now copies `deploy/hostinger/entrypoint-django.sh`
- Cost budget: ~$13/mo intro / ~$29/mo renewal for KVM 4 (+ free weekly backups)

## Operator next (live Hostinger)

1. Order KVM 4 + Ubuntu Docker template — run `.\deploy\hostinger\scripts\provision-vps.ps1`
2. SSH → `bootstrap-vps.sh` → fill `.env`
3. DNS A records `app`/`mm`/`odoo` → VPS IP
4. `bringup.sh` → migrate dumps → retarget Slack/HubSpot → `smoke-test.sh`
5. Update this handoff with **VPS_IP**, region, and snapshot date

## Prior bingo still valid

- Slack / Mattermost / HubSpot → Odoo contacts (`newpolysaascontact` + HubSpot FlowLink)
- Latest HubSpot bingo: `11a0d627`
- `deploy/digitalocean/` remains in repo as historical only

## Parked

- DigitalOcean live provision (token friction)
- AWS exploration (superseded by Hostinger)
