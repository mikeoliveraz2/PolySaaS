# Iframe Handling Techniques Reference

## Policy Clarification

**Our Approach:**
- We will **not** use iframes as our primary solution for passthrough applications
- However, if an external passthrough application uses iframes internally, that's acceptable (we can't control their implementation)
- All is not lost - there are techniques to handle iframe-protected applications if we encounter them

## Technique Comparison Table

| Level | Technique | Works even if target does… | Real examples already running | Effort |
|-------|-----------|---------------------------|------------------------------|--------|
| 1 | Simple iframe + DOM injection | Normal CSP, no frame-busting | Old Zendesk, HubSpot (classic), Stripe Dashboard | 5 minutes |
| 2 | iframe + Playwright browser in proxy mode (stream the remote page into your own iframe) | X-Frame-Options, CSP frame-ancestors, frame-busting scripts | Intercom inbox, old Salesforce Classic, some banking portals | 1–2 hours |
| 3 | Full visual proxy (Puppeteer/Playwright mirrors the page, re-serves every asset through your domain) | All of the above + fingerprinting + Cloudflare iframe protection | Linear.app (full working mirror), ClickUp dashboard, Figma file list (read-only), even parts of Gmail itself if you want to go crazy | 1 weekend |
| 4 | Hybrid rewrite (API for data + visual proxy only for the parts that are iframe-only) | Literally anything short of DRM video | Most modern SPAs that hide juicy parts in iframes (Notion's own editor, Airtable interfaces, etc.) | Most bulletproof |

## Notes

- **Level 1**: Quick solution for basic iframe embedding when CSP allows it
- **Level 2**: More robust, handles frame-busting scripts and CSP restrictions
- **Level 3**: Most comprehensive but resource-intensive, requires full page mirroring
- **Level 4**: Best approach for modern SPAs - use API for data, visual proxy only where needed

## When to Use

These techniques should only be considered if:
1. An external service we're proxying uses iframes internally
2. We encounter frame-busting or CSP restrictions that prevent normal proxying
3. A specific integration requires iframe-based content that can't be accessed via API

## Current Implementation

Our current passthrough architecture uses:
- Direct HTML proxying with URL rewriting (for scraper types)
- OAuth2 API passthrough (for API types)
- No iframes in our implementation

If we encounter iframe-protected services in the future, refer to this table for appropriate techniques.

