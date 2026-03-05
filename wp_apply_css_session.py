"""Apply CSS via WordPress admin by logging in with session cookies."""
import requests
import re

SITE = "https://azure-nightingale-589250.hostingersite.com"
LOGIN_URL = f"{SITE}/wp-login.php"
CUSTOMIZE_URL = f"{SITE}/wp-admin/customize.php"

USERNAME = "mikeoliveraz@gmail.com"
PASSWORD = "M@ster119611p"

CSS = """/* ================================================================
   PolySaaS Site-Wide Brand Uniformity CSS
   Applied by Cursor — 2026-03-05
   ================================================================ */

#brxe-9d3229 {
    background-image: none !important;
    background-color: transparent !important;
}

#brxe-spdnfe {
    background-color: #003399 !important;
    color: #ffffff !important;
}
#brxe-spdnfe:hover {
    background-color: #03a9f4 !important;
}

#brxe-108a27 {
    background-color: #003399 !important;
    color: #ffffff !important;
}
#brxe-108a27:hover {
    background-color: #03a9f4 !important;
}

#brxe-5a8e5d {
    background-image: linear-gradient(180deg, #e0e0e0, #81d4fa) !important;
}

#brxe-a41c97 {
    background-image: linear-gradient(180deg, #81d4fa, #e0e0e0) !important;
}

#brxe-d09dd8 {
    background-image: linear-gradient(180deg, #e0e0e0, #81d4fa) !important;
}

#brxe-48433c,
#brxe-ebdc99,
#brxe-c34c6b,
#brxe-c42948,
#brxe-3d9d44,
#brxe-212ef4,
#brxe-c84666,
#brxe-d99909,
#brxe-5043f6,
#brxe-bb6825 {
    background-color: #f5f5f5 !important;
}

#brxe-77ca79 .icon,
#brxe-77ca79 .icon a,
#brxe-f81cf6 .icon,
#brxe-f81cf6 .icon a,
#brxe-16b8fe .icon,
#brxe-16b8fe .icon a,
#brxe-1088c8 .icon,
#brxe-1088c8 .icon a,
#brxe-9a18af .icon,
#brxe-9a18af .icon a,
#brxe-444777 .icon,
#brxe-444777 .icon a {
    color: #03a9f4 !important;
}

#brxe-d5dad2,
#brxe-454ad3,
#brxe-f09dcf {
    color: #03a9f4 !important;
}

#brxe-lxtgtl {
    background-color: #003399 !important;
    color: #ffffff !important;
}
#brxe-lxtgtl:hover { background-color: #03a9f4 !important; }

#brxe-klbakr {
    background-color: #003399 !important;
    color: #ffffff !important;
}
#brxe-klbakr:hover { background-color: #03a9f4 !important; }

#brxe-azcciv {
    background-color: #003399 !important;
    color: #ffffff !important;
}
#brxe-azcciv:hover { background-color: #03a9f4 !important; }

#brxe-jzzqut {
    background-color: #003399 !important;
    color: #ffffff !important;
}
#brxe-jzzqut:hover { background-color: #03a9f4 !important; }

#brxe-knhbzg {
    background-color: #003399 !important;
    color: #ffffff !important;
}
#brxe-knhbzg:hover { background-color: #03a9f4 !important; }

#brxe-moougs {
    background-color: #003399 !important;
    color: #ffffff !important;
}
#brxe-moougs:hover { background-color: #03a9f4 !important; }

#brxe-vfwohf {
    background-color: #003399 !important;
    color: #ffffff !important;
}
#brxe-vfwohf:hover { background-color: #03a9f4 !important; }

#brxe-furbff {
    background-color: #003399 !important;
    color: #ffffff !important;
}
#brxe-furbff:hover { background-color: #03a9f4 !important; }

#brxe-mhyjsp {
    background-color: #003399 !important;
    color: #ffffff !important;
}
#brxe-mhyjsp:hover { background-color: #03a9f4 !important; }

#brxe-pnmgpm {
    background-color: #003399 !important;
    color: #ffffff !important;
}
#brxe-pnmgpm:hover { background-color: #03a9f4 !important; }

#brxe-hhhbrs {
    background-color: #003399 !important;
    color: #ffffff !important;
}
#brxe-hhhbrs:hover { background-color: #03a9f4 !important; }

#brxe-llvriy {
    background-color: #003399 !important;
    color: #ffffff !important;
}
#brxe-llvriy:hover { background-color: #03a9f4 !important; }

#brxe-jfoddi {
    background-color: #003399 !important;
    color: #ffffff !important;
}
#brxe-jfoddi:hover { background-color: #03a9f4 !important; }

#brxe-rdjkmy {
    background-color: #003399 !important;
    color: #ffffff !important;
}
#brxe-rdjkmy:hover { background-color: #03a9f4 !important; }

#brxe-lqyjnf {
    background-color: #003399 !important;
    color: #ffffff !important;
}
#brxe-lqyjnf:hover { background-color: #03a9f4 !important; }

#brxe-clefgx {
    background-color: #003399 !important;
    color: #ffffff !important;
}
#brxe-clefgx:hover { background-color: #03a9f4 !important; }

#brxe-1c174a {
    background-color: #003399 !important;
    color: #ffffff !important;
}
#brxe-1c174a:hover { background-color: #03a9f4 !important; }

#brxe-wjsthw {
    background-color: #003399 !important;
    color: #ffffff !important;
}
#brxe-wjsthw:hover {
    background-color: #03a9f4 !important;
}

#brxe-tszryz,
#brxe-tszryz a {
    color: #03a9f4 !important;
}
#brxe-tszryz a:hover {
    color: #003399 !important;
}"""

session = requests.Session()
session.headers.update({
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
})

# Step 1: Get the login page to extract nonce/testcookie
print("Step 1: Fetching login page...")
login_page = session.get(LOGIN_URL)
print(f"  Status: {login_page.status_code}")

# Step 2: Login via POST
print("\nStep 2: Logging in...")
login_data = {
    'log': USERNAME,
    'pwd': PASSWORD,
    'wp-submit': 'Log In',
    'redirect_to': f'{SITE}/wp-admin/',
    'testcookie': '1',
}
# Set the testcookie that WP checks
session.cookies.set('wordpress_test_cookie', 'WP+Cookie+check', domain='azure-nightingale-589250.hostingersite.com')

login_resp = session.post(LOGIN_URL, data=login_data, allow_redirects=False)
print(f"  Status: {login_resp.status_code}")
print(f"  Location: {login_resp.headers.get('Location', 'none')}")
print(f"  Cookies: {[c.name for c in session.cookies]}")

# Follow redirect
if login_resp.status_code in (301, 302):
    redirect_url = login_resp.headers.get('Location', '')
    print(f"  Following redirect to: {redirect_url}")
    dash = session.get(redirect_url)
    print(f"  Dashboard status: {dash.status_code}")
    if 'wp-admin' in dash.url:
        print("  LOGIN SUCCESSFUL!")
    elif 'login' in dash.url.lower():
        print("  LOGIN FAILED — redirected back to login")
        # Check for error message
        if 'incorrect' in dash.text.lower() or 'error' in dash.text.lower():
            error = re.search(r'<div id="login_error">(.*?)</div>', dash.text, re.DOTALL)
            if error:
                print(f"  Error: {error.group(1).strip()[:200]}")

# Step 3: Access the Customizer API to save CSS
print("\nStep 3: Attempting to save CSS via Customizer...")

# WordPress Customizer uses admin-ajax.php with customize_save action
# First, get the customize.php page to extract the nonce
customize_page = session.get(CUSTOMIZE_URL)
print(f"  Customizer page status: {customize_page.status_code}")

if customize_page.status_code == 200 and 'customize' in customize_page.url.lower():
    print("  Customizer accessible!")
    
    # Extract the customize nonce
    nonce_match = re.search(r'"nonce":\s*\{[^}]*"save":\s*"([a-f0-9]+)"', customize_page.text)
    if not nonce_match:
        nonce_match = re.search(r'customize-save-nonce["\s]*value="([^"]+)"', customize_page.text)
    if not nonce_match:
        nonce_match = re.search(r'"_wpnonce":"([a-f0-9]+)"', customize_page.text)
    if not nonce_match:
        nonce_match = re.search(r'_wpnonce=([a-f0-9]+)', customize_page.text)
    
    if nonce_match:
        save_nonce = nonce_match.group(1)
        print(f"  Found save nonce: {save_nonce}")
        
        # Save via admin-ajax.php customize_save
        ajax_url = f"{SITE}/wp-admin/admin-ajax.php"
        
        import json
        save_data = {
            'action': 'customize_save',
            'wp_customize': 'on',
            'customize-save-nonce': save_nonce,
            'nonce': save_nonce,
            'customize_changeset_status': 'publish',
            'customized': json.dumps({
                'custom_css[bricks]': CSS,
            }),
        }
        
        save_resp = session.post(ajax_url, data=save_data)
        print(f"  Save response: HTTP {save_resp.status_code}")
        print(f"  Response: {save_resp.text[:300]}")
        
        if save_resp.status_code == 200:
            try:
                result = save_resp.json()
                if result.get('success'):
                    print("\n  CSS APPLIED SUCCESSFULLY!")
                else:
                    print(f"\n  Save returned: {result}")
            except:
                print(f"\n  Raw response: {save_resp.text[:500]}")
    else:
        print("  Could not find customize save nonce in page")
        # Try to find any nonces
        nonces = re.findall(r'"([a-f0-9]{10})"', customize_page.text)
        print(f"  Found {len(nonces)} potential nonce values")
elif 'login' in customize_page.url.lower():
    print("  Not logged in — redirected to login page")
    print("  The admin login may require a different password than the API Application Password")
else:
    print(f"  Unexpected response URL: {customize_page.url}")

# Step 4: Alternative — try the REST API changeset approach
print("\nStep 4: Trying REST API changeset approach...")
api_session = requests.Session()
api_session.auth = (USERNAME, "vlop MpGU Os2V xDSI C6T7 2fAN")

# Create a changeset
import json, uuid
changeset_uuid = str(uuid.uuid4())
changeset_data = {
    "title": changeset_uuid,
    "status": "auto-draft",
    "content": json.dumps({
        "custom_css[bricks]": {
            "value": CSS,
            "type": "option",
        }
    }),
}

resp = api_session.post(
    f"{SITE}/wp-json/wp/v2/changesets",
    json=changeset_data
)
print(f"  Changeset creation: HTTP {resp.status_code}")
if resp.status_code in (200, 201):
    cs = resp.json()
    cs_id = cs.get('id')
    print(f"  Changeset ID: {cs_id}")
    
    # Publish it
    pub_resp = api_session.post(
        f"{SITE}/wp-json/wp/v2/changesets/{cs_id}",
        json={"status": "publish"}
    )
    print(f"  Publish: HTTP {pub_resp.status_code}")
else:
    print(f"  Response: {resp.text[:300]}")

print("\nDone.")
