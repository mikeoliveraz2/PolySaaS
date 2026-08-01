# BINGO: Mattermost PassThroughEndpoint Upsert Fix

**Date:** 2026-08-02
**Verified by:** agent, via direct DB query + Django test client render of `/dose/home/` for tenant `pso16` (Mattermost tile now present alongside Odoo/NextCloud/HubSpot/Dolibarr).

## What this certifies

`dose/services/mattermost_tenant_provisioner.py` — owner unlocked the freeze on this file
specifically for this fix ("unlock the freeze it was obviously wrong, fix it properly").

## Symptom

No tenant — going back to before the migration off Render — ever had a Mattermost tile on
`/dose/home/` or the admin sidebar, even though Mattermost provisioning itself (team creation,
user creation, OIDC, token) succeeded and `TenantApp(app_name='mattermost')` correctly showed
`status='active'`.

## Root cause

`_ensure_passthrough_endpoint()` called:

```python
PassThroughEndpoint.objects.update_or_create(
    slug='mattermost',
    defaults={
        'name': 'Mattermost',
        ...
    },
)
```

`PassThroughEndpoint` has no `name` field (only `menu_title`, `description`, `slug`, etc.). Every
call raised `TypeError`/`FieldError`, which was caught by the surrounding `try/except` and logged
as a `warning` — so `result['passthrough_endpoint_error']` was set but the overall provisioning
result still reported success (team/user/token steps all genuinely succeeded), masking the
failure. The row was never created, in any tenant schema, ever.

Likely origin: lost during the `public_bundles` / search_path cleanup on 2026-07-30, or earlier —
predates this session either way.

## Fix

1. Removed the invalid `'name'` key from the `defaults` dict — that alone fixes the crash.
2. Per owner request, `description` now carries the tenant's real company/display name (the
   `display_name = company_name or tenant_name` value already computed by the caller), matching
   the convention already established by `odoo_tenant_provisioner.py`
   (`f'Odoo ERP for {company_name or tenant_name}'`).
3. Also appended the shared/common team name (`_shared_team_name()`, defaults to
   `polysaas-dev-team`) to the description, since the owner asked for it and the helper already
   existed with no extra API risk to call.

```python
def _ensure_passthrough_endpoint(tenant_schema: str, mm_url: str, display_name: str, result: dict) -> None:
    ...
    shared_team_name = _shared_team_name()
    _, created = PassThroughEndpoint.objects.update_or_create(
        slug='mattermost',
        defaults={
            'endpoint_url': mm_url,
            'description': f'Mattermost Team Chat for {display_name} (shared team: {shared_team_name})',
            'is_enabled': True,
            'passthrough_type': 'scraper',
            'integration_mode': 'web_api',
            'api_endpoint': f"{mm_url}/api/v4",
            'show_in_menu': True,
            'menu_title': 'Mattermost',
            'menu_icon': 'chat',
            'menu_sort_order': 25,
            'starting_uri': '/',
        },
    )
```

Call site updated to pass the already-computed `display_name` through:
`_ensure_passthrough_endpoint(tenant_schema, mm_url, display_name, result)`.

## Backfill

Ran a one-off script (not committed — temporary, deleted after use) that iterated every active
`Tenant`, set `search_path` to that tenant's schema, and called the now-fixed
`_ensure_passthrough_endpoint()` for any tenant with `TenantApp(app_name='mattermost',
status='active')` but no existing `PassThroughEndpoint(slug='mattermost')` row. This retroactively
created the missing row for tenants that were already fully provisioned before this fix, without
re-running the expensive Mattermost API calls (team/user/token creation) a second time.

Backfilled: `polysaas`, `pso13`, `pso14`, `pso16`.

```
polysaas -> url=http://localhost:8065 desc='Mattermost Team Chat for PolySaaS Online LLC (shared team: polysaas-dev-team)'
pso13    -> url=http://localhost:8065 desc='Mattermost Team Chat for pso13 (shared team: polysaas-dev-team)'
pso14    -> url=http://localhost:8065 desc='Mattermost Team Chat for PSO14 (shared team: polysaas-dev-team)'
pso16    -> url=http://localhost:8065 desc='Mattermost Team Chat for pso16 (shared team: polysaas-dev-team)'
```

## Verified

Restarted Waitress to load the fixed provisioner code, then rendered `/dose/home/` for `pso16`
via Django's test client:

```
[JAZZMIN DEBUG] Loaded 5 passthrough endpoints from schema: pso16
[JAZZMIN DEBUG] - Odoo: http://localhost:8086
[JAZZMIN DEBUG] - Mattermost: http://localhost:8065
[JAZZMIN DEBUG] - NextCloud: http://localhost:8888
[JAZZMIN DEBUG] - HubSpot: https://app.hubspot.com
[JAZZMIN DEBUG] - Dolibarr: http://localhost:8083
status: 200
Mattermost mentioned: True
```

Mattermost now appears as a passthrough tile for every tenant with an active Mattermost
`TenantApp`, both going forward (new signups) and retroactively (existing tenants, via backfill).

## Files in this commit

- `dose/services/mattermost_tenant_provisioner.py`
- `dose/services/mattermost_tenant_provisioner.py.bak_20260802_passthrough_endpoint_fix` (backup, per `bak-before-edit.mdc`)
- `documentation/BINGO_MATTERMOST_PASSTHROUGH_ENDPOINT_FIX_2026-08-02.md` (this file)

`dose/services/mattermost_tenant_provisioner.py` carries its pre-existing freeze banner plus a new
`BINGO:` annotation line dated 2026-08-02 documenting this specific owner-approved exception.
