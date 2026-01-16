# PolySysMon Passthrough Handler: <base> Tag Injection

## Purpose
This handler customizes passthrough for the PolySysMon endpoint in PolySaaS. It ensures that the Vue SPA and its router work correctly when loaded via the Django admin passthrough by injecting a `<base href="/pt/admin/polysysmon/">` tag into the HTML `<head>`. This allows all relative asset and router paths to resolve properly, fixing blank content issues when PolySysMon is loaded at a subpath.

## Implementation Details
- The handler subclasses the base passthrough handler.
- After asset URL rewriting, it parses the HTML and injects the correct `<base>` tag.
- This is endpoint-specific logic and only applies to PolySysMon.
- All generic passthrough logic remains in the base handler.

## Location
- File: `dose/passthrough/handlers/polysysmon_handler.py`
- Template: `templates/passthrough/passthrough_content.html`

## Commit Message
```
fix(polysysmon): inject <base href="/pt/admin/polysysmon/"> for correct SPA routing

- Ensures PolySysMon Vue SPA works in admin passthrough by rewriting <base> tag
- Fixes blank content and router errors when loaded at a subpath
- Endpoint-specific logic isolated to PolySysMon handler
```

## Testing
- Visit the PolySysMon passthrough in the admin interface.
- Confirm the content loads and the Vue SPA router works as expected.
- Check browser dev tools: `<base href="/pt/admin/polysysmon/">` should appear in the HTML `<head>`.

---
This change resolves the blank PolySysMon passthrough issue and is safe for commit.
