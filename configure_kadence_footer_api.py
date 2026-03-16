"""
Configure Kadence footer layout via WordPress Customizer API.
Since we're now logged in as admin and have published Widget 1 to the middle row,
we can read the current theme_mods_kadence option and build on it.

Strategy: Use a mini PHP helper uploaded as a must-use plugin to read/write
theme_mods programmatically via a REST endpoint.
"""
import requests, json, sys, time
sys.stdout.reconfigure(encoding='utf-8')

AZURE = "https://azure-nightingale-589250.hostingersite.com"
s = requests.Session()
s.auth = ("mikeoliveraz@gmail.com", "vlop MpGU Os2V xDSI C6T7 2fAN")

# First, let's see what the Customizer changeset looks like after publishing
# by reading the theme_mods through a custom REST route

# Step 1: Create a tiny PHP helper as a page template that outputs theme_mods
# We'll use the wp-json/wp/v2/settings endpoint to see what's available
r = s.get(f"{AZURE}/wp-json/wp/v2/settings", timeout=30)
print(f"Settings endpoint: {r.status_code}")
if r.status_code == 200:
    settings = r.json()
    # Look for any footer-related settings
    footer_keys = [k for k in settings.keys() if 'footer' in k.lower()]
    print(f"Footer-related settings: {footer_keys}")

# Step 2: Try to read theme_mods via wp/v2/themes endpoint
r2 = s.get(f"{AZURE}/wp-json/wp/v2/themes?status=active", timeout=30)
print(f"\nThemes endpoint: {r2.status_code}")
if r2.status_code == 200:
    themes = r2.json()
    for t in themes:
        print(f"  Active theme: {t.get('name', {}).get('rendered', 'unknown')}")
        if 'theme_mods' in t:
            print(f"  Has theme_mods: {list(t['theme_mods'].keys())[:20]}")

# Step 3: Let's try to use the REST API to upload a small PHP file as a must-use plugin
# that registers a custom REST route for reading/writing theme_mods
php_code = '''<?php
/*
Plugin Name: PolySaaS Theme Mods API
Description: Temporary helper for reading/writing Kadence theme mods via REST
*/

add_action('rest_api_init', function() {
    register_rest_route('polysaas/v1', '/theme-mods', array(
        'methods' => 'GET',
        'callback' => function() {
            $mods = get_theme_mods();
            $footer_mods = array();
            foreach ($mods as $key => $val) {
                if (strpos($key, 'footer') !== false) {
                    $footer_mods[$key] = $val;
                }
            }
            return new WP_REST_Response($footer_mods, 200);
        },
        'permission_callback' => function() {
            return current_user_can('manage_options');
        }
    ));

    register_rest_route('polysaas/v1', '/theme-mods', array(
        'methods' => 'POST',
        'callback' => function($request) {
            $mods = $request->get_json_params();
            foreach ($mods as $key => $val) {
                set_theme_mod($key, $val);
            }
            return new WP_REST_Response(array('updated' => array_keys($mods)), 200);
        },
        'permission_callback' => function() {
            return current_user_can('manage_options');
        }
    ));
});
'''

# Upload the PHP helper as a regular file via the media library
# WordPress won't allow .php uploads by default, so let's try a different approach
# We can use the Customizer's customize_save AJAX endpoint

# Actually, let's try a direct approach - use the admin to install a plugin
# Or even simpler: use WP's built-in evaluate-PHP capability if available

# Step 4: Let's try the most direct approach - use WordPress admin login session
# to POST to admin-ajax.php with customize_save action
print("\n--- Trying to use customize_save via admin session ---")

# First login to get cookies
login_data = {
    'log': 'mikeoliveraz@gmail.com',
    'pwd': 'M@ster119611p',
    'wp-submit': 'Log In',
    'redirect_to': f'{AZURE}/wp-admin/',
    'testcookie': '1',
}
login_r = s.post(f"{AZURE}/wp-login.php", data=login_data, allow_redirects=True, timeout=30)
print(f"Login status: {login_r.status_code}")
print(f"Redirected to: {login_r.url}")
logged_in = 'wp-admin' in login_r.url or login_r.status_code == 200

if logged_in:
    # Get the Customizer page to extract nonce
    customizer_r = s.get(
        f"{AZURE}/wp-admin/customize.php?autofocus[panel]=kadence_customizer_footer",
        timeout=30
    )
    print(f"Customizer page: {customizer_r.status_code}")

    # Extract nonce from the page
    import re
    nonce_match = re.search(r'"nonce":"([a-f0-9]+)"', customizer_r.text)
    if not nonce_match:
        nonce_match = re.search(r'_wpnonce=([a-f0-9]+)', customizer_r.text)
    if not nonce_match:
        nonce_match = re.search(r'"customize-save":"([a-f0-9]+)"', customizer_r.text)

    if nonce_match:
        nonce = nonce_match.group(1)
        print(f"Found nonce: {nonce}")
    else:
        # Try to find any nonce patterns
        all_nonces = re.findall(r'"([^"]+)"\s*:\s*"([a-f0-9]{10})"', customizer_r.text)
        print(f"All possible nonces: {all_nonces[:10]}")
        nonce = None

    # Also look for the changeset UUID
    changeset_match = re.search(r'"changeset_uuid"\s*:\s*"([^"]+)"', customizer_r.text)
    if changeset_match:
        changeset_uuid = changeset_match.group(1)
        print(f"Changeset UUID: {changeset_uuid}")

    # Look for all _customize settings patterns
    settings_match = re.findall(r'"settings"\s*:\s*\{([^}]{1,500})', customizer_r.text)
    if settings_match:
        print(f"\nCustomizer settings patterns found:")
        for sm in settings_match[:3]:
            print(f"  {sm[:200]}")

    # Let's extract the current footer_items setting name pattern
    footer_pattern = re.findall(r'(kadence_customizer_footer[^"]*|footer_[a-z_]+_items[^"]*)', customizer_r.text)
    print(f"\nFooter setting patterns: {list(set(footer_pattern))[:20]}")

    # Look for the specific footer builder settings
    builder_patterns = re.findall(r'"(footer[^"]*(?:item|row|column|builder|layout|middle)[^"]*)"', customizer_r.text)
    print(f"\nFooter builder patterns: {list(set(builder_patterns))[:20]}")
