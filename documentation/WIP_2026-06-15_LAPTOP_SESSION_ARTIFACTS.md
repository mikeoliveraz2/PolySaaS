# WIP — Laptop Session Artifacts (2026-06-15)

**Status:** Work in progress — not certified, not BINGO.  
**Purpose:** Preserve diagnostic scripts, HAR compare tooling, and local backups from the polysaasppd / Mattermost passthrough session. Safe to delete after office merge if redundant.

---

## Contents

| Path | WIP purpose |
|------|-------------|
| `scripts/_check_ppd_tenant.py` | DB sanity check: Instructions, CallBackData, TenantApp for `polysaasppd` |
| `scripts/_check_instruction_schema.py` | Inspect `tenant_slug` column types per schema |
| `scripts/_check_schema_tables.py` | List `dose_*` tables in tenant schema |
| `scripts/_fix_ppd_instructions.py` | One-off: delete public mis-placed Instructions + re-provision in tenant schema |
| `scripts/_har_compare_once.py` | Single-run HAR comparison helper |
| `scripts/compare_hars.py` | Compare Team Not Found vs BINGO HARs from agent transcript |
| `har_teamnotfound_vs_bingo.txt` | Captured output / error log from HAR compare attempt |
| `mattermost-passthrough-plugin/server/main.go.bak` | Local backup before Mattermost plugin edits |
| `scripts/eod/Eod-EveningSync.ps1.bak2` | EOD script backup (office sync) |
| `scripts/eod/Eod-Services.ps1.bak` | EOD script backup |

---

## Do not treat as production

- Scripts may hardcode tenant slugs, paths, or machine-specific transcript locations.
- HAR tooling expects Cursor agent transcript JSONL format.
- Plugin `.bak` is not the authoritative plugin source.

---

## Related certified work (see session handoff)

Production fixes landed separately on `main`:

- `documentation/SESSION_HANDOFF_2026-06-15_POLYSAASPPD_SUBSCRIBE_ORCHESTRATION.md`
- Commits `1b80079d` through `b0f9763c`
