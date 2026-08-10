# BINGO: Passthrough Endpoint-Only Identity

**Date:** 2026-08-09  
**Status:** Implemented and regression-tested

## Certified Design

For `PassThroughEndpoint` routing, the unique `endpoint_url` string is the only
reference to the endpoint. Browser routes expose neither the database primary
key nor `slug`:

```text
/pt/admin/<endpoint host>/<upstream path>
/pt/dose/<endpoint host>/<upstream path>
```

The host is parsed from the stored `endpoint_url`. `starting_uri` contributes
only the initial upstream path. The unchanged `endpoint_url` remains the proxy
target and exact tenant-row match.

## Defunct Designs

The following are defunct for `PassThroughEndpoint` browser links and proxy
resolution and must not be restored:

- Integer primary-key or integer-offset endpoint identity.
- `slug` endpoint identity.
- A second trigger, alias, or synthesized upstream URL.
- Public-schema, cross-tenant, ID, or slug fallback when the exact tenant host
  does not match.

This restriction does not remove integer IDs from unrelated Django admin,
PolySniffer, capture, or session records.

## Enforcement

- `endpoint_url` has a database unique constraint in every tenant schema.
- `get_proxy_prefix(surface)` permits only `admin` and `dose`.
- Dose landing links explicitly request the `dose` surface.
- The obsolete, unregistered `direct_service_view(endpoint_id)` entry point was
  removed.
- Route parameters and current comments identify the endpoint host rather than
  a slug or trigger.

## Validation

- `dose.tests.test_passthrough_endpoint_url`: 5 tests passed.
- `python manage.py check`: no issues.
- `python manage.py makemigrations --check --dry-run`: no changes detected.
- Existing endpoint tables audited in `polysaas`, `polysaasonline`, `pso10`,
  `pso13`, `pso14`, `pso15`, `pso16`, `psol6`, and `public`: no duplicate
  `endpoint_url` values.
- Migrations `0059` and `0060` applied successfully to `public` and all eight
  tenant schemas with `migrate_all_schemas --no-input`.