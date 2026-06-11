# BINGO: Font and Theme Toggle

**Date:** 2026-06-11  
**Status:** ✅ VERIFIED WORKING  
**Branch:** main  
**Commit:** _(recorded in follow-up commit after push)_

---

## Summary

Certified working split between **display mode toggle** (light ↔ dark) and **Bootswatch theme selection** (palette), plus sidebar CONTROLS UX fixes.

- ✅ Top nav **Toggle light/dark** flips mode only via `/dose/toggle-theme/` (no navigation to theme picker page)
- ✅ Sidebar **CONTROLS → Themes** opens full theme picker (16 light + 5 dark Bootswatch choices, font size, accessibility)
- ✅ Theme picker popover portaled to `document.body` with fixed positioning (not clipped by sidebar `overflow: hidden`)
- ✅ SVG palette + bell icons in CONTROLS (immune to `applyFont()` Font Awesome breakage)
- ✅ `/admin/select-theme/` and `/admin/select-theme/api/` restored for palette save/load
- ✅ `/dose/set-display-mode/` for explicit Light / Dark / System mode (palette picks unchanged)
- ✅ Default light Bootswatch: **Sandstone** (was Flatly — too bright)
- ✅ Font controls modal remains in `base_site.html` `extrajs` block

---

## Architecture

| Control | Action | Endpoint |
|---------|--------|----------|
| Top nav toggle / user menu | Flip light ↔ dark | `GET /dose/toggle-theme/` |
| Sidebar Themes button | Open Bootswatch + display settings popover | In-sidebar JS + `/admin/select-theme/api/` |
| Display Mode buttons in popover | Set light / dark / system | `GET /dose/set-display-mode/?mode=…` |
| Save Themes in popover | Persist light + dark Bootswatch picks | `POST /admin/select-theme/` |
| Font controls (legacy modal) | Font family / size / weight | `base_site.html` localStorage + `applyFont()` |

**Rule:** Toggle = mode only. Palette = Bootswatch theme names.

---

## Verification (manual)

1. Hard refresh admin (`Ctrl+Shift+R`).
2. **CONTROLS → Themes:** popover opens fully to the right of sidebar (not clipped); light/dark dropdowns populated; Save Themes reloads with new Bootswatch.
3. **CONTROLS icons:** palette and bell render as SVG (not tofu boxes).
4. **Top nav Toggle light/dark:** page reloads in opposite mode; badge shows Light/Dark; Bootswatch pick for that mode unchanged.
5. **Display Mode** in popover: Light / Dark / System switches mode without changing saved Bootswatch names.
6. Try **Journal** or **Sandstone** as light theme if Flatly feels too bright.

---

## FROZEN FILE MANIFEST

**NO CHANGES WITHOUT OWNER PERMISSION (Michael / Shela).**

| File | Role |
|------|------|
| `dose/admin_views.py` | `select_theme`, `select_theme_api`, theme lists, Sandstone default |
| `dose/apps.py` | AdminSite `select-theme` URL registration fallback |
| `dose/theme_views.py` | `toggle_theme`, `set_display_mode`, profile theme prefs |
| `dose/urls.py` | `set-display-mode` route |
| `dose/static/admin/js/theme-toggle.js` | Nav toggle binding + mode badge |
| `static/admin/js/theme-toggle.js` | Collected copy (keep in sync) |
| `dose/templates/admin/base_site.html` | Theme modal, font controls modal, `applyFont()` |
| `dose/templates/admin/includes/custom_sidebar.html` | CONTROLS tiles, SVG icons, theme popover portal |
| `mysite/urls.py` | `admin/select-theme/` routes |
| `mysite/settings.py` | Jazzmin toggle link `#ps-theme-toggle` |

Associated `.bak` snapshots alongside edited files are included in the commit.

---

## BINGO ZIP

```powershell
$name = "BINGO_FONT_AND_THEME_TOGGLE_2026-06-11"
Compress-Archive -Path "D:\PolySaaS\*" -DestinationPath "D:\BINGO ZIPS\$name.zip" -CompressionLevel Optimal
Write-Host "BINGO ZIP created: D:\BINGO ZIPS\$name.zip"
```
