# Active Handoff

This file is the canonical startup and end-of-day handoff for PolySaaS.
Every agent (Copilot, Cursor, Windsurf) must read it before work and update it at EOD.

**Date:** 2026-09-10 (Thursday)  
**Session:** DigitalOcean deploy package (phase 1 core stack)  
**Branch:** main

## Completed

- Added `deploy/digitalocean/` production Compose stack: Traefik + Django + mailbox-consumer + core Postgres + Redis + Mattermost + Odoo
- Scripts: provision (doctl), bootstrap droplet, bringup, DNS checklist, dump/migrate, smoke
- Runbook: `documentation/deployment/DIGITALOCEAN_DEPLOY_RUNBOOK.md`
- Hostnames: `app` / `mm` / `odoo`.polysaas.online (apex WordPress unchanged)

## Blocked on operator

Live Droplet create needs `DIGITALOCEAN_ACCESS_TOKEN` + SSH key fingerprint (not present on this machine). Run:

```powershell
$env:DIGITALOCEAN_ACCESS_TOKEN = "dop_v1_..."
$env:DO_SSH_KEY_FINGERPRINT = "..."
.\deploy\digitalocean\scripts\provision-droplet.ps1
```

Then follow the runbook steps 2–7.

## Prior bingo still valid

- Slack / Mattermost / HubSpot → Odoo contacts (`newpolysaascontact` + HubSpot FlowLink)
- Latest HubSpot bingo: `11a0d627`

## Next

1. Provision DO droplet with token  
2. DNS A records → floating IP  
3. `bringup.sh` + migrate demo dumps  
4. Retarget Slack/HubSpot webhooks to `https://app.polysaas.online/...`
