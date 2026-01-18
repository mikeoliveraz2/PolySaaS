"""
OSTicket Admin Integration
Displays OSTicket within Django admin interface - NOT in iframe, just server-side wrapping.
Uses the same URL rewriting and JavaScript interception strategy as the Flask proxy.
"""
import logging
import re
import os
from django.shortcuts import render
from django.contrib.admin.views.decorators import staff_member_required
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse, HttpResponseRedirect
from django.conf import settings
import requests
from bs4 import BeautifulSoup
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

logger = logging.getLogger(__name__)

# Separate log file for OSTicket debugging (in project root)
# Use __file__ to find project root (go up from dose/osticket_admin.py to project root)
# dose/osticket_admin.py -> dose/ -> project root
_project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OSTICKET_DEBUG_LOG = os.path.join(_project_root, 'osticket_debug.log')

# Test log file creation on module load
try:
    with open(OSTICKET_DEBUG_LOG, 'a', encoding='utf-8') as f:
        import datetime
        f.write(f"[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Module loaded - log file accessible\n")
        f.flush()
except Exception as e:
    pass  # Log file will be created on first write

def debug_log(message):
    """Write to separate debug log file"""
    try:
        import datetime
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open(OSTICKET_DEBUG_LOG, 'a', encoding='utf-8') as f:
            f.write(f"[{timestamp}] {message}\n")
            f.flush()  # Force write immediately
    except Exception as e:
        # If log fails, at least print to console
        print(f"[DEBUG_LOG ERROR] {e} - Message: {message}")

# Configuration (must match Flask proxy)
REAL_BASE = "https://oliverenterprises.app.saasify.cloud/scp/"
PROXY_PATH = "/admin/osticket/"

# CRITICAL: Module-level persistent session for maintaining OSTicket cookies across requests
# This allows login to persist and form submissions to maintain session state
_osticket_session = None

def get_osticket_session():
    """Get or create a persistent session for OSTicket requests"""
    global _osticket_session
    if _osticket_session is None:
        _osticket_session = requests.Session()
        retry = Retry(connect=3, backoff_factor=0.5)
        adapter = HTTPAdapter(max_retries=retry)
        _osticket_session.mount('http://', adapter)
        _osticket_session.mount('https://', adapter)
        print("[OSTICKET] Created persistent session for cookie management")
    return _osticket_session


def get_google_oauth_token(user):
    """Get Google OAuth2 token for the user"""
    from allauth.socialaccount.models import SocialToken
    from datetime import datetime, timezone

    try:
        token_obj = SocialToken.objects.filter(
            account__user=user,
            account__provider__iexact='google'
        ).first()

        if not token_obj:
            logger.debug(f"No Google token found for user {user.username}")
            return None

        # Check if token is expired
        now = datetime.now(timezone.utc)
        if token_obj.expires_at and token_obj.expires_at < now:
            logger.warning(f"Google token expired for user {user.username}, attempting refresh...")
            # Try to refresh token if refresh token is available
            if token_obj.token_secret:  # token_secret stores refresh token
                try:
                    import requests as req_lib
                    from django.conf import settings
                    from allauth.socialaccount.models import SocialApp

                    app = SocialApp.objects.get(provider='google')
                    refresh_response = req_lib.post(
                        'https://oauth2.googleapis.com/token',
                        data={
                            'client_id': app.client_id,
                            'client_secret': app.secret,
                            'refresh_token': token_obj.token_secret,
                            'grant_type': 'refresh_token'
                        },
                        timeout=10
                    )

                    if refresh_response.status_code == 200:
                        refresh_data = refresh_response.json()
                        token_obj.token = refresh_data['access_token']
                        if 'expires_in' in refresh_data:
                            from datetime import timedelta
                            token_obj.expires_at = now + timedelta(seconds=refresh_data['expires_in'])
                        token_obj.save()
                        logger.info(f"Google token refreshed for user {user.username}")
                    else:
                        logger.error(f"Failed to refresh Google token: {refresh_response.text}")
                        return None
                except Exception as e:
                    logger.error(f"Error refreshing Google token: {e}")
                    return None
            else:
                logger.warning(f"No refresh token available for user {user.username}")
                return None

        return token_obj.token
    except Exception as e:
        logger.error(f"Error getting Google OAuth token: {e}")
        return None



def doseify_html(html: str, current_path: str = '') -> str:
    """
    Convert incoming HTML: replace real URLs with proxy paths and inject JS interception.

    Args:
        html: The HTML content to process
        current_path: The current request path to detect if /scp/ is in the base

    Dynamically detects OSTicket's base:
    - If current_path contains /scp/ ΓåÆ relative paths are relative to /scp/
    - If current_path is root (/) ΓåÆ relative paths might still be in /scp/ context
      (check if HTML contains /scp/ links or forms)
    """
    original_html = html

    print(f"[DOSEIFY] ===== STARTING HTML PROCESSING =====")
    print(f"[DOSEIFY] Current path: {current_path}")
    print(f"[DOSEIFY] HTML size: {len(html)} bytes")
    print(f"[DOSEIFY] First 500 chars: {html[:500]}")

    # CRITICAL: Check what CSS/JS refs look like in raw HTML
    import re as re_module
    css_refs = re_module.findall(r'href="[^"]*\.css[^"]*"', html, re_module.IGNORECASE)
    js_refs = re_module.findall(r'src="[^"]*\.js[^"]*"', html, re_module.IGNORECASE)
    print(f"[DOSEIFY] CSS refs in HTML: {css_refs[:3]}")
    print(f"[DOSEIFY] JS refs in HTML: {js_refs[:3]}")

    # Detect if the request was for /scp/ path
    has_scp_in_path = '/scp/' in current_path if current_path else False

    # HEURISTIC: Even if path doesn't have /scp/, if HTML has /scp/ content,
    # it's probably /scp/ content being served (OSTicket root returns /scp/ relative paths)
    has_scp_in_html = ('/scp/' in html) or ('scp/login.php' in html) or ('/scp/dashboard' in html)

    # Final decision: use /scp/ base if either path or content suggests it
    use_scp_base = has_scp_in_path or has_scp_in_html

    if use_scp_base:
        their_base = "https://oliverenterprises.app.saasify.cloud/scp/"
        their_base_no_slash = "https://oliverenterprises.app.saasify.cloud/scp"
        our_scp_base = "/admin/osticket/scp/"
        detection_reason = "path" if has_scp_in_path else "HTML content"
        print(f"[DOSEIFY] ≡ƒöì Using /scp/ base (detected via {detection_reason})")
    else:
        their_base = "https://oliverenterprises.app.saasify.cloud/"
        their_base_no_slash = "https://oliverenterprises.app.saasify.cloud"
        our_scp_base = "/admin/osticket/"
        print(f"[DOSEIFY] ≡ƒöì Using root base")

    # CRITICAL: Replace paths SELECTIVELY based on type
    # - .php files in action=/href= (navigation/forms) ΓåÆ prepend our base /admin/osticket/
    # - assets (.css, .js, .img, etc., including .php in src=) ΓåÆ prepend their full base URL https://
    # DO NOT do broad replacements of https:// URLs to proxy paths - that breaks asset loading!

    # Second: Handle relative paths with NO leading slash (css/file.css, js/file.js, etc.)
    # These are ASSETS RELATIVE TO THE /SCP/ CONTEXT and must be fetched from their host with full domain prepended
    # css/login.css (in /scp/ context) ΓåÆ https://oliverenterprises.app.saasify.cloud/scp/css/login.css
    # js/script.js (in /scp/ context) ΓåÆ https://oliverenterprises.app.saasify.cloud/scp/js/script.js
    before = html
    css_js_pattern = r'(src|href)="(?!/)([^":]*\.(css|js|png|jpg|jpeg|gif|svg|woff|woff2|ttf|eot|ico))"'
    matches = re.findall(css_js_pattern, html, flags=re.IGNORECASE)
    print(f"[DOSEIFY] Found {len(matches)} relative asset paths: {[m[1] for m in matches[:5]]}")

    # For relative paths, we need to check if we're in /scp/ context and prepend accordingly
    if use_scp_base:
        # We're in /scp/ context, so prepend /scp/ to relative paths
        print(f"[DOSEIFY] ≡ƒöº Processing relative assets IN /scp/ context (use_scp_base={use_scp_base})")
        html = re.sub(css_js_pattern,
                       lambda m: f'{m.group(1)}="https://oliverenterprises.app.saasify.cloud/scp/{m.group(2)}"',
                       html,
                       flags=re.IGNORECASE)
        print(f"[DOSEIFY] Γ£à Relative assets NOW include /scp/ in URL")
    else:
        # We're at root, prepend root
        print(f"[DOSEIFY] ≡ƒöº Processing relative assets at ROOT context (use_scp_base={use_scp_base})")
        html = re.sub(css_js_pattern,
                       lambda m: f'{m.group(1)}="https://oliverenterprises.app.saasify.cloud/{m.group(2)}"',
                       html,
                       flags=re.IGNORECASE)
    if before != html:
        print(f"[DOSEIFY] Γ£à Prepended full OSTicket base to relative asset paths (css/js/img)")
        # Show what the rewritten paths look like now
        relative_assets_after = re.findall(r'(src|href)="[^"]*\.(css|js|png|jpg|gif)[^"]*"', html, re.IGNORECASE)
        print(f"[DOSEIFY] Sample rewritten relative paths: {relative_assets_after[:2]}")
    else:
        print(f"[DOSEIFY] ΓÜá∩╕Å No relative asset paths found to rewrite")

    # Third: Handle paths starting with / that are assets
    # /css/file.css ΓåÆ https://oliverenterprises.app.saasify.cloud/css/file.css
    # /js/script.js ΓåÆ https://oliverenterprises.app.saasify.cloud/js/script.js
    # >>>>>>>>>>>>>>>>>>>>>>>>>>>>>> SECTION 3: ABSOLUTE ASSET PATHS >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
    # Skip paths that are already external (https://) or are Django static/media
    before = html
    abs_asset_pattern = r'(src|href)="/([^"]*\.(css|js|png|jpg|jpeg|gif|svg|woff|woff2|ttf|eot|ico)(?:\?[^"]*)?)"'
    abs_matches = re.findall(abs_asset_pattern, html, flags=re.IGNORECASE)
    print(f"[DOSEIFY] >>>>>>>>>> SECTION 3 START: Rewriting absolute /asset paths <<<<<<<<<<")
    print(f"[DOSEIFY] Found {len(abs_matches)} absolute asset paths: {[m[1] for m in abs_matches[:5]]}")

    # Only replace if NOT already pointing to external domain and NOT Django static/media
    def replace_abs_asset(m):
        full_path = m.group(2)
        # Skip if it's already external or if it's Django static/media
        if full_path.startswith('admin/osticket') or full_path.startswith('static/') or full_path.startswith('media/'):
            return m.group(0)  # Return unchanged
        # Replace with full external domain
        return f'{m.group(1)}="https://oliverenterprises.app.saasify.cloud/{full_path}"'

    html = re.sub(abs_asset_pattern, replace_abs_asset, html, flags=re.IGNORECASE)
    if before != html:
        print(f"[DOSEIFY] Γ£à Prepended full OSTicket base to /asset paths")
    else:
        print(f"[DOSEIFY] ΓÜá∩╕Å No absolute asset paths found to rewrite")

    # >>>>>>>>>>>>>>>>>>>>>>>>>>>>>> SECTION 4: PHP FILES IN SRC= (DYNAMIC ASSETS) >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
    # Fourth: Handle .php files in src= attributes FIRST (dynamic asset generation like logo.php?login)
    # CRITICAL: These are ASSETS and should fetch from external host, NOT proxied through Django
    # src="logo.php?login" ΓåÆ src="https://oliverenterprises.app.saasify.cloud/scp/logo.php?login"
    # src="/scp/logo.php?login" ΓåÆ src="https://oliverenterprises.app.saasify.cloud/scp/logo.php?login"
    before = html
    print(f"[DOSEIFY] >>>>>>>>>> SECTION 4 START: Rewriting .php files in src= attributes <<<<<<<<<<")

    html = re.sub(r'src="(?!/)([^":]*\.php[^"]*)"',
                   lambda m: f'src="https://oliverenterprises.app.saasify.cloud/{our_scp_base.replace("/admin/osticket/", "")}{m.group(1)}"',
                   html,
                   flags=re.IGNORECASE)

    # Handle absolute /scp/.php in src - these are assets, prepend external base
    html = re.sub(r'src="/scp/([^"]*\.php[^"]*)"',
                   r'src="https://oliverenterprises.app.saasify.cloud/scp/\1"',
                   html,
                   flags=re.IGNORECASE)

    if before != html:
        print(f"[DOSEIFY] Γ£à Prepended external host to .php files in src= attributes (dynamic assets like logo.php)")
        print(f"[DOSEIFY] >>>>>>>>>> SECTION 4 END <<<<<<<<<")
    else:
        print(f"[DOSEIFY] Γä╣∩╕Å No .php files in src= attributes found")
        print(f"[DOSEIFY] >>>>>>>>>> SECTION 4 END <<<<<<<<<")

    # >>>>>>>>>>>>>>>>>>>>>>>>>>>>>> SECTION 5: PHP FILES IN ACTION=/HREF= (NAVIGATION) >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
    # Fifth: Handle relative .php paths in NAVIGATION contexts ONLY (action=, href=)
    # CRITICAL: These are FORM ACTIONS and LINKS, should go through Django proxy
    # login.php ΓåÆ /admin/osticket/{our_scp_base}/login.php (form submission)
    # pwreset.php ΓåÆ /admin/osticket/{our_scp_base}/pwreset.php (link)
    # Note: .php files in src= were already handled above as assets
    before = html
    print(f"[DOSEIFY] >>>>>>>>>> SECTION 5 START: Rewriting .php files in action=/href= <<<<<<<<<<")
    html = re.sub(r'(action|href)="(?!/)([^":]*\.php[^"]*)"',
                   lambda m: f'{m.group(1)}="{our_scp_base}{m.group(2)}"',
                   html)
    if before != html:
        print(f"[DOSEIFY] Γ£à Prepended {our_scp_base} to .php actions/links (navigation)")
        print(f"[DOSEIFY] >>>>>>>>>> SECTION 5 END <<<<<<<<<")
    else:
        print(f"[DOSEIFY] Γä╣∩╕Å No .php actions/links found to rewrite")
        print(f"[DOSEIFY] >>>>>>>>>> SECTION 5 END <<<<<<<<<")

    # >>>>>>>>>>>>>>>>>>>>>>>>>>>>>> SECTION 6: ABSOLUTE /SCP/ PATHS >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
    # Sixth: Handle absolute /scp/ paths AND relative scp/ paths in action/href
    # /scp/login.php ΓåÆ /admin/osticket/scp/login.php (so browser comes back through us)
    # scp/login.php ΓåÆ /admin/osticket/scp/login.php (relative path, no leading slash)
    # BUT: Skip paths that ALREADY have /admin/osticket/ in them (to avoid double wrapping)
    before = html
    print(f"[DOSEIFY] >>>>>>>>>> SECTION 6 START: Rewriting absolute /scp/ and relative scp/ paths <<<<<<<<<<")

    # Handle absolute /scp/ paths
    html = re.sub(r'(action|href)="/(?!admin/osticket/)scp/([^"]*)"',
                   r'\1="/admin/osticket/scp/\2"',
                   html)

    # Handle relative scp/ paths (without leading slash) - CRITICAL FOR LOGIN FORM
    html = re.sub(r'(action|href)="(?!/)scp/([^"]*)"',
                   r'\1="/admin/osticket/scp/\2"',
                   html)

    if before != html:
        print(f"[DOSEIFY] Γ£à Prepended /admin/osticket to /scp/ and scp/ paths (with guard against duplicates)")
        print(f"[DOSEIFY] >>>>>>>>>> SECTION 6 END <<<<<<<<")

    # >>>>>>>>>>>>>>>>>>>>>>>>>>>>>> SECTION 7: REMAINING /SCP/ PATHS (WITH GUARD) >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
    # Seventh: Fix onclick handlers and data attributes with /scp/ paths
    # onclick="window.location='/scp/...'" ΓåÆ onclick="window.location='/admin/osticket/scp/...'"
    # BUT: Skip paths that ALREADY have /admin/osticket/ in them
    # ALSO: Skip /scp/ that's part of external URLs (https://...)
    before = html
    print(f"[DOSEIFY] >>>>>>>>>> SECTION 7 START: Fixing remaining /scp/ paths (with guard) <<<<<<<<<<")
    html = re.sub(r"(?<!admin/osticket)(?<!\.cloud)(/scp/)",
                   r'/admin/osticket/scp/',
                   html)
    if before != html:
        print(f"[DOSEIFY] Γ£à Fixed remaining /scp/ paths in attributes (with guard against duplicates)")
        print(f"[DOSEIFY] >>>>>>>>>> SECTION 7 END <<<<<<<<<")

    if 'action="/scp/' in html or 'action="/' in html:
        action_matches = re.findall(r'action="[^"]*"', html)
        print(f"[DOSEIFY] WARNING: Found action attributes: {action_matches[:5]}")

    # Log ALL form actions for debugging
    all_actions = re.findall(r'action="[^"]*"', html)
    print(f"[DOSEIFY] All form actions in final HTML: {all_actions}")

    # >>>>>>>>>>>>>>>>>>>>>>>>>>>>>> FINAL VERIFICATION: CHECK ALL PATHS >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
    # CHECK: Verify CSS/JS paths are actually rewritten
    print(f"[DOSEIFY] >>>>>>>>>> FINAL VERIFICATION START <<<<<<<<<<")
    print(f"[DOSEIFY] ===== FINAL HTML VERIFICATION ======")
    css_refs_after = re.findall(r'href="[^"]*\.css[^"]*"', html, re.IGNORECASE)
    js_refs_after = re.findall(r'src="[^"]*\.js[^"]*"', html, re.IGNORECASE)
    print(f"[DOSEIFY] CSS refs AFTER processing: {css_refs_after[:3]}")
    print(f"[DOSEIFY] JS refs AFTER processing: {js_refs_after[:3]}")

    # Check for any relative paths that might have been missed
    relative_assets = re.findall(r'(href|src)="(?!https:|/|http)([^"]*\.(css|js|png|jpg|gif))"', html, re.IGNORECASE)
    if relative_assets:
        print(f"[DOSEIFY] ΓÜá∩╕Å WARNING: Still found {len(relative_assets)} unrewritten relative asset paths:")
        for match in relative_assets[:5]:
            print(f"[DOSEIFY]   {match[0]}=\"{match[1]}\"")
    else:
        print(f"[DOSEIFY] Γ£à All asset paths appear to be properly rewritten")
    print(f"[DOSEIFY] >>>>>>>>>> FINAL VERIFICATION END <<<<<<<<<")


    # Inject JavaScript to intercept AJAX/fetch requests and rewrite URLs
    js_intercept = """
    <script>
    console.log('[OSTicket Interceptor] Initializing...');

    (function() {
        // Intercept XMLHttpRequest
        const originalOpen = XMLHttpRequest.prototype.open;
        XMLHttpRequest.prototype.open = function(method, url, ...args) {
            if (typeof url === 'string') {
                const newUrl = url
                    .replace('https://oliverenterprises.app.saasify.cloud/scp/', '/admin/osticket/')
                    .replace('https://oliverenterprises.app.saasify.cloud', '/admin/osticket');
                if (newUrl !== url) {
                    console.log('[OSTicket XHR] Rewriting URL:', url, 'ΓåÆ', newUrl);
                }
                url = newUrl;
            }
            return originalOpen.apply(this, [method, url, ...args]);
        };
        console.log('[OSTicket Interceptor] XMLHttpRequest intercepted');

        // Intercept fetch
        const originalFetch = window.fetch;
        window.fetch = function(resource, config) {
            if (typeof resource === 'string') {
                // CRITICAL: Don't rewrite URLs that are already /admin/osticket/ paths
                if (resource.startsWith('/admin/osticket/')) {
                    console.log('[OSTicket Fetch] URL already proxied, passing through:', resource);
                    return originalFetch.apply(this, [resource, config]);
                }

                const newUrl = resource
                    .replace('https://oliverenterprises.app.saasify.cloud/scp/', '/admin/osticket/')
                    .replace('https://oliverenterprises.app.saasify.cloud', '/admin/osticket');
                if (newUrl !== resource) {
                    console.log('[OSTicket Fetch] Rewriting URL:', resource, 'ΓåÆ', newUrl);
                }
                resource = newUrl;
            }
            return originalFetch.apply(this, [resource, config]);
        };
        console.log('[OSTicket Interceptor] Fetch intercepted');

        // Intercept jQuery AJAX if it exists
        if (window.jQuery && window.jQuery.ajax) {
            const originalAjax = window.jQuery.ajax;
            window.jQuery.ajax = function(settings) {
                if (settings && settings.url) {
                    let newUrl = settings.url
                        .replace('https://oliverenterprises.app.saasify.cloud/scp/', '/admin/osticket/')
                        .replace('https://oliverenterprises.app.saasify.cloud', '/admin/osticket');

                    // Also handle relative paths like "login.php" or "index.php"
                    // These should become "/admin/osticket/login.php" etc.
                    if (!newUrl.startsWith('/') && !newUrl.startsWith('http') && !newUrl.startsWith('//')) {
                        // It's a relative path - prepend the osticket proxy path
                        newUrl = '/admin/osticket/' + newUrl;
                    }

                    if (newUrl !== settings.url) {
                        console.log('[OSTicket jQuery] Rewriting URL:', settings.url, 'ΓåÆ', newUrl);
                    }
                    settings.url = newUrl;
                }

                // INTERCEPT SUCCESS CALLBACK TO REWRITE REDIRECT URLS IN RESPONSE
                const originalSuccess = settings.success;
                if (originalSuccess) {
                    settings.success = function(data, status, xhr) {
                        // If response contains a redirect URL, rewrite it
                        if (data && data.redirect) {
                            console.log('[OSTicket jQuery] Response redirect before:', data.redirect);
                            data.redirect = data.redirect
                                .replace('https://oliverenterprises.app.saasify.cloud/scp/', '/admin/osticket/')
                                .replace('https://oliverenterprises.app.saasify.cloud', '/admin/osticket')
                                .replace('/scp/', '/admin/osticket/');
                            if (!data.redirect.startsWith('/admin/osticket') && data.redirect.startsWith('/scp/')) {
                                data.redirect = data.redirect.replace('/scp/', '/admin/osticket/');
                            }
                            console.log('[OSTicket jQuery] Response redirect after:', data.redirect);
                        }
                        return originalSuccess.call(this, data, status, xhr);
                    };
                }

                return originalAjax.apply(this, [settings]);
            };
            console.log('[OSTicket Interceptor] jQuery AJAX intercepted with response handling');
        }

        // Also set up a monitor to intercept jQuery if it loads AFTER this script
        if (!window.jQuery) {
            const checkJQuery = setInterval(function() {
                if (window.jQuery && window.jQuery.ajax && !window.jQuery.ajax.__osticketPatched) {
                    console.log('[OSTicket Interceptor] jQuery loaded after script, patching now...');
                    const originalAjax = window.jQuery.ajax;
                    window.jQuery.ajax = function(settings) {
                        if (settings && settings.url) {
                            let newUrl = settings.url
                                .replace('https://oliverenterprises.app.saasify.cloud/scp/', '/admin/osticket/')
                                .replace('https://oliverenterprises.app.saasify.cloud', '/admin/osticket');
                            if (!newUrl.startsWith('/') && !newUrl.startsWith('http') && !newUrl.startsWith('//')) {
                                newUrl = '/admin/osticket/' + newUrl;
                            }
                            if (newUrl !== settings.url) {
                                console.log('[OSTicket jQuery Delayed] Rewriting URL:', settings.url, 'ΓåÆ', newUrl);
                            }
                            settings.url = newUrl;
                        }
                        return originalAjax.apply(this, [settings]);
                    };
                    window.jQuery.ajax.__osticketPatched = true;
                    clearInterval(checkJQuery);
                }
            }, 100);
            setTimeout(() => clearInterval(checkJQuery), 5000); // Stop checking after 5 seconds
        }

        // Also intercept regular link clicks for fallback
        document.addEventListener('click', function(e) {
            const link = e.target.closest('a[href]');
            if (link) {
                let href = link.getAttribute('href');
                if (href && !href.startsWith('javascript:') && !href.startsWith('#')) {
                    const newHref = href
                        .replace('https://oliverenterprises.app.saasify.cloud/scp/', '/admin/osticket/')
                        .replace(/^\\/scp\\//, '/admin/osticket/')
                        .replace('https://oliverenterprises.app.saasify.cloud', '/admin/osticket');
                    if (newHref !== href) {
                        console.log('[OSTicket Link] Rewriting click href:', href, 'ΓåÆ', newHref);
                        link.setAttribute('href', newHref);
                    }
                }
            }
        }, true);
        console.log('[OSTicket Interceptor] Link click handler attached');

        // Intercept form submissions to rewrite action attributes
        document.addEventListener('submit', function(e) {
            const form = e.target;
            if (form && form.action) {
                let action = form.action;
                let newAction = action
                    .replace('https://oliverenterprises.app.saasify.cloud/scp/', '/admin/osticket/')
                    .replace('https://oliverenterprises.app.saasify.cloud', '/admin/osticket');

                // Handle relative paths
                if (!newAction.startsWith('/') && !newAction.startsWith('http')) {
                    newAction = '/admin/osticket/' + newAction;
                }

                if (newAction !== action) {
                    console.log('[OSTicket Form] Rewriting form action:', action, 'ΓåÆ', newAction);
                    form.action = newAction;
                }
            }
        }, true);
        console.log('[OSTicket Interceptor] Form submit handler attached');

        console.log('[OSTicket Interceptor] Γ£à All interceptors installed');
    })();
    </script>
    """

    # Inject before closing body tag or at end
    if '</body>' in html:
        html = html.replace('</body>', js_intercept + '</body>')
    else:
        html = html + js_intercept

    return html


@csrf_exempt
@staff_member_required
def osticket_admin_view(request, path=''):
    """
    Display OSTicket content wrapped within Django admin template.
    Uses handler system (same as PolySniffer) for consistency.

    CSRF exempt because OSTicket has its own CSRF protection mechanism.
    """
    # CRITICAL: Print FIRST before anything else to confirm view is called
    print("\n" + "="*80)
    print(f"[OSTICKET VIEW] ===== VIEW FUNCTION CALLED =====")
    print(f"[OSTICKET VIEW] Path: {request.path_info}")
    print(f"[OSTICKET VIEW] Path param: {path}")
    print(f"[OSTICKET VIEW] Method: {request.method}")
    print(f"[OSTICKET VIEW] Log file: {OSTICKET_DEBUG_LOG}")
    print("="*80 + "\n")

    # Log immediately at start - use both debug_log and print
    debug_log("="*80)
    debug_log("OSTICKET VIEW: FUNCTION CALLED")
    debug_log(f"Path: {request.path_info}")
    debug_log(f"Path parameter: {path}")
    debug_log(f"Method: {request.method}")

    from django.contrib import admin
    from dose.passthrough.handlers import get_handler_for_endpoint
    from dose.models import PassThroughEndpoint
    from dose.utils import get_current_tenant

    print(f"\n\n{'='*80}")
    print(f"[OSTICKET VIEW] ===== REQUEST RECEIVED =====")
    print(f"[OSTICKET VIEW] Called with path: {request.path_info}")
    print(f"[OSTICKET VIEW] Path parameter: {path}")
    print(f"{'='*80}\n")

    try:
        # Get OSTicket endpoint
        tenant = get_current_tenant(request) if request else None
        endpoint = PassThroughEndpoint.objects.filter(
            trigger_path__iexact='osticket',
            is_enabled=True
        ).first()

        if not endpoint:
            # Fallback: try to find by endpoint_url
            endpoint = PassThroughEndpoint.objects.filter(
                endpoint_url__icontains='osticket',
                is_enabled=True
            ).first()

        if not endpoint:
            # Second fallback: try supportsystem
            endpoint = PassThroughEndpoint.objects.filter(
                endpoint_url__icontains='supportsystem',
                is_enabled=True
            ).first()

        if not endpoint:
            print(f"[OSTICKET VIEW] ❌ No endpoint found - trigger_path='osticket' or endpoint_url contains 'osticket' or 'supportsystem'")
            return HttpResponse("OSTicket endpoint not found. Please configure a PassThroughEndpoint with trigger_path='osticket'.", status=404)

        print(f"[OSTICKET VIEW] ✅ Found endpoint: id={endpoint.id}, trigger_path={endpoint.trigger_path}, endpoint_url={endpoint.endpoint_url}")

        # Get handler (same as PolySniffer)
        handler = get_handler_for_endpoint(endpoint, request)
        logger.info(f"[OSTICKET VIEW] Using handler: {handler.__class__.__name__} for endpoint: {endpoint.trigger_path}")
        print(f"[OSTICKET VIEW] 🔍 Handler: {handler.__class__.__name__}, endpoint: {endpoint.trigger_path}, endpoint_url: {endpoint.endpoint_url}")

        # Use the path parameter if provided, otherwise extract from request.path_info
        if path:
            ext_path = path.strip('/')
        else:
            # Extract the path after /admin/osticket/
            ext_path = request.path_info.replace('/admin/osticket/', '', 1).strip('/')

        # Use handler for static asset handling FIRST (before defaulting to login.php)
        # This ensures CSS/JS requests are handled correctly
        if handler and ext_path:
            print(f"[OSTICKET VIEW] Checking static asset - ext_path: '{ext_path}', request.path: '{request.path}'")
            static_response = handler.handle_static_asset(request.path, ext_path)
            if static_response:
                logger.info(f"[OSTICKET VIEW] Handler {handler.__class__.__name__} handled static asset: {ext_path}")
                print(f"[OSTICKET VIEW] ✅ Static asset handled successfully: {ext_path}")
                return static_response
            else:
                print(f"[OSTICKET VIEW] ⚠️ Handler did not handle as static asset: {ext_path}")

        # BINGO COMMIT: If no path specified (root), default to login page
        if not ext_path:
            ext_path = 'login.php'
            print(f"[OSTICKET VIEW] No path specified, defaulting to login.php")

        # Build the real URL using handler (same as PolySniffer)
        target_url = handler.get_target_url(endpoint.endpoint_url, ext_path) if handler else (REAL_BASE + ext_path)

        print(f"[OSTICKET VIEW] Forwarding to: {target_url}")

        # Use persistent session to maintain cookies across requests
        sess = get_osticket_session()
        print(f"[OSTICKET VIEW] Using persistent session, current cookies: {sess.cookies.get_dict()}")

        # BINGO COMMIT: Simple cookie syncing from browser to session
        browser_cookies = request.COOKIES
        for cookie_name in ['OSTSESSID', 'csrf_token']:
            if cookie_name in browser_cookies:
                sess.cookies.set(cookie_name, browser_cookies[cookie_name])

        # Add query string if present
        if request.GET:
            from urllib.parse import urlencode
            target_url += '?' + urlencode(request.GET)

        # Start with MINIMAL headers (matching Flask proxy - it doesn't add many)
        request_headers = {}

        if request.method == 'POST':
            print(f"[OSTICKET VIEW] POST request")
            # Convert Django QueryDict to regular dict for proper requests.post() serialization
            post_data = {key: request.POST.getlist(key) if len(request.POST.getlist(key)) > 1 else request.POST[key]
                        for key in request.POST}

            # CRITICAL FIX: Add 'ajax': '1' parameter if this is a login request
            # OSTicket requires this for AJAX login requests (discovered via Chrome DevTools)
            if 'do' in post_data and post_data.get('do') == 'scplogin':
                if 'ajax' not in post_data:
                    post_data['ajax'] = '1'
                    print(f"[OSTICKET VIEW] Added 'ajax': '1' parameter to login POST")

            print(f"[OSTICKET VIEW] POST data being sent: {post_data}")

            # CRITICAL FIX: Add proper headers for AJAX login requests
            # These headers are required by OSTicket (discovered via Chrome DevTools)
            if 'do' in post_data and post_data.get('do') == 'scplogin':
                request_headers.update({
                    'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
                    'X-Requested-With': 'XMLHttpRequest',
                    'Referer': f'{REAL_BASE}login.php',
                    'Origin': 'https://oliverenterprises.app.saasify.cloud',
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                })
                print(f"[OSTICKET VIEW] Added AJAX headers for login request")

            # Capture traffic for PolySniffer
            import time
            start_time = time.time()

            response = sess.post(
                target_url,
                data=post_data,
                headers=request_headers,
                timeout=15,
                verify=False,
                allow_redirects=False  # Don't follow redirects - we'll handle them
            )

            duration_ms = (time.time() - start_time) * 1000

            # Log to PolySniffer
            try:
                from dose.polysniffer.models import TrafficLog
                TrafficLog.objects.create(
                    method='POST',
                    url=target_url,
                    path=ext_path or '/',
                    headers=dict(request_headers),
                    cookies=dict(sess.cookies),
                    query_params=dict(request.GET),
                    body=str(post_data),
                    status_code=response.status_code,
                    response_headers=dict(response.headers),
                    response_body=response.text[:50000],
                    response_size=len(response.content),
                    endpoint_name='OS Ticket',
                    user=request.user if request.user.is_authenticated else None,
                    duration_ms=duration_ms
                )
                print(f"[OSTICKET VIEW] Traffic logged to PolySniffer")
            except Exception as e:
                print(f"[OSTICKET VIEW] Failed to log to PolySniffer: {e}")

            print(f"[OSTICKET VIEW] POST response status: {response.status_code}")
            print(f"[OSTICKET VIEW] POST response headers: {dict(response.headers)}")
            print(f"[OSTICKET VIEW] POST Set-Cookie present: {'Set-Cookie' in response.headers}")
        else:
            print(f"[OSTICKET VIEW] GET request")
            # Add cache-busting headers to force OSTicket to generate FRESH CSRF token
            request_headers.update({
                'Cache-Control': 'no-cache, no-store, must-revalidate',
                'Pragma': 'no-cache',
                'Expires': '0'
            })
            print(f"[OSTICKET VIEW] Adding cache-busting headers to GET request")
            # Capture traffic for PolySniffer
            import time
            start_time = time.time()

            response = sess.get(
                target_url,
                headers=request_headers,
                timeout=15,
                verify=False,
                allow_redirects=False  # Don't follow redirects - we'll handle them
            )

            duration_ms = (time.time() - start_time) * 1000

            # Log to PolySniffer
            try:
                from dose.polysniffer.models import TrafficLog
                TrafficLog.objects.create(
                    method='GET',
                    url=target_url,
                    path=ext_path or '/',
                    headers=dict(request_headers),
                    cookies=dict(sess.cookies),
                    query_params=dict(request.GET),
                    body='',
                    status_code=response.status_code,
                    response_headers=dict(response.headers),
                    response_body=response.text[:50000],
                    response_size=len(response.content),
                    endpoint_name='OS Ticket',
                    user=request.user if request.user.is_authenticated else None,
                    duration_ms=duration_ms
                )
                print(f"[OSTICKET VIEW] Traffic logged to PolySniffer")
            except Exception as e:
                print(f"[OSTICKET VIEW] Failed to log to PolySniffer: {e}")

        # CRITICAL: Handle redirects with URL rewriting
        # If OSTicket sends a redirect (301/302/303/307), rewrite the Location header
        if response.status_code in [301, 302, 303, 307]:
            print(f"[OSTICKET VIEW] Γ£à Got redirect status: {response.status_code}")
            location = response.headers.get('Location', '')
            print(f"[OSTICKET VIEW] Original Location header: {location}")

            if location:
                # Simple and direct: prepend our base to any /scp/ paths
                new_location = location

                # If location is /scp or /scp/something, make it /admin/osticket/scp or /admin/osticket/scp/something
                if location.startswith('/scp'):
                    new_location = '/admin/osticket' + location
                    print(f"[OSTICKET VIEW] Γ£à Prepended /admin/osticket to /scp path")
                # If location is the full domain, replace domain with our base
                elif 'oliverenterprises.app.saasify.cloud/scp' in location:
                    new_location = location.replace('https://oliverenterprises.app.saasify.cloud/scp', '/admin/osticket/scp')
                    print(f"[OSTICKET VIEW] Γ£à Replaced full domain with /admin/osticket/scp")

                print(f"[OSTICKET VIEW] Rewritten Location header: {new_location}")

                # Return a redirect response with the rewritten URL
                # CRITICAL: Copy Set-Cookie headers so browser gets OSTicket session
                redirect_response = HttpResponseRedirect(new_location)

                # Copy cookies from OSTicket response to Django response
                if 'Set-Cookie' in response.headers:
                    print(f"[OSTICKET VIEW] Γ£à Copying Set-Cookie header from OSTicket")
                    from http.cookies import SimpleCookie
                    set_cookie_headers = response.raw.headers.getlist('Set-Cookie') if hasattr(response.raw.headers, 'getlist') else [response.headers.get('Set-Cookie')]
                    for cookie_header in set_cookie_headers:
                        if not cookie_header:
                            continue
                        print(f"[OSTICKET VIEW] Cookie header: {cookie_header}")
                        cookie = SimpleCookie()
                        cookie.load(cookie_header)
                        for key, morsel in cookie.items():
                            print(f"[OSTICKET VIEW] Setting cookie: {key}={morsel.value}")
                            redirect_response.set_cookie(
                                key=key,
                                value=morsel.value,
                                max_age=morsel.get('max-age', None),
                                expires=morsel.get('expires', None),
                                path=morsel.get('path', '/'),
                                domain=None,  # Let browser use current domain
                                secure=False,  # We're on localhost HTTP
                                httponly=morsel.get('httponly', False),
                                samesite=None
                            )
                else:
                    print(f"[OSTICKET VIEW] ΓÜá∩╕Å No Set-Cookie header in OSTicket response")

                return redirect_response

        print(f"[OSTICKET VIEW] Got status: {response.status_code}")
        print(f"[OSTICKET VIEW] Content-Type: {response.headers.get('content-type', 'unknown')}")
        print(f"[OSTICKET VIEW] Response size: {len(response.text) if response.text else 0} bytes")

        # CRITICAL: Check if this is an AJAX request
        # AJAX requests (like login POST) should return raw response, not wrapped in Django template
        is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.POST.get('ajax') == '1'
        if is_ajax:
            print(f"[OSTICKET VIEW] Γ£à AJAX request detected, returning raw response")
            django_response = HttpResponse(response.content, content_type=response.headers.get('content-type', 'text/html'), status=response.status_code)

            # Copy cookies from OSTicket response
            if 'Set-Cookie' in response.headers:
                from http.cookies import SimpleCookie
                set_cookie_headers = response.raw.headers.getlist('Set-Cookie') if hasattr(response.raw.headers, 'getlist') else [response.headers.get('Set-Cookie')]
                for cookie_header in set_cookie_headers:
                    if not cookie_header:
                        continue
                    cookie = SimpleCookie()
                    cookie.load(cookie_header)
                    for key, morsel in cookie.items():
                        django_response.set_cookie(
                            key=key,
                            value=morsel.value,
                            max_age=morsel.get('max-age', None),
                            expires=morsel.get('expires', None),
                            path=morsel.get('path', '/'),
                            domain=None,
                            secure=False,
                            httponly=morsel.get('httponly', False),
                            samesite=None
                        )
            return django_response

        # Check if response is HTML
        content_type = response.headers.get('content-type', '').lower()

        # Check if this is an asset request (CSS, JS, image, etc.)
        is_asset = any(ext in ext_path for ext in ['.css', '.js', '.png', '.jpg', '.jpeg', '.gif', '.svg', '.woff', '.woff2', '.ttf', '.eot', '.ico', '.map'])

        # If it's an asset, return it directly regardless of content
        if is_asset:
            print(f"[OSTICKET VIEW] Asset request detected ({ext_path}), returning directly with content-type: {content_type}")
            return HttpResponse(response.content, content_type=content_type)

        # For non-assets, check if HTML
        is_html = 'html' in content_type or (response.text.strip().startswith('<') and '<html' in response.text.lower())

        print(f"[OSTICKET VIEW] Is HTML: {is_html}")
        print(f"[OSTICKET VIEW] HTML check details:")
        print(f"[OSTICKET VIEW]   - content_type contains 'html': {'html' in content_type}")
        print(f"[OSTICKET VIEW]   - starts with '<': {response.text.strip().startswith('<')}")
        print(f"[OSTICKET VIEW]   - contains '<html': {'<html' in response.text.lower()}")

        # Debug: show first part of response
        if not is_asset:
            print(f"[OSTICKET VIEW] First 500 chars: {response.text[:500]}")
            if response.status_code >= 400:
                print(f"[OSTICKET VIEW] ΓÜá∩╕Å ERROR RESPONSE (status {response.status_code})")
                print(f"[OSTICKET VIEW] Full response:\n{response.text}")

        if is_html:
            debug_log("HTML detected - entering handler processing")
            # Use handler's process_html_response (same as PolySniffer)
            proxy_base = '/admin/osticket/'
            # Get base URL - must be external server, NOT localhost
            if handler:
                base_url = handler.get_base_url(endpoint.endpoint_url)
                debug_log(f"Handler provided base_url: {base_url}")
            else:
                # Extract external server URL from endpoint_url
                from urllib.parse import urlparse
                parsed = urlparse(endpoint.endpoint_url)
                base_url = f"{parsed.scheme}://{parsed.netloc}"
                debug_log(f"No handler, extracted base_url: {base_url}")

            # Verify base_url is NOT localhost
            if 'localhost' in base_url or '127.0.0.1' in base_url:
                # Extract from endpoint_url instead
                from urllib.parse import urlparse
                parsed = urlparse(endpoint.endpoint_url)
                base_url = f"{parsed.scheme}://{parsed.netloc}"
                debug_log(f"Fixed localhost base_url to: {base_url}")

            debug_log(f"About to call handler.process_html_response - handler exists: {handler is not None}, has method: {hasattr(handler, 'process_html_response') if handler else False}")
            if handler and hasattr(handler, 'process_html_response'):
                debug_log(f"Calling handler.process_html_response() - handler: {handler.__class__.__name__}")
                debug_log(f"proxy_base: {proxy_base}, base_url: {base_url}")
                try:
                    print(f"[OSTICKET VIEW] About to call handler.process_html_response - handler exists: {handler is not None}, has method: {hasattr(handler, 'process_html_response') if handler else False}")
                    debug_log(f"About to call handler.process_html_response - handler exists: {handler is not None}, has method: {hasattr(handler, 'process_html_response') if handler else False}")
                    if handler and hasattr(handler, 'process_html_response'):
                        print(f"[OSTICKET VIEW] Calling handler.process_html_response() - handler: {handler.__class__.__name__}")
                        debug_log(f"Calling handler.process_html_response() - handler: {handler.__class__.__name__}")
                        handler_result = handler.process_html_response(
                            response.text,
                            response,
                            target_url,
                            proxy_base,
                            base_url
                        )
                        print(f"[OSTICKET VIEW] Handler returned: {handler_result is not None}")
                        debug_log(f"Handler returned: {handler_result is not None}")
                    else:
                        print(f"[OSTICKET VIEW] ERROR: No handler or no process_html_response method")
                        debug_log(f"ERROR: No handler or no process_html_response method")
                        handler_result = None
                    head_content = ""  # Initialize for all code paths
                    doseified = ""  # Initialize for all code paths
                    if handler_result and handler_result[0] is not None:
                        # Handler processed the HTML - use it EXACTLY like PolySniffer does
                        processed_html, django_response = handler_result
                        debug_log("="*80)
                        debug_log("OSTICKET VIEW: Handler processed HTML")
                        debug_log(f"Handler: {handler.__class__.__name__}")
                        debug_log(f"HTML length: {len(processed_html)}")

                        # CRITICAL: Use handler output the SAME way as PolySniffer
                        # Only difference: Extract body for admin template (not full screen)
                        # Handler already processed all URLs correctly - no additional processing needed
                        from bs4 import BeautifulSoup
                        try:
                            soup = BeautifulSoup(processed_html, 'html.parser')
                            head = soup.find('head')
                            body = soup.find('body')
                            if head:
                                # Extract CSS/JS from head for template injection
                                head_elements = head.find_all(['link', 'script', 'style'])
                                head_content = '\n'.join([str(tag) for tag in head_elements])
                                debug_log(f"Extracted head: {len(head_elements)} elements")
                            if body:
                                # Extract body content only (handler's HTML is already correct)
                                doseified = str(body.decode_contents())
                                debug_log(f"Extracted body: {len(doseified)} chars")
                            else:
                                debug_log("WARNING: No <body> tag, using full HTML")
                                doseified = processed_html
                        except Exception as e:
                            debug_log(f"Error extracting body: {e}, using full HTML")
                            doseified = processed_html
                        debug_log("="*80)
                    else:
                        # Handler didn't process - this should not happen
                        debug_log("ERROR: Handler returned None result")
                        debug_log(f"handler_result: {handler_result}")
                        logger.error(f"[OSTICKET VIEW] Handler {handler.__class__.__name__} returned None result")
                        # Use raw HTML (handler should always process, but fallback to raw)
                        doseified = response.text
                        django_response = None
                except Exception as e:
                    debug_log(f"EXCEPTION in handler.process_html_response: {e}")
                    import traceback
                    debug_log(traceback.format_exc())
                    logger.error(f"[OSTICKET VIEW] Error in handler.process_html_response: {e}", exc_info=True)
                    # Use raw HTML on error (handler should handle everything)
                    doseified = response.text
                    django_response = None
            else:
                # No handler - this should not happen for OSTicket
                debug_log(f"ERROR: No handler - handler={handler}, hasattr={hasattr(handler, 'process_html_response') if handler else 'N/A'}")
                logger.error(f"[OSTICKET VIEW] Handler missing: handler={handler}, hasattr={hasattr(handler, 'process_html_response') if handler else 'N/A'}")
                # Use raw HTML (handler should always exist for OSTicket)
                doseified = response.text
                django_response = None

            # Get admin site context to preserve sidebar and admin UI
            from django.utils.safestring import mark_safe
            context = admin.site.each_context(request)

            # Debug: Log head content length
            debug_log(f"Head content length: {len(head_content)} chars")
            debug_log(f"Body content length: {len(doseified)} chars")
            if head_content:
                # Show sample of head content (first 500 chars)
                debug_log(f"Head content sample: {head_content[:500]}")

            context.update({
                'title': 'OSTicket',
                'osticket_content': mark_safe(doseified),
                'osticket_head': mark_safe(head_content) if head_content else '',
                'user': request.user,
            })

            # Log context before rendering
            print(f"[OSTICKET VIEW] Context keys: {list(context.keys())}")
            print(f"[OSTICKET VIEW] osticket_content length: {len(doseified)} chars")
            print(f"[OSTICKET VIEW] osticket_content sample (first 1000 chars):\n{doseified[:1000]}")

            # Render through admin template which extends admin base (BINGO commit used osticket_wrapper.html)
            result = render(request, 'admin/osticket_wrapper.html', context)

            # CRITICAL: Propagate cookies from persistent session to browser
            # Without this, browser doesn't send OSTSESSID on subsequent requests
            print(f"[OSTICKET VIEW] ≡ƒì¬ Propagating session cookies to browser...")
            for cookie_name, cookie_value in sess.cookies.items():
                print(f"[OSTICKET VIEW] Setting cookie: {cookie_name}={cookie_value}")
                result.set_cookie(
                    key=cookie_name,
                    value=cookie_value,
                    path='/admin/osticket/',  # Scope to osTicket paths only
                    domain=None,  # Let browser use current domain (127.0.0.1)
                    secure=False,  # We're on localhost HTTP
                    httponly=False,  # Allow JS to read (needed for fetch/XHR)
                    samesite='Lax'
                )

            # CRITICAL: Add cache-prevention headers to ensure browser gets fresh CSRF tokens
            result['Cache-Control'] = 'no-cache, no-store, must-revalidate, private'
            result['Pragma'] = 'no-cache'
            result['Expires'] = '0'
            print(f"[OSTICKET VIEW] Γ£à Added cache-prevention headers to response")

            print(f"[OSTICKET VIEW] Template rendered successfully, status={result.status_code}")
            return result
        else:
            # Non-HTML content or error - show debug info
            print(f"[OSTICKET VIEW] Non-HTML content, showing error")
            import traceback

            if response.status_code >= 400:
                # Error response - show diagnostic info
                context = {
                    'error': f'HTTP {response.status_code} from OSTicket',
                    'debug_info': f"""Endpoint: {target_url}
Status: {response.status_code}
Content-Type: {content_type}
Response Size: {len(response.text)} bytes
Response Text:
{response.text[:500]}""",
                    'title': 'OSTicket Error'
                }
                return render(request, 'admin/osticket_error.html', context)
            else:
                # Non-error non-HTML - return directly (JSON, image, PDF, etc.)
                django_response = HttpResponse(response.content, content_type=content_type, status=response.status_code)

                # CRITICAL: Rewrite Set-Cookie headers for JSON responses (AJAX login)
                if 'Set-Cookie' in response.headers:
                    print(f"[OSTICKET VIEW] Found Set-Cookie in non-HTML response")
                    from http.cookies import SimpleCookie

                    # Parse and rewrite cookies
                    set_cookie_headers = response.raw.headers.getlist('Set-Cookie') if hasattr(response.raw.headers, 'getlist') else [response.headers.get('Set-Cookie')]

                    for cookie_header in set_cookie_headers:
                        if not cookie_header:
                            continue
                        print(f"[OSTICKET VIEW] Original cookie: {cookie_header}")

                        cookie = SimpleCookie()
                        cookie.load(cookie_header)

                        for key, morsel in cookie.items():
                            django_response.set_cookie(
                                key=key,
                                value=morsel.value,
                                max_age=morsel.get('max-age', None),
                                expires=morsel.get('expires', None),
                                path=morsel.get('path', '/'),
                                domain=None,  # Let Django use current domain
                                secure=False,  # Don't require HTTPS for localhost
                                httponly=morsel.get('httponly', False),
                                samesite=None
                            )
                            print(f"[OSTICKET VIEW] Set cookie '{key}' on response")

                return django_response

    except Exception as e:
        print(f"[OSTICKET VIEW] Exception: {e}")
        logger.error(f"[OSTICKET] Error: {e}", exc_info=True)
        import traceback
        context = {
            'error': str(e),
            'debug_info': traceback.format_exc(),
            'title': 'OSTicket Error'
        }
        return render(request, 'admin/osticket_error.html', context)
