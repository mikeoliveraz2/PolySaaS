# PolySniffer Reconciliation Handoff - 2026-08-10

## Stable Baseline

- Local `main` and `origin/main` were aligned at `998b8035`.
- This baseline includes the tenant-schema capture-user fix merged through PR #50.
- Focused capture-user validation passed: `dose.tests.test_polysniffer_v2` (5/5).

## Preserved Experiments

The experimental work is isolated on `wip-local-reconcile-20260810`:

```text
348acc04 Preserve local process rules
3c3ba1bf Preserve local endpoint identity work
b9f92d31 Preserve local AI admin work
8d8b5ef5 Preserve local native forwarding work
60802fbe Preserve local browser capture work
```

Validation recorded while preserving the stack:

- Endpoint URL suite: 5/5 passed.
- PolySniffer architecture suite: 20/20 passed.
- Browser command `capture_polysniffer_browser` registered successfully.
- Locked architecture suite: 23/27 passed. Known findings include the Native rewrite import and existing endpoint-ID references. These were not repaired during preservation.

## Deliberately Excluded

The following local paths were not committed:

- `dose/migrations/0060_alter_passthroughendpoint_endpoint_url.py`
- `documentation/Capital Raise Project/`
- `polysniffer-auth.json`
- `polysniffer_evidence/`

Migration `0060` proposes global uniqueness for `endpoint_url` and needs an explicit tenancy decision before use. Authentication state and capture evidence may contain sensitive or environment-specific data and must not be committed without review.

## Next Decisions

1. Review the WIP commits independently before selecting work for production.
2. Decide whether endpoint URL uniqueness is global or tenant-scoped before accepting migration `0060`.
3. Resolve the locked-architecture findings before promoting the Native experiment.
4. Decide whether local authentication/evidence paths should be ignored, archived securely, or deleted.

The earlier `GIT_STATUS_ANALYSIS_2026-08-10.md` is historical and is not authoritative for the reconciled repository state.