<!-- THIS CODE IS FROZEN — NO CHANGES TO THIS CODE ARE ALLOWED WITHOUT THE OWNER'S PERMISSION -->
<!-- BINGO: WordPress dark-mode nav visibility — 2026-08-04 -->

# BINGO: WordPress Dark-Mode Nav Visibility

**Date:** 2026-08-04  
**Status:** COMPLETE — Live on production WordPress  
**Site:** `https://polysaas.online`  
**Verified by:** owner (login) + agent (Customizer publish + computed-style check)  
**Commit:** `70cf5218` (`70cf521870f079505e6e00fe1f52b11c3f8f2f2a`)

## What this certifies

In **dark mode** on the marketing homepage, header nav items that WordPress marks as `current-menu-item` are readable again:

| Item | Role |
|------|------|
| Home | current (home) → white |
| Applications | current (hash `#bundled-apps` on home) → white |
| Features | current (hash `#platform-features` on home) → white |
| Other top-level items | non-current → light blue `#60A5FA` |

Site title in dark mode also lightens to `#E2E8F0`.

## Root cause

1. **Kadence** styles `.current-menu-item > a` with near-black `var(--global-palette3)`.
2. Home + in-page hash links (`#bundled-apps`, `#platform-features`) all receive `current-menu-item` / `menu-item-home` on the homepage.
3. An earlier page-content nav CSS attempt was saved as HTML `<p>` / `<br />` text, so those overrides never applied as CSS.

## Fix applied (live)

Published clean CSS via **Appearance → Customize → Additional CSS** (`custom_css[kadence]`).

Canonical repo copy:

`documentation/website/dark-mode-nav-fix.css`

## Verification

With `body.dark-mode` on `https://polysaas.online/`:

```
Home: rgb(255, 255, 255) (current)
Applications: rgb(255, 255, 255) (current)
Features: rgb(255, 255, 255) (current)
About Us / External Applications / Blog: rgb(96, 165, 250)
```

Customizer save state: **Published**.

## Files in this commit

| Path | Role |
|------|------|
| `documentation/website/dark-mode-nav-fix.css` | Frozen CSS snapshot matching live Additional CSS |
| `documentation/BINGO_WP_DARK_MODE_NAV_VISIBILITY_2026-08-04.md` | This certification |

## Freeze

Source files carry:

```
THIS CODE IS FROZEN — NO CHANGES TO THIS CODE ARE ALLOWED WITHOUT THE OWNER'S PERMISSION
```

plus `BINGO: WordPress dark-mode nav visibility — 2026-08-04`.

## GOLD ZIP

`D:\BINGO ZIPS\BINGO_WP_DARK_MODE_NAV_2026-08-04.zip`  
(retention: keep newest 4 `BINGO_*.zip` only)
