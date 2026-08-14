# PolySaaS AI Rules

All AI assistants working on this repository MUST read this file before making changes, especially when touching passthrough, embedding, tenant, or admin code.

## 1. PolySniffer embedding — NO IFRAMES

- NEVER use `<iframe>` for PolySniffer passthrough or workspace embedding.
- Allowed approaches:
  1. Server-side inline HTML scoping/rewriting (preferred for passthrough content).
  2. `<object type="text/html">` only where the template already uses it.
- If an `<iframe>` seems unavoidable, STOP and ask the user for explicit permission before writing code.
- Before changing `sniff_workspace.html`, `sniff_pt_embed.py`, `sniff_urls.py`, or `sniff_v2_workspace.py`, re-read this rule and confirm the chosen approach.

## 2. PostgreSQL schema architecture

- The `public` schema is for shared/global tables only:
  - `auth_user`
  - `dose_tenant`
  - `dose_userprofile`
  - `dose_usertenantmembership`
  - subscriptions and public site config
- Everything else lives in tenant-specific schemas.
- Admin `ModelAdmin` for user/tenant must force `public` schema.
- All other model admins must use `TenantAwareModelAdmin` and set `search_path` to the tenant schema.

## 3. General guardrails

- Do not create `.bak` files or temporary test files in source directories.
- Frozen files (`# THIS CODE IS FROZEN`) may not be changed without owner permission.
- Prefer minimal upstream fixes over downstream workarounds.
- For passthrough apps, route all asset URLs through the existing proxy; do not hotlink upstream hosts.
