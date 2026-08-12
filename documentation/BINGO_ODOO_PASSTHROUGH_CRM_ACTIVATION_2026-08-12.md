# BINGO: Odoo Passthrough CRM Activation Working

**Date:** 2026-08-12  
**Commit:** (to be inserted at push)  
**Status:** ✅ VERIFIED WORKING

## Summary

The Odoo passthrough endpoint for the `odoo2` tenant now renders correctly inside PolySniffer, with the PolySaaS admin sidebar fully suppressed and the full width available to Odoo. The CRM app activates and runs without the layout being obscured.

## Problem

When opening the Odoo passthrough endpoint through PolySniffer, the workspace placeholder was replaced by the passthrough object, but the PolySaaS admin sidebar remained visible, covering part of the Odoo interface. Earlier attempts also caused a brief flash of the sidebar before it disappeared, and the workspace placeholder did not reset automatically for a new session/window.

## Root Cause

- The left sidebar (`#dose-custom-sidebar`) was being shown by JavaScript inside `custom_sidebar.html` after the page loaded, overriding the initial CSS `display: none`.
- The workspace `sniff_shell` view was restoring the previous PolySniffer capture session from the Django session on every load, so the object auto-loaded and the placeholder was not preserved for a new window.

## Solution

### 1. Sidebar Suppression in `passthrough_embed.html`
- Added higher-specificity CSS rules targeting `body.polysaas-passthrough-embed-page` to hide `#dose-custom-sidebar` and set `grid-template-columns: 0 1fr` on the wrapper.
- Added a JavaScript guard in the `extrajs` block that force-sets `display: none !important`, `visibility: hidden !important`, and `grid-template-columns: 0 1fr !important` after the sidebar setup script runs.

### 2. Fresh Workspace on New Window
- Updated `dose/polysniffer/views/sniff_v2_workspace.py` so the `sniff_shell` view clears the previous capture/mode session keys when loaded without an explicit `mode` query parameter. This keeps the "Click Native or Passthrough" placeholder visible until the user explicitly starts a capture.

### 3. Odoo Provisioning Alignment
- Fixed `odoo.conf` `admin_passwd` to match `ODOO_MASTER_PASSWORD` so XML-RPC database provisioning succeeds.
- Confirmed `odoo2` tenant database provisions and the Odoo web interface is accessible through the passthrough endpoint.

## Evidence

Screenshot of the working passthrough showing the CRM app for `odoo2` with no PolySaaS sidebar and the green orchestration bar active:

![Odoo CRM passthrough for odoo2](assets/BINGO_ODOO_PASSTHROUGH_CRM_ACTIVATION_2026-08-12.png)

## Affected Files

- `dose/templates/admin/passthrough_embed.html`
- `dose/polysniffer/views/sniff_v2_workspace.py`
- `dose/polysniffer/sniff_v2_workspace.py` (session reset)
- `dose/admin_views.py` (`Http404` import)
- `odoo.conf` (inside Odoo container)

## Verification Steps

1. Open `/admin/polysniffer/sniff/localhost:8086/` in a fresh browser tab.
2. Confirm the placeholder message "Click Native or Passthrough to start capturing." persists.
3. Click **Start Passthrough**.
4. Confirm the Odoo interface loads without the PolySaaS left sidebar.
5. Activate the CRM app and confirm it renders correctly.

## BINGO

CRM app activation through the PolySniffer Odoo passthrough endpoint is working for `odoo2`.
