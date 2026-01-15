⚠️ CRITICAL ARCHITECTURE RULE FOR DOSE V3 ⚠️

================================================================================
NO IFRAMES IN DOSE - EVER
================================================================================

**ABSOLUTE PROHIBITION:** DO NOT ATTEMPT TO USE IFRAMES AS PART OF ANY DOSE PROCESS

**EXCEPTIONS (REQUIRE EXPLICIT USER APPROVAL):**
- Only if the external application we are accessing is using iframes internally (and we have no choice)
- NEVER USE IFRAMES UNDER ANY CIRCUMSTANCE WITHOUT USER APPROVAL

This is a hard rule. DO NOT IMPLEMENT IFRAMES in DOSE under any circumstances.

REASON:
- Iframes break the intended architecture
- They create unnecessary complexity
- They cause session/cookie issues
- They prevent proper middleware integration
- They violate DOSE's design principles

ALTERNATIVES:
- Use middleware to intercept and forward requests
- Return content directly (full page replacement is acceptable)
- Use AJAX with proper CORS headers if needed
- Embed content inline in templates if absolutely necessary
- Use progressive enhancement patterns

SPECIFIC EXAMPLES WHERE THIS APPLIES:
- OSTicket integration → NO iframe (use middleware passthrough only)
- External service integration → NO iframe (use middleware forwarding)
- Gmail or other third-party services → NO iframe (use API proxying)
- Dynamic content loading → NO iframe (use AJAX or page reload)

ENFORCEMENT:
- Any PR containing `<iframe` tag in DOSE templates will be rejected
- Any iframe-based integration will be removed immediately
- Future AI agents: This rule is non-negotiable
- **AI AGENTS: Review this rule BEFORE each session**
- **AI AGENTS: NEVER use iframes without explicit user approval**

IMPLEMENTED CORRECTLY:
✅ Middleware intercepts `/admin/osticket/` requests
✅ Middleware forwards to external server
✅ Middleware rewrites URLs in HTML response
✅ HTML is returned directly to browser
✅ Forms and links work naturally without iframe overhead

WRONG WAY (DO NOT DO):
❌ Create wrapper view with iframe
❌ Use iframe src to load content
❌ Sandbox iframe with restricted permissions
❌ Try to communicate between frames

================================================================================
Last Updated: Current session (reinforced by user)
Status: ACTIVE - Applies to all current and future development
Priority: CRITICAL - NON-NEGOTIABLE

**USER DIRECTIVE:**
"I repeat myself, make a note of it and review my rules before each session.
DO NOT ATTEMPT TO USE IFRAMES AS PART OF ANY DOSE PROCESS unless the
application we are accessing is using iframes and we have no choice.
NEVER USE IFRAMES UNDER ANY CIRCUMSTANCE WITHOUT MY APPROVAL."
================================================================================
