# How to Check Odoo Browser Cookies

## In Your Browser (Chrome/Firefox/Edge):

1. **Open DevTools** (F12)
2. Go to **Application** or **Storage** tab
3. Look for **Cookies** section
4. Find cookies for `polysaas.odoo.com`:
   - Look for: `session_id`, `session`, `odoo-session`, or any auth-related cookies
   - Note their values and expiration

5. **Check Request Headers** (Network tab):
   - Open any page in Odoo
   - Look at Network tab
   - Check headers sent - especially:
     - `Cookie` (all cookies sent)
     - `Origin`
     - `Referer`
     - `User-Agent`

## Key Questions:
- Are there any cookies that persist authentication?
- Do they have specific domain/path restrictions?
- What Origin/Referer does your browser send?

## For Our Proxy:
We need to either:
1. Extract these cookies and pass them through
2. Or find the actual authentication API that Odoo uses
3. Or capture the session establishment flow
