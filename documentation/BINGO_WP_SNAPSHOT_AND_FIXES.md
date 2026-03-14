# BINGO: WordPress Snapshot Utility & Header/Toggle Fixes

**Date:** March 14, 2026  
**Status:** Complete and Tested  
**Branch:** commit-changes

---

## Summary

Built a WordPress page snapshot/restore utility for rollback safety, fixed the header logo size reversion, and repositioned the dark mode toggle to stop overlapping the Sign Up nav item.

---

## 1. WordPress Snapshot Utility (`wp_snapshot.py`)

### Problem
Bulk update scripts modify all 22+ WordPress pages via REST API. When a script introduced bugs (e.g., CSS corruption from `wpautop`, lost style blocks), there was no way to quickly roll back — the previous content was gone.

### Solution
Created `wp_snapshot.py` — a CLI and library utility that exports all page content (raw Gutenberg blocks via `context=edit`) to timestamped JSON files before any changes.

### Usage
```
python wp_snapshot.py export "description"    # Save snapshot
python wp_snapshot.py list                     # List snapshots
python wp_snapshot.py restore <file> [slug]    # Restore all or one page
python wp_snapshot.py diff <file>              # Show changes since snapshot
```

As a library (called from fix scripts):
```python
from wp_snapshot import take_snapshot
take_snapshot("before fixing X")
```

### Key Design Decisions
- Uses `context=edit` API parameter to get **raw** Gutenberg block content, not rendered HTML
- Snapshots stored in `wp_snapshots/` directory with timestamps and descriptions
- Supports single-page restore for surgical rollbacks
- Diff command shows character-level size changes per page

---

## 2. Header Logo Size Fix

### Problem
The header logo had reverted to its large default size (~200px) despite CSS being "injected." Investigation revealed the root cause: previous fix scripts fetched `content.rendered` (which has `wpautop` applied, stripping `<!-- wp:html -->` wrappers) and posted it back. This destroyed the protection that prevented WordPress from corrupting our CSS with `<p>` tags.

### Solution
`fix_logo_final.py` — fetches pages with `context=edit` (raw content), removes any corrupted CSS blocks, and re-injects clean header logo CSS wrapped in `<!-- wp:html -->`:

```css
.site-branding a.brand img { max-width: 60px !important; }
```

### Verification
- Rendered HTML confirmed: clean CSS, no `<p>` corruption
- Browser screenshot: logo ~60px in both light and dark mode

### Root Cause Lesson
**Always use `context=edit` when reading and writing WordPress page content via API.** Using `content.rendered` strips Gutenberg block markers, causing `wpautop` to corrupt CSS/JS on the next save.

---

## 3. Toggle Button Position Fix

### Problem
The dark mode toggle button (fixed position at `top:80px;right:20px`, later moved to `top:12px;right:12px`) was overlapping the "Sign Up" navigation menu item.

### Solution
`fix_toggle_position.py` — repositioned toggle to `top:90px;right:20px` (just below the ~80px header bar), using raw content via `context=edit`. Takes a snapshot before making changes.

### Verification
- Browser screenshot: "Sign Up" fully visible, toggle below header bar
- Both light and dark mode confirmed working

---

## Files Created/Modified

| File | Purpose |
|------|---------|
| `wp_snapshot.py` | Snapshot/restore utility |
| `wp_snapshots/` | Snapshot storage directory |
| `fix_logo_final.py` | Header logo CSS fix (raw content) |
| `fix_toggle_position.py` | Toggle repositioning (raw content) |
| `fix_logo_and_toggle_pos.py` | Initial attempt (rendered content) |
| `debug_header_logo.py` | Diagnostic script for header CSS |

## Snapshots Taken
1. `snapshot_20260314_105406_baseline_before_toggle_and_logo_fixes.json` — 30 pages
2. `snapshot_20260314_105447_before_toggle_position_fix.json` — 30 pages
3. `snapshot_20260314_105915_bingo_snapshot_after_logo_toggle_fixes.json` — 30 pages

---

## Tested and Verified
- [x] Header logo renders at ~60px in light mode
- [x] Header logo renders at ~60px in dark mode
- [x] Toggle button does not overlap Sign Up
- [x] Toggle button works (light/dark switch functional)
- [x] Dark mode text is white (not grey)
- [x] Snapshot export captures all 30 pages
- [x] Snapshot list shows available backups
- [x] All 22 content pages updated consistently
