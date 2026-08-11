# PolySniffer Reconciliation Handoff - 2026-08-10

## Stable Baseline

- Local `main` and `origin/main` were aligned at `23512685`.
- This baseline includes the tenant-schema capture-user fix merged through PR #50.
- The complete focused PolySniffer suite passed: 34/34 tests across v2, architecture, and locked-architecture modules.

## 2026-08-11 Certification State

The two PolySniffer surfaces have separate verdicts:

- Capture workspace: GREEN. `/admin/polysniffer/sniff/localhost:8065/` resolved on stable `main`; passthrough capture 18 recorded a Mattermost 200 response and persisted one `passthrough` log with `user_id=None`; polling returned one row; stop left no active captures.
- Production embed: RED. `/pt/admin/localhost:8065/` returned Mattermost HTML, but the UI was blank because Mattermost `/static/main.*` and `remote_entry.js` requests resolved on the PolySaaS origin and returned 404, while inline scripts were blocked by CSP.

UI acceptance must be performed in the user's normal browser, with the user's viewport, credentials, and session. The integrated browser and Django test client may provide diagnostic or server-side evidence but do not certify layout or usability.

For the local Mattermost test account:

- Username: `admin`
- Tenant profile: `polysaas`
- Expected endpoint: Mattermost at `http://localhost:8065`

The account profile was left assigned to `polysaas` so a fresh logout/login selects the correct tenant.

## Server State Before Office Retest

Port 8000 had two competing listeners during the final test:

- A stale Django `runserver 127.0.0.1:8000 --noreload` process started on 2026-08-09.
- A Waitress process listening on `0.0.0.0:8000`.

The stale process served the old iframe workspace, including `proxy-frame` and `capture-frame`. Stable `main` at `23512685` has an iframe-free workspace that launches Native and Passthrough in a top-level browser window.

Before retesting at the office, stop the competing port-8000 processes and start exactly one server from `F:\PolySaaS` at `23512685`. Do not modify stable `main` to repair behavior observed from the stale process.

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