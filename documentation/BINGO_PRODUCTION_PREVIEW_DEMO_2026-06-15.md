# BINGO — Production Preview Demo (AI Peers + Orchestration + Subscribe)

**Date:** 2026-06-15  
**Declared by:** Michael  
**Commit:** `55ce3402`  
**Baseline:** `783f7fbe` — Odoo invoicing menu-id-only GET instruction  
**Demo tenants:** `polysaasppy`, `polysaasppx`, `polysaasppv2`, `polysaasppd`  
**Services:** `.\runall.ps1` (Waitress + `run_mattermost_bot`)

---

## What Was Achieved

Production Preview video demo: Mattermost AI peers respond in shared Town Square, Odoo invoicing produces **one** CallBackData row per visit, and subscribe reports provisioning failures honestly.

### Certified behaviors

| Feature | Status |
|---------|--------|
| AI peers @grok @gemini @copilot in **PolySaaS-Dev-Team / Town Square** | ✓ |
| WebSocket bot dispatches without blocking asyncio loop (threaded `_dispatch`) | ✓ |
| New subscribers land on **shared** Town Square (`last/team` + `last/channel` prefs) | ✓ |
| `add_bots_to_all_tenants` syncs bots + landing prefs on `runall` | ✓ |
| Mattermost provision **fails** if MM user cannot be created/linked (no false “ready”) | ✓ |
| Subscribe API returns `provisioning_results` + error styling in UI | ✓ |
| Email-already-exists → link existing MM user by email | ✓ |
| Odoo Invoicing: **one** `odoo_invoicing_viewed` CallBackData per navigation | ✓ |
| Duplicate/orphan Instructions pruned on orchestration provision | ✓ |
| `TenantApp` not marked active without `mm_user_id` | ✓ |

---

## Root Causes Fixed

| Symptom | Fix |
|---------|-----|
| Bots silent despite “bot running” | Expired `BOT_TOKEN_*` (401 on post); regenerate via `setup_demo_mattermost_peers` |
| Bot received WS events but never replied | `_on_event` blocked asyncio loop; dispatch moved to background thread |
| Users on private Town Square (no bots) | Shared-team landing prefs + passthrough opens `polysaas-dev-team` |
| Subscribe said apps ready when MM user missing | `provision_mattermost_tenant` returns `success: False`; subscribe surfaces error |
| Two CallBackData rows for one Invoicing visit | Unified `odoo:accounting` action gate + `eventKey` dedupe; prune duplicate Instructions |
| Wrong-tenant Instructions in tenant schema | `_prune_duplicate_invoicing_instructions` removes bleed + duplicates |

---

## Files in This BINGO

| File | Change |
|------|--------|
| `dose/mattermost_bot/bot.py` | Threaded WebSocket `_dispatch` |
| `dose/services/mattermost_tenant_provisioner.py` | Shared landing prefs, email link, fail without user, `_store_credentials` gate |
| `dose/management/commands/add_bots_to_all_tenants.py` | Landing sync after bot roster |
| `dose/subscription_views.py` | `provisioning_results` in API; honest success/failure messages |
| `dose/templates/dose/subscribe.html` | Show provisioning notice + error styling |
| `dose/passthrough/orchestration_hook.py` | `eventKey` dedupe; unified `odoo:accounting` action path |
| `dose/services/odoo_orchestration_provisioner.py` | Prune duplicate/wrong-tenant invoicing Instructions |

---

## Operator Checklist (before recording)

1. `.\runall.ps1` — confirm `[OK] AI Peers bot`
2. Verify bot tokens (must not 401):
   ```powershell
   python manage.py setup_demo_mattermost_peers --team=polysaas-dev-team --no-welcome
   ```
   Update `.env` / Secret Manager with printed `BOT_TOKEN_*` values; restart `runall`.
3. Login as demo tenant → Mattermost sidebar → **PolySaaS-Dev-Team / Town Square**
4. `@grok ping` or `@gemini ping` — reply within ~10s
5. Odoo Invoicing → **one** CallBackData row for `odoo_invoicing_viewed`

---

## Token / env note

Bot PATs are **not** in git. After MM server token rotation, re-run `setup_demo_mattermost_peers` and refresh `BOT_TOKEN_GEMINI`, `BOT_TOKEN_SUPERGROK`, `BOT_TOKEN_COPILOT` in `.env` or Secret Manager.
