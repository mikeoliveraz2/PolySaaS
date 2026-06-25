# BINGO: UI Cleanup — Dose Home, Unified Login, Admin Sidebar

**Date:** 2026-06-25  
**Status:** Verified locally (office)  
**Branch:** `main`  
**Commit:** _(recorded after commit)_

---

## Summary

Restores the tenant-first navigation shell, consolidates login branding, and fixes the Jazzmin admin sidebar grid so passthrough icons and model cards layout correctly at full and collapsed widths.

---

## Verified

| Area | Check |
|------|--------|
| **Dose home** | `/` → `/dose/home/`; tenant landing for staff and non-staff |
| **Passthrough** | Sidebar / nav links use `/pt/dose/{hostname}/` in Dose shell |
| **Admin optional** | Staff see Admin Panel link; not forced to `/admin/` on login |
| **Unified login** | `/accounts/login/` PolySaaS logo + heading; `/dose/login/` and `/admin/login/` redirect |
| **Post-login** | `LOGIN_REDIRECT_URL` / adapter → `/dose/home/` |
| **tenantsettings** | `{% url 'dose:tenantsettings' %}` resolves; landing page loads |
| **Admin sidebar grid** | Two-column grid (no empty 320px void); Jazzmin `col-lg-9` full width |
| **Collapsed sidebar** | Passthrough icons single-column, scaled to 60px rail |
| **Sidebar height** | No viewport cap; nav panels grow with content |

---

## Files in this BINGO

| File | Change |
|------|--------|
| `dose/urls.py` | `/dose/home/`, `tenantsettings/`, login redirect route |
| `dose/views/main.py` | Home context, `/pt/dose/` URLs, login → allauth |
| `dose/account_adapter.py` | Post-login → `/dose/home/` |
| `dose/doseusertenantmiddleware.py` | Skip `/accounts/login/` |
| `dose/static/admin/css/polysaas-admin-polish.css` | Grid / content column polish |
| `dose/templates/admin/base_site.html` | `custom_sidebar_head.html` in `extrahead` |
| `dose/templates/admin/includes/custom_sidebar_head.html` | **New** — sidebar CSS (grid, collapsed PT cards) |
| `dose/templates/admin/includes/custom_sidebar.html` | Grid JS, recent-actions hoist, collapsed layout |
| `mysite/settings.py` | `LOGIN_URL`, `LOGIN_REDIRECT_URL`, Jazzmin home → `/dose/home/` |
| `mysite/urls.py` | `/admin/login/` → `/accounts/login/` |
| `templates/account/base.html` | PolySaaS login shell |
| `templates/account/login.html` | Unified PolySaaS sign-in |
| `templates/admin/login.html` | PolySaaS fallback admin login template |
| `templates/account/socialaccount_login.html` | Back link copy |
| `templates/account/sociallogin.html` | Back link copy |
| `templates/socialaccount/login.html` | Back link copy |
| `dose/templates/dose/subscribe.html` | Post-subscribe → `/accounts/login/` |
| `dose/templates/dose/connect_social.html` | Login link |
| `dose/templates/dose/connect_social_after_subscribe.html` | Login link |

Prior commit `f8cda096` also landed Dose home routing (`mysite/urls.py`, `custom_sidebar.html` HOME link, `context_processors.py`, etc.) — this BINGO completes login + sidebar grid work on top of that base.

---

## Gold master

ZIP: `D:\BINGO ZIPS\BINGO_UI_CLEANUP_2026-06-25.zip`

---

## Restore

```powershell
Expand-Archive -Path "D:\BINGO ZIPS\BINGO_UI_CLEANUP_2026-06-25.zip" -DestinationPath "D:\PolySaaS"
```
