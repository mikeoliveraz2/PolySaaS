# Dolibarr — PolySniffer internal navigation verified

**Date:** 2026-08-13  
**Owner:** Michael  
**Status:** Verified (not BINGO) — Company/Organization and theme CSS OK under PolySniffer workspace  
**Endpoint:** Dolibarr `http://localhost:8083`  
**Tenant context:** `pso17`  
**Related commits:** `c9fe06bf` (proxy prefix / DOLSESSID), `22dc51bd` (SSO cookies), `d23d23a8` (workspace `<iframe>`)

---

## What was verified

PolySniffer workspace (**Native** session) loads Dolibarr Setup → **Company/Organization** with theme styling and internal navigation far enough for capture work.

| Check | Result |
|-------|--------|
| Company/Organization form (tabs, fields, currency/country) | Renders with eldy theme |
| Live capture lists theme/CSS/JS assets | `200` including `/theme/eldy/style.css.php?...` |
| Session example | `localhost:8083-native-20240812-2255` |
| Workspace browser pane | `<iframe>` (object→iframe on this branch) |

Jazzmin production-style path `/pt/admin/localhost:8083/…` was already known good for Dolibarr CSS; this note certifies the **PolySniffer** embed path (`/pt/polysniff/{endpoint_id}/…`) for the same Company setup screen.

---

## Architecture notes (for later work)

| Piece | Role |
|-------|------|
| `sniff_workspace.html` | Admin shell; both modes load `/pt/polysniff/{id}{browse_subpath}` in the pane |
| `sniff_pt_proxy.py` | Rewrites to `/pt/admin/{trigger}/`, sets `_polysniffer_proxy_prefix`, Location/HTML rewrite, capture shim |
| `dolibarr_handler.py` | Theme/CSS path rewrites; honors `_polysniffer_proxy_prefix` |

If CSS breaks again: inspect the **iframe** document Network tab (not the workspace poll HAR) for `/theme/…` and `style.css.php` host/status.

---

## Operator checklist (smoke)

1. Admin → PassThrough Endpoints → PolySniffer workspace for Dolibarr (`localhost:8083`)
2. **Start Native** (or Passthrough) → open Setup → Company/Organization
3. Confirm styled tabs/form (not bare bullets)
4. Live capture shows `style.css.php` / theme assets `200`
5. Spot-check a few other Setup links; note any unstyled page or host jump off `/pt/polysniff/…`

---

## Next

- **Nextcloud** PolySniffer / passthrough SSO (next focus)
- Broader Dolibarr menu walk still operator-driven; escalate only if a specific path loses CSS or auth
