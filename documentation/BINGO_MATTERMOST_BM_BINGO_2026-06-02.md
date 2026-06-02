# BINGO: Mattermost BM Checkpoint

Date: 2026-06-02
Status: COMPLETE
Branch: main

## Objective

Create a full Mattermost passthrough checkpoint that is safe to revert to later, with all current working-tree changes committed together and documented.

## What Was Included

1. Mattermost passthrough hardening and login-flow ownership in `dose/passthrough/handlers/mattermost_handler.py`.
2. Passthrough endpoint URL scheme inference fix for internal `:80` services in `dose/passthrough/middleware.py`.
3. Controller logging normalization updates in `dose/doserequestcontroller.py`.
4. Baseline BOM and checkpoint documentation updates.
5. Current HAR capture and handler snapshot artifacts:
   - `docs/temp_har.txt`
   - `dose/passthrough/handlers/mattermost_handler.py.current`

## Mattermost Functional Changes

1. PolySaaS bridge now owns passthrough `/login` routes server-side.
2. Upstream native login HTML is redirected to the PolySaaS bridge.
3. Team Not Found HTML is intercepted and redirected to passthrough root.
4. Root redirects were neutralized to `/` instead of forced team/channel paths.
5. IndexedDB persist payload writes are defensive for string-serialized nested slices.

## Non-Mattermost Supporting Changes

1. Passthrough trigger URL construction now infers `http://` for internal hostnames and explicit `:80`.
2. Request controller debug output moved from `print` to logger calls for cleaner runtime logs.

## Revert Guidance

Use this commit as the baseline restore point.

1. Find this commit by message:
   - `BINGO: Mattermost BM checkpoint`
2. Revert to this state later with:
   - `git revert <commit_hash>` (safe reverse)
   - or `git checkout <commit_hash>` (detached historical inspection)

## Verification Notes

1. Mattermost passthrough renders in admin embed and reaches Town Square.
2. NextCloud passthrough endpoint `polysaas-nextcloud:80` now targets `http://polysaas-nextcloud:80`.
3. Team Not Found fallback protection is in place server-side.
