# Active Handoff

This file is the canonical startup and end-of-day handoff for PolySaaS.
Every agent (Copilot, Cursor, Windsurf) must read it before work and update it at EOD.

**Date:** 2026-09-10 (Thursday)  
**Session:** DigitalOcean deploy package (phase 1 core stack)  
**Branch:** main  
**Latest commit:** `09b5904e` (+ follow-up Traefik tlsChallenge / bringup `.env` source)

## Completed (repo)

- `deploy/digitalocean/` Compose: Traefik + Django + mailbox-consumer + core Postgres + Redis + Mattermost + Odoo
- Scripts: provision (doctl), bootstrap, bringup, DNS checklist, dump/migrate, retarget, smoke
- Runbook: `documentation/deployment/DIGITALOCEAN_DEPLOY_RUNBOOK.md`
- Hostnames: `app` / `mm` / `odoo`.polysaas.online (apex WordPress unchanged)
- Pushed to `origin/main` so droplet bootstrap can `git clone` / `git pull`

## Blocked on operator (live cloud)

No `DIGITALOCEAN_ACCESS_TOKEN` / `DO_SSH_KEY_FINGERPRINT` in this environment — cannot create Droplet, DNS, bring-up, restore, or smoke against production yet.

```powershell
$env:DIGITALOCEAN_ACCESS_TOKEN = "dop_v1_..."
$env:DO_SSH_KEY_FINGERPRINT = "..."   # doctl compute ssh-key list
$env:DO_REGION = "sgp1"
.\deploy\digitalocean\scripts\provision-droplet.ps1
```

Then runbook §§2–7 (bootstrap → DNS → bringup → migrate → smoke).

## Prior bingo still valid

- Slack / Mattermost / HubSpot → Odoo contacts (`newpolysaascontact` + HubSpot FlowLink)
- Latest HubSpot bingo: `11a0d627`

## Next

1. Michael: paste DO token + SSH key fingerprint (or set env vars) so agent can finish provision→smoke  
2. DNS A records → floating IP  
3. `bringup.sh` + migrate demo dumps  
4. Retarget Slack/HubSpot webhooks to `https://app.polysaas.online/...`
