"""
Set Kadence footer middle row styling to match the dark footer look.
"""
import requests, json, sys, re, uuid
sys.stdout.reconfigure(encoding='utf-8')

AZURE = "https://azure-nightingale-589250.hostingersite.com"

admin = requests.Session()
admin.headers.update({'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0'})
admin.cookies.set('wordpress_test_cookie', 'WP+Cookie+check')

# Login
login_data = {
    'log': 'mikeoliveraz@gmail.com',
    'pwd': 'M@ster119611p',
    'wp-submit': 'Log In',
    'redirect_to': f'{AZURE}/wp-admin/',
    'testcookie': '1',
}
login_r = admin.post(f"{AZURE}/wp-login.php", data=login_data, allow_redirects=True, timeout=30)
print(f"Login: {login_r.url}")

# Get Customizer nonce
cust_r = admin.get(f"{AZURE}/wp-admin/customize.php", timeout=30)
nonce_match = re.search(r'"save"\s*:\s*"([a-f0-9]+)"', cust_r.text)
if not nonce_match:
    nonce_match = re.search(r'"nonce"\s*:\s*"([a-f0-9]+)"', cust_r.text)
nonce = nonce_match.group(1) if nonce_match else None
print(f"Nonce: {nonce}")

changeset_match = re.search(r'"changeset_uuid"\s*:\s*"([^"]+)"', cust_r.text)
changeset_uuid = changeset_match.group(1) if changeset_match else str(uuid.uuid4())

# Also extract any existing footer settings to understand current state
# Search for footer_items in the settings
items_match = re.search(r'"footer_items"\s*:\s*(\{[^}]*\{[^}]*\}[^}]*\}[^}]*\})', cust_r.text)
if items_match:
    print(f"Current footer_items: {items_match.group(1)[:200]}")

# Configure middle row styling
settings = {
    "footer_middle_background": {
        "value": {
            "desktop": {
                "color": "#111827"
            }
        },
        "type": "theme_mod"
    },
    "footer_middle_top_border": {
        "value": {
            "desktop": {
                "width": 0,
                "unit": "px",
                "style": "none",
                "color": "transparent"
            }
        },
        "type": "theme_mod"
    },
    "footer_middle_bottom_border": {
        "value": {
            "desktop": {
                "width": 0,
                "unit": "px",
                "style": "none",
                "color": "transparent"
            }
        },
        "type": "theme_mod"
    },
    "footer_middle_link_colors": {
        "value": {
            "color": "#5eead4",
            "hover": "#2dd4bf"
        },
        "type": "theme_mod"
    },
    "footer_middle_widget_title": {
        "value": {
            "color": "#5eead4",
            "size": {"desktop": 16, "unit": "px"}
        },
        "type": "theme_mod"
    },
    "footer_middle_widget_content": {
        "value": {
            "color": "#e5e7eb",
            "size": {"desktop": 14, "unit": "px"}
        },
        "type": "theme_mod"
    },
    "footer_middle_top_spacing": {
        "value": {
            "desktop": {"top": 20, "bottom": 20, "unit": "px"}
        },
        "type": "theme_mod"
    },
    "footer_middle_column_spacing": {
        "value": {
            "desktop": {"left": 15, "right": 15, "unit": "px"}
        },
        "type": "theme_mod"
    },
    # Bottom row (copyright) styling
    "footer_bottom_background": {
        "value": {
            "desktop": {
                "color": "#0f172a"
            }
        },
        "type": "theme_mod"
    },
    "footer_bottom_top_border": {
        "value": {
            "desktop": {
                "width": 1,
                "unit": "px",
                "style": "solid",
                "color": "#1e293b"
            }
        },
        "type": "theme_mod"
    },
}

if nonce:
    save_data = {
        'action': 'customize_save',
        'wp_customize': 'on',
        'customize-save-nonce': nonce,
        'nonce': nonce,
        'customize_changeset_uuid': changeset_uuid,
        'customize_changeset_status': 'publish',
        'customized': json.dumps(settings)
    }

    save_r = admin.post(
        f"{AZURE}/wp-admin/admin-ajax.php",
        data=save_data,
        timeout=30
    )
    print(f"\nSave status: {save_r.status_code}")
    print(f"Save response: {save_r.text[:500]}")
else:
    print("ERROR: No nonce found!")
