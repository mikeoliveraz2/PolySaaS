# PolySaaS daily handoff

Updated: 2026-08-15
Branch: `cursor/polysniffer-switch-object-to-iframe`
Status: WIP, not validated end to end

## Why this file exists

The 2026-08-14 end-of-day commit did not include all WIP in one canonical
handoff, which prevented a clean continuation from another computer. This file
is now the only active handoff. Git history preserves prior states; do not
create parallel dated or task-specific handoff files.

## Current objective

Run Slack's sign-in flow through a native PolySniffer browser capture so its
requests and responses are recorded. This is an explicitly authorized
native-sniff exception to the default Slack API-only rule in `AI_RULES.md`.

## Current state

- Slack handler detection and native-sniff rewrite code were added in commit
  `91fd6ffc`.
- Workspace native launch generation was changed to use
  `/dose/sniff/<endpoint-id>/native/...`.
- A staff-side request to `/dose/sniff/6/native/sign_in` returned HTTP 404.
- In the active `t104` tenant schema, endpoint ID 6 resolved to Dolibarr at
  `http://localhost:8083`, not Slack.
- The branch and remote were compared after fetch on 2026-08-15 and were
  `0` ahead / `0` behind before today's documentation edits.
- The worktree contains substantial unrelated WIP and `.bak`/temporary files.
  Preserve all of it for the end-of-day synchronization; do not discard it.

## Architecture issue discovered

The Slack WIP was committed without updating or reading the previous canonical
handoff. That handoff documented a locked host-identified Admin-only
PolySniffer architecture with raw Native capture and no `/dose/sniff/`
happy-path route. Commit `91fd6ffc` introduced endpoint-ID native routing and
Slack response rewriting, so it conflicts with that recorded architecture.

Do not treat the HTTP 404 as merely a missing Slack row until this conflict is
resolved. The next implementation must either:

1. adapt the Slack capture to the host-identified Admin-only/raw-Native
   architecture; or
2. obtain an explicit owner decision superseding those architecture rules and
   document that decision here before changing code.

## Next step

Trace the currently active Admin PolySniffer route and session identity from
the endpoint-row action through the workspace launch. Determine the smallest
way to run the authorized Slack native capture while preserving host identity,
tenant-schema isolation, and the no-iframe rule. Validate the exact route with
the correct tenant and endpoint host before editing production code.

## Relevant files

- `AI_RULES.md`
- `.github/copilot-instructions.md`
- `dose/passthrough/handlers/slack_handler.py`
- `dose/polysniffer/handlers/slack_native_sniff.py`
- `dose/polysniffer/views/sniff_v2_workspace.py`
- `dose/templates/polysniffer/sniff_workspace.html`
- `dose/tests/test_slack_native_sniff.py`

## Daily synchronization contract

At the start of each workday, fetch/pull the active branch and read this file
before implementation. At the end of each workday, update this file, commit all
WIP (including incomplete and unvalidated work), and push the active branch.
This is the only active handoff file; Git history is the archive.
