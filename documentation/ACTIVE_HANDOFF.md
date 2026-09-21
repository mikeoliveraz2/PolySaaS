# Active Handoff

This file is the canonical startup and end-of-day handoff.
Every agent must read this file before editing or answering.

**Date:** 2026-09-21 (Monday)
**Session:** Captured Topics missing on Hostinger — Docker fix
**Branch:** main

## Root cause
`Dockerfile.django` did not `COPY captured_topics`, so Hostinger never installed the app.
Jazzmin hid `dose.webhookmailbox`, so Captured Topics vanished entirely from Admin.

## Fix
- `Dockerfile.django` now copies `captured_topics/`.
- Rebuild/redeploy Django image, then `migrate` (proxy migration).

## Expected Admin
After rebuild: sidebar section **Captured Topics** immediately after **Authentication and Authorization**.
