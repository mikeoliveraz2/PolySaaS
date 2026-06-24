# BINGO — PolySniffer 2.0 (Native + Passthrough dual-mode sniff)

**Date:** 2026-06-24  
**Declared by:** Michael  
**Commit:** _(filled after push)_  
**Replaces:** Chrome extension as primary capture path; legacy `/admin/polysniffer/proxy/` HTML rewrite

---

## What Was Achieved

Server-only PolySniffer with two sniff modes on `/dose/sniff/<endpoint_id>/`:

| Mode | Route | Transform | Orchestration | `capture_source` |
|------|-------|-----------|---------------|------------------|
| **Native** | `/dose/sniff/<id>/native/…` | Transparent proxy only | Off | `native` |
| **Passthrough** | `/dose/sniff/<id>/passthrough/…` | Full handler chain | On (production-like) | `passthrough` |

Shared `har_capture` engine writes `TrafficLog` + HAR JSON for parity diffs (native vs passthrough HAR workflow).

---

## Certified behaviors

| Feature | Status |
|---------|--------|
| Mode picker UI at `/dose/sniff/<id>/` | ✓ |
| TrafficCapture session start/stop (staff, tenant-scoped) | ✓ |
| Native sniff — no handlers, no orchestration_hook | ✓ |
| Passthrough sniff — delegates to `pt_admin_generic_passthrough_view` | ✓ |
| Forwarder logs via `har_capture` when capture session active | ✓ |
| Native vs passthrough diff view | ✓ |
| HAR export (+ optional GCS via `POLYSNIFFER_GCS_BUCKET`) | ✓ |
| Admin **PolySniffer 2.0** button on PassThroughEndpoint | ✓ |
| Legacy `proxy_capture` redirects to mode picker | ✓ |
| Unit tests `dose.tests.test_polysniffer_v2` | ✓ |
| `python manage.py check` clean | ✓ |

---

## Architecture

```
Admin Sniff → /dose/sniff/<id>/ → Native | Passthrough
Native → sniff_forward.forward_sniff_native → har_capture → TrafficLog
Passthrough → pt_admin → handlers → forwarding → orchestration_hook → har_capture
```

---

## Files in this commit

| File | Role |
|------|------|
| `dose/polysniffer/har_capture.py` | Shared TrafficLog + HAR writer |
| `dose/polysniffer/sniff_forward.py` | Native transparent proxy |
| `dose/polysniffer/views/sniff_v2.py` | Mode picker, sessions, diff, export |
| `dose/polysniffer/sniff_urls.py` | URL routes |
| `dose/polysniffer/gcs_export.py` | Optional GCS HAR upload |
| `dose/polysniffer/middleware.py` | Skip `/dose/sniff/`; use har_capture |
| `dose/polysniffer/views/proxy.py` | Deprecated redirect |
| `dose/polysniffer/views/ui.py` | open_sniffer → mode picker |
| `dose/passthrough/forwarding.py` | Passthrough capture via har_capture |
| `dose/urls.py` | Mount `sniff/` routes |
| `dose/apps.py` | Re-register `/admin/polysniffer/` legacy URLs |
| `dose/admin.py` | PolySniffer 2.0 admin button |
| `dose/templates/polysniffer/mode_picker.html` | Mode picker UI |
| `dose/templates/polysniffer/diff_view.html` | Diff UI |
| `dose/tests/test_polysniffer_v2.py` | Unit tests |
| `documentation/deployment/polysniffer/POLYSNIFFER_2.0_DESIGN.md` | Design + operator guide |
| `documentation/POLYSNIFFER_SETUP.md` | Extension deprecation notice |

---

## Operator checklist

1. Restart: `.\runall.ps1`
2. Admin → PassThrough Endpoints → **PolySniffer 2.0**
3. Start **native** session → open native proxy → browse upstream
4. Start **passthrough** session → open passthrough proxy → verify handler/orchestration path
5. **Diff** — compare paths; expect mismatches where handlers rewrite HTML
6. **Export HAR** — download JSON; optional `?gcs=1` with `POLYSNIFFER_GCS_BUCKET` set

```powershell
python manage.py test dose.tests.test_polysniffer_v2
python manage.py check
```

---

## Known limits

- Native mode is sniff-native (minimal PolySaaS proxy), not browser-direct-to-upstream
- WebSocket traffic not fully captured in HAR
- Passthrough sniff rewrites `request.path_info` to `/pt/admin/<trigger>/…` for handler dispatch
- `orchestration_hook.py` unchanged — native mode bypasses it by routing

---

## Tests

```powershell
python manage.py test dose.tests.test_polysniffer_v2
```
