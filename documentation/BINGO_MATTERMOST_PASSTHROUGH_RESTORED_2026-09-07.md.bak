<!-- THIS CODE IS FROZEN — NO CHANGES TO THIS CODE ARE ALLOWED WITHOUT THE OWNER'S PERMISSION -->
<!-- BINGO: Mattermost passthrough restored — PolySaaSOline Town Square — 2026-09-07 -->

# BINGO: Mattermost Passthrough Restored — Town Square Working

**Date:** 2026-09-07  
**Verified by:** Michael (live browser, tenant PolySaaSOline / michael.oliver)  
**Branch:** `cursor/polysniffer-slack-native-capture`  
**Commit:** *(filled after commit)*

## What this certifies

Mattermost passthrough loads Town Square again under the PolySaaS admin shell for tenant **PolySaaSOline**:

- URL: `/pt/admin/mattermost/` → `/pt/admin/mattermost/polysaas-team/channels/town-square`
- Early fetch guard v37 + display shim (`2026-06-12-theme-sync`) both run
- Channel UI + Town Square + Mattermost onboarding modal render
- Orchestration bar: `Action Path: /polysaas-team/channels/town-square`

This is a restore of BINGO `8100b79a` (2026-08-02 slug identity + SSO), not a new passthrough design.

## What broke it (do not reintroduce)

1. **Aug 8 hostname lookup** (`d7981e58`) replaced slug resolution with `endpoint_url` host matching. `/pt/admin/mattermost/` then 404'd.
2. **Stale token on the wrong tenant.** Fresh PAT was written to tenant `polysaas`. The logged-in tenant is `polysaasonline` (PolySaaSOline), which still had expired `ebojaniy…`.
3. **Landing team slug did not exist.** `mm_shared_team_name=polysaas-dev-team` → Mattermost “Team Not Found”. This user is on `polysaas-team` only.
4. **Parallel MM→Odoo producer work** chased handler/shim fixes. Slack → Odoo (`e9f5f20f`) was never the failure.

## Restore

| Item | Action |
|------|--------|
| `dose/passthrough/handlers/mattermost_handler.py` | Restored from `8100b79a` |
| `dose/passthrough/middleware.py` | Restored from `8100b79a` (slug `__iexact` + legacy hostname 302) |
| TenantApp `polysaasonline` Mattermost `extra_config` | Valid PAT on **this** tenant; `mm_shared_team_name` / `mm_team_name` = `polysaas-team` |

## Not in this BINGO

- Slack → Odoo contact flow (`e9f5f20f`) — already frozen, unchanged
- Mattermost outgoing webhook → same Slack topic — next session, after this freeze

## Files in this commit

| Path | Role |
|------|------|
| `dose/passthrough/handlers/mattermost_handler.py` | BINGO handler restore + 2026-09-07 freeze |
| `dose/passthrough/middleware.py` | Slug lookup restore + 2026-09-07 freeze |
| `documentation/BINGO_MATTERMOST_PASSTHROUGH_RESTORED_2026-09-07.md` | This certification |
| `documentation/ACTIVE_HANDOFF.md` | Session handoff |

## Freeze

```
THIS CODE IS FROZEN — NO CHANGES TO THIS CODE ARE ALLOWED WITHOUT THE OWNER'S PERMISSION
```

No handler/middleware edits without Michael or Shela.
