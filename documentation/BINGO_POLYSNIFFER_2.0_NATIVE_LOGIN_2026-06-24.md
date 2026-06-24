# BINGO — PolySniffer 2.0 Native Login Workspace

**Date:** 2026-06-24  
**Declared by:** Michael  
**Commit:** `24ce8dfa`  
**Builds on:** `e93f9c23` (PolySniffer 2.0 dual-mode sniff)

---

## What Was Achieved

Split PolySniffer workspace with live capture panel plus **native Mattermost login** through the minimal sniff proxy (not browser-direct upstream).

| Area | Behavior |
|------|----------|
| **Workspace UI** | Left iframe = native or passthrough browse; right iframe = green-screen live `TrafficLog` poll |
| **Native browse** | `/dose/sniff/<id>/native/login/` — minimal proxy, static direct to upstream host |
| **Mattermost shim** | API/plugins via sniff prefix; `config/client?format=old`; `SiteURL` rewritten |
| **Capture** | Tenant-scoped `TrafficCapture` + `workspace_poll` live rows |
| **Login fix** | Query-string forwarding bug fixed (`request.GET.urlencode()` — was 500 on `?format=old`) |

---

## Certified behaviors

| Feature | Status |
|---------|--------|
| Workspace at `/dose/sniff/<id>/workspace/` | ✓ |
| Start native / passthrough session from workspace | ✓ |
| Live capture poll (`workspace_poll`) — tenant schema | ✓ |
| Native `/login/` HTML — shim injected, no "sign-in methods" error | ✓ |
| `GET .../api/v4/config/client?format=old` → 200, `EnableSignInWithEmail: true` | ✓ |
| `POST .../api/v4/users/login` proxied (401 on bad creds, not 500) | ✓ |
| `scripts/_test_native_login.py` passes | ✓ |

---

## Root cause fixed

`forward_sniff_native` called `urlencode(QUERY_STRING)` on a raw string. Any proxied API request with query parameters (including Mattermost `config/client?format=old` from the client shim) returned **500**, so the SPA showed *"This server doesn't have any sign-in methods enabled"*.

**Fix:** `target_url += sep + request.GET.urlencode()`

---

## Files in this commit

| File | Role |
|------|------|
| `dose/polysniffer/sniff_forward.py` | Native forwarder; query-string fix; handler rewrites |
| `dose/polysniffer/sniff_native_rewrite.py` | Generic native fallback; `prepare_native_upstream_url` |
| `dose/polysniffer/sniff_handler_bridge.py` | Handler-registered native rewrite dispatch |
| `dose/polysniffer/handlers/mattermost_native_sniff.py` | Mattermost HTML shim + `config/client` rewrite |
| `dose/polysniffer/sniff_tenant.py` | Tenant binding for capture lookup |
| `dose/polysniffer/sniff_session.py` | Session start/stop in tenant schema |
| `dose/polysniffer/views/sniff_v2_workspace.py` | Split workspace + capture poll |
| `dose/polysniffer/sniff_urls.py` | Workspace routes |
| `dose/polysniffer/schema_patch.py` | TrafficLog capture column ensure |
| `dose/templates/polysniffer/sniff_workspace.html` | Workspace shell UI |
| `dose/templates/polysniffer/sniff_workspace_capture.html` | Live capture panel |
| `dose/templates/polysniffer/sniff_workspace_browse.html` | Browse iframe helper |
| `dose/templates/polysniffer/mode_picker.html` | Link to workspace |
| `scripts/_test_native_login.py` | Regression script |

---

## Operator checklist

1. Restart: `.\runall.ps1`
2. Admin → PassThrough Endpoints → **PolySniffer 2.0** → workspace
3. **Start native** — left pane loads Mattermost login form; right pane shows captured traffic
4. Confirm capture row: `GET .../config/client?format=old` status **200**
5. Log in with Mattermost credentials (native = no PolySaaS SSO)

```powershell
python scripts\_test_native_login.py
```

---

## Known limits

- Native mode requires upstream Mattermost credentials; passthrough mode is for PolySaaS SSO
- WebSocket traffic not fully captured in HAR
- `sniff_forward.py` from prior BINGO extended — not a pure transparent proxy for Mattermost (handler rewrites required)
