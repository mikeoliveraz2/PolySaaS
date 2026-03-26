# BINGO: Admin Dashboard Layout Fix (Jazzmin + AdminLTE 4)

**Date:** 2026-03-26
**Status:** Complete and verified
**Branch:** commit-changes

---

## Screenshot

![Admin Dashboard Fixed Layout](../images/admin-layout-fixed-2026-03-26.png)

---

## Problem

The Django admin dashboard using Jazzmin theme had layout issues:
- Top navbar was floating in the middle of the page instead of at the top
- Dashboard content was pushed far below the sidebar instead of being aligned with it
- Content area had excessive whitespace/margins

## Root Cause

1. **Template Priority**: The custom `templates/admin/base_site.html` was being overridden by Jazzmin's own template at `.venv/Lib/site-packages/jazzmin/templates/admin/base_site.html`
2. **Wrong CSS Classes**: CSS was targeting AdminLTE 3 classes (`.main-sidebar`, `.content-wrapper`, `.main-header`) but Jazzmin uses AdminLTE 4 classes (`.app-sidebar`, `.app-main`, `.app-header`)
3. **Flex Layout**: AdminLTE 4's `.app-wrapper` uses flexbox column layout which was pushing content below the sidebar

---

## What Was Done

### 1. Template Relocation
- Copied `templates/admin/base_site.html` to `dose/templates/admin/base_site.html`
- This takes priority in Django's template loading order (dose/templates listed first in TEMPLATES setting)

### 2. CSS Fixes for AdminLTE 4
Updated CSS to target correct AdminLTE 4 class names:

```css
/* AdminLTE 4: Sidebar fixed at left */
.app-sidebar {
  position: fixed !important;
  left: 0 !important;
  top: 0 !important;
  width: 250px !important;
  height: 100vh !important;
  z-index: 1038 !important;
}

/* AdminLTE 4: Main content area - positioned absolutely */
.app-main {
  position: absolute !important;
  top: 0 !important;
  left: 255px !important;
  right: 0 !important;
  padding-top: 60px !important;
  padding-left: 10px !important;
  min-height: 100vh !important;
}

/* AdminLTE 4: Top navbar fixed */
.app-header {
  position: fixed !important;
  top: 0 !important;
  left: 250px !important;
  right: 0 !important;
  z-index: 1037 !important;
}

/* Force app-wrapper to NOT use flex column */
.app-wrapper {
  display: block !important;
  position: relative !important;
}
```

### 3. Jazzmin Settings
Added to `JAZZMIN_SETTINGS`:
```python
"show_ui_builder": False,
"show_sidebar": True,
"navigation_expanded": False,
"changeform_format": "horizontal_tabs",
```

---

## Files Modified

| File | Change |
|------|--------|
| `dose/templates/admin/base_site.html` | New file - AdminLTE 4 layout fix CSS |
| `mysite/settings.py` | Added Jazzmin settings for UI builder off, etc. |

---

## Verification

1. Hard refresh admin page (Ctrl+Shift+R)
2. Top navbar should be at very top of page
3. Dashboard content should start immediately below navbar, aligned with top of sidebar
4. No excessive whitespace between navbar and content

---

## Notes

- AdminLTE 4 (used by latest Jazzmin) has completely different class names than AdminLTE 3
- Template priority in Django: first matching template wins, so `dose/templates/` takes precedence over `templates/` which takes precedence over Jazzmin's bundled templates
- The JS errors about `content-wrapper not found` in console are from legacy code and don't affect the layout fix
