# BINGO: Odoo Passthrough Layout Fix

**Date:** 2026-06-09  
**Commit:** (to be added after commit)  
**Status:** ✅ VERIFIED WORKING

## Summary

Fixed Odoo passthrough layout issue where Odoo content was not properly positioning in the Django admin content area. The root cause was a missing template context flag that caused the wrong CSS layout to be applied.

## Problem

Odoo content was displaying but not correctly positioned:
- Not filling the content area to the right of the sidebar
- Not properly positioned under the green orchestration bar
- Not using full available width and height
- Layout appeared compressed and misaligned

## Root Cause

The `OdooPassthroughHandler` was missing the `passthrough_embed_template_context()` method that sets the `embed_enable_odoo_body_scope` flag. 

The `passthrough_embed.html` template has conditional CSS:
```django
{% if embed_enable_odoo_body_scope %}
    /* Odoo-specific flex layout CSS */
{% else %}
    /* Mattermost/generic layout CSS */
{% endif %}
```

Without this flag being set, the template was incorrectly applying Mattermost's CSS layout rules to Odoo, which uses a completely different layout model:
- **Odoo**: Flex container with `flex: 1 1 auto`, proper containment for SPA
- **Mattermost**: `overflow: visible`, different height calculations

## Solution

### 1. Restored Working Template
Restored `dose/templates/admin/passthrough_embed.html` from working commit `f3e9f9c3` which had:
- Proper `body.polysaas-passthrough-embed-page` selector prefixes
- Conditional CSS for Odoo vs Mattermost layouts
- Correct flex layout with proper height calculations

### 2. Added Missing Handler Method
Added `passthrough_embed_template_context()` method to `OdooPassthroughHandler`:

```python
def passthrough_embed_template_context(self, request, upstream_path, **kwargs):
    """Provide Odoo-specific template context including the body scope flag."""
    print(f"[ODOO HANDLER] Setting embed_enable_odoo_body_scope=True for template")
    return {
        'embed_enable_odoo_body_scope': True
    }
```

This ensures the template applies the correct Odoo-specific CSS layout.

## Files Modified

1. **dose/passthrough/handlers/odoo_handler.py**
   - Added `passthrough_embed_template_context()` method
   - Sets `embed_enable_odoo_body_scope = True`

2. **dose/templates/admin/passthrough_embed.html**
   - Restored from commit f3e9f9c3
   - Contains working conditional CSS for Odoo vs Mattermost layouts

## Verification Steps

1. Navigate to Odoo passthrough: `http://localhost:8000/pt/admin/<odoo-endpoint>/`
2. Verify Odoo content:
   - ✅ Displays in content area to right of PolySaaS sidebar
   - ✅ Positioned directly under green orchestration bar
   - ✅ Fills full available width
   - ✅ Fills full available height with proper flex layout
   - ✅ All Odoo apps/icons visible and clickable
   - ✅ Odoo navigation bar visible at top of content area

## Technical Details

### CSS Layout Applied (Odoo-specific)
```css
body.polysaas-passthrough-embed-page {
    overflow-x: hidden !important;
}

.polysaas-passthrough-embed-wrap {
    display: flex !important;
    flex-direction: column !important;
    height: calc(100vh - var(--pss-header-h, 64px) - 42px) !important;
    min-height: 420px !important;
    max-height: calc(100vh - var(--pss-header-h, 64px) - 42px) !important;
    box-sizing: border-box !important;
}

.polysaas-passthrough-scope {
    position: relative !important;
    flex: 1 1 auto !important;
    min-height: 0 !important;
    width: 100% !important;
    overflow: hidden !important;
    box-sizing: border-box !important;
    background: #fff !important;
    padding: 0 !important;
    margin: 0 !important;
    display: flex !important;
    flex-direction: column !important;
}
```

### Key Differences from Mattermost Layout
- Odoo uses flex containment with `overflow: hidden` for proper SPA containment
- Mattermost uses `overflow: visible` and allows height to be auto
- Different height calculations account for different header/bar structures

## Architecture Notes

This fix follows the established SSO passthrough pattern:
1. Handler discovers endpoint type via `matches_endpoint()`
2. Handler provides app-specific template context via `passthrough_embed_template_context()`
3. Template applies conditional CSS based on app type flags
4. Each app gets its own optimized layout

## Related Documentation

- `documentation/BINGO_MATTERMOST_SSO_PASSTHROUGH_WORKING_2026-06-07.md`
- `.cursor/rules/passthrough-handler-isolation.mdc`
- `.cursor/rules/sso-architecture.mdc`

## Certification

Odoo passthrough layout verified working on 2026-06-09 by Michael.
- Odoo loads correctly in admin content area
- Layout matches design: sidebar left, green bar top, Odoo content fills remaining space
- All interactive elements functional
- No console errors
- Assets load correctly through proxy
