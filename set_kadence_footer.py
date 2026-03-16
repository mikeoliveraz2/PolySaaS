"""
Set Kadence footer layout by saving settings through the Customizer AJAX API.

Key setting: footer_items - controls which widgets go in which rows/columns.
The Kadence footer builder stores items as a nested structure:
{
  "top": {"top_left": [], "top_left_center": [], "top_center": [], "top_right_center": [], "top_right": []},
  "middle": {"middle_left": [], "middle_left_center": [], "middle_center": [], "middle_right_center": [], "middle_right": []},
  "bottom": {"bottom_left": [], "bottom_left_center": [], "bottom_center": [], "bottom_right_center": [], "bottom_right": []}
}
"""
import requests, json, sys, re, time, uuid
sys.stdout.reconfigure(encoding='utf-8')

AZURE = "https://azure-nightingale-589250.hostingersite.com"

# Create a session for cookie-based auth (admin login)
admin = requests.Session()
admin.headers.update({'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0'})

# Login to WordPress admin
print("Step 1: Logging into WordPress admin...")
login_page = admin.get(f"{AZURE}/wp-login.php", timeout=30)

login_data = {
    'log': 'mikeoliveraz@gmail.com',
    'pwd': 'M@ster119611p',
    'wp-submit': 'Log In',
    'redirect_to': f'{AZURE}/wp-admin/',
    'testcookie': '1',
}
admin.cookies.set('wordpress_test_cookie', 'WP+Cookie+check')

login_r = admin.post(f"{AZURE}/wp-login.php", data=login_data, allow_redirects=True, timeout=30)
print(f"  Login redirect URL: {login_r.url}")
print(f"  Cookies: {list(admin.cookies.keys())}")

# Check if logged in by accessing wp-admin
admin_check = admin.get(f"{AZURE}/wp-admin/", timeout=30, allow_redirects=True)
print(f"  Admin page status: {admin_check.status_code}")
print(f"  Admin page URL: {admin_check.url}")
logged_in = 'wp-admin' in admin_check.url and 'wp-login' not in admin_check.url

if not logged_in:
    print("ERROR: Could not log in to WordPress admin!")
    print("Trying REST API approach instead...")

# REST API session  
api = requests.Session()
api.auth = ("mikeoliveraz@gmail.com", "vlop MpGU Os2V xDSI C6T7 2fAN")

if logged_in:
    # Get the Customizer page to extract nonce and changeset UUID
    print("\nStep 2: Loading Customizer to get nonce...")
    cust_r = admin.get(f"{AZURE}/wp-admin/customize.php", timeout=30)
    print(f"  Customizer status: {cust_r.status_code}")

    # Extract nonce for customize_save
    nonce_match = re.search(r'"save"\s*:\s*"([a-f0-9]+)"', cust_r.text)
    if not nonce_match:
        nonce_match = re.search(r'"nonce"\s*:\s*"([a-f0-9]+)"', cust_r.text)
    
    changeset_match = re.search(r'"changeset_uuid"\s*:\s*"([^"]+)"', cust_r.text)
    
    if nonce_match:
        nonce = nonce_match.group(1)
        print(f"  Nonce: {nonce}")
    else:
        print("  WARNING: Could not find nonce")
        nonce = None
    
    if changeset_match:
        changeset_uuid = changeset_match.group(1)
        print(f"  Changeset UUID: {changeset_uuid}")
    else:
        changeset_uuid = str(uuid.uuid4())
        print(f"  Generated changeset UUID: {changeset_uuid}")
    
    # The Kadence footer_items setting structure
    footer_items = {
        "top": {
            "top_left": [],
            "top_left_center": [],
            "top_center": [],
            "top_right_center": [],
            "top_right": []
        },
        "middle": {
            "middle_left": ["footer-widget1"],
            "middle_left_center": [],
            "middle_center": ["footer-widget2"],
            "middle_right_center": [],
            "middle_right": ["footer-widget3"]
        },
        "bottom": {
            "bottom_left": [],
            "bottom_left_center": [],
            "bottom_center": ["footer-html"],
            "bottom_right_center": [],
            "bottom_right": []
        }
    }

    # Also need middle row columns set to 3
    footer_middle_columns = 3

    if nonce:
        print("\nStep 3: Saving footer settings via Customizer AJAX...")
        
        customized = {
            "footer_items": {
                "value": footer_items,
                "type": "theme_mod",
                "user_id": 1
            },
            "footer_middle_columns": {
                "value": footer_middle_columns,
                "type": "theme_mod",
                "user_id": 1
            }
        }

        save_data = {
            'action': 'customize_save',
            'wp_customize': 'on',
            'customize-save-nonce': nonce,
            'nonce': nonce,
            'customize_changeset_uuid': changeset_uuid,
            'customize_changeset_status': 'publish',
            'customized': json.dumps(customized)
        }

        save_r = admin.post(
            f"{AZURE}/wp-admin/admin-ajax.php",
            data=save_data,
            timeout=30
        )
        print(f"  Save status: {save_r.status_code}")
        print(f"  Save response: {save_r.text[:500]}")

# Regardless of admin login, also try the REST API changeset approach
print("\n--- REST API changeset approach ---")

# Create a changeset via REST API
changeset_data = {
    "footer_items": {
        "value": {
            "top": {
                "top_left": [],
                "top_left_center": [],
                "top_center": [],
                "top_right_center": [],
                "top_right": []
            },
            "middle": {
                "middle_left": ["footer-widget1"],
                "middle_left_center": [],
                "middle_center": ["footer-widget2"],
                "middle_right_center": [],
                "middle_right": ["footer-widget3"]
            },
            "bottom": {
                "bottom_left": [],
                "bottom_left_center": [],
                "bottom_center": ["footer-html"],
                "bottom_right_center": [],
                "bottom_right": []
            }
        },
        "type": "theme_mod"
    },
    "footer_middle_columns": {
        "value": 3,
        "type": "theme_mod"
    }
}

# Try to create/update a changeset post
new_uuid = str(uuid.uuid4())
changeset_post = {
    "title": new_uuid,
    "status": "publish",
    "content": json.dumps(changeset_data)
}

# WordPress Customizer changesets are stored as posts of type 'customize_changeset'
# The slug is the UUID
r = api.post(
    f"{AZURE}/wp-json/customize/v1/changesets",
    json=changeset_post,
    timeout=30
)
print(f"Changeset API: {r.status_code}")
if r.status_code != 200:
    print(f"Response: {r.text[:300]}")

# Alternative: try the standard posts endpoint with customize_changeset type
r2 = api.get(
    f"{AZURE}/wp-json/wp/v2/types",
    timeout=30
)
print(f"\nPost types: {r2.status_code}")
if r2.status_code == 200:
    types = r2.json()
    if 'customize_changeset' in types:
        print("  customize_changeset type exists!")
        # Try to create a changeset post
        cs_data = {
            "title": new_uuid,
            "slug": new_uuid,
            "status": "publish",
            "content": json.dumps(changeset_data)
        }
        r3 = api.post(
            f"{AZURE}/wp-json/wp/v2/customize_changesets",
            json=cs_data,
            timeout=30
        )
        print(f"  Create changeset: {r3.status_code}")
        print(f"  Response: {r3.text[:300]}")
