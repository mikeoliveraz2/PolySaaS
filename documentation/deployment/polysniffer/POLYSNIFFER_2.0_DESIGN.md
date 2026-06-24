<!-- THIS CODE IS FROZEN — NO CHANGES TO THIS CODE ARE ALLOWED WITHOUT THE OWNER'S PERMISSION -->
<!-- BINGO: PolySniffer 2.0 — 2026-06-24 -->

# PolySniffer 2.0 — Design & Operator Guide

**Status:** Implemented (server-only dual-mode sniff)  
**Replaces:** Chrome extension as primary capture path  
**Related:** [PASSTHROUGH_HAR_PARITY_HANDOFF_2026-05-22.md](../../../PASSTHROUGH_HAR_PARITY_HANDOFF_2026-05-22.md)

---

## Summary

PolySniffer 2.0 provides **two sniff modes** on a dedicated staff-only endpoint:

| Mode | Route | Transformation | Orchestration | `capture_source` |
|------|-------|----------------|---------------|------------------|
| **Native** | `/dose/sniff/<id>/native/…` | None (transparent proxy) | Off | `native` |
| **Passthrough** | `/dose/sniff/<id>/passthrough/…` | Full handler chain | On (production-like) | `passthrough` |

Both modes write to the same `TrafficLog` / HAR export pipeline via `dose.polysniffer.har_capture`.

---

## Operator workflow

1. Django Admin → **PassThrough Endpoints** → click **PolySniffer 2.0**.
2. Choose **Native** or **Passthrough** and start a capture session.
3. Browse the upstream app through the sniff proxy URL (new tab — not iframe).
4. Stop session → **Export HAR** or open **Diff** to compare native vs passthrough rows.

### URLs

```
/dose/sniff/<endpoint_id>/                      Mode picker
/dose/sniff/<endpoint_id>/session/start/        POST — start capture
/dose/sniff/<endpoint_id>/session/stop/         POST — stop capture
/dose/sniff/<endpoint_id>/native/<path>         Native proxy
/dose/sniff/<endpoint_id>/passthrough/<path>    Passthrough proxy
/dose/sniff/<endpoint_id>/diff/                 Native vs passthrough diff
/dose/sniff/<endpoint_id>/export-har/           HAR download (session filter)
```

Legacy `/admin/polysniffer/proxy/…` redirects to the mode picker.

---

## Architecture

- **`har_capture.py`** — single write path for `TrafficLog` + HAR JSON
- **`sniff_forward.py`** — native transparent forward (no handlers, no orchestration)
- **`views/sniff_v2.py`** — mode picker, session control, passthrough dispatch, diff
- **`forwarding.py`** — passthrough sniff logs via `har_capture` when a session is active; orchestration unchanged

Native mode is **sniff-native** (minimal PolySaaS proxy), not browser-direct-to-upstream. HAR metadata includes `sniff_mode`.

---

## Constraints

- Staff-only; tenant-scoped `TrafficCapture` sessions
- No app-specific branches in shared forwarder (generic session + mode flags only)
- `orchestration_hook.py` not modified — native mode never enters passthrough forwarder orchestration path
- Mattermost: no team API / team slug logic added in sniff code

---

## GCS export (optional)

Set in environment:

```
POLYSNIFFER_GCS_BUCKET=polysaas-polysniffer-hars
GCP_PROJECT_ID=your-project
```

POST `/dose/sniff/<id>/export-har/?gcs=1` uploads HAR JSON to  
`gs://{bucket}/{tenant_slug}/{capture_id}/export.har`

---

## Deprecations

- Chrome extension: deprecated for operator workflows; `browser_extension` capture_source retained for legacy rows
- `proxy_capture` HTML rewriting path: redirects to PolySniffer 2.0 mode picker
