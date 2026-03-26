"""Find sign-up page and get full WPForms configuration."""
import requests, sys, json
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

AZURE = "https://azure-nightingale-589250.hostingersite.com"
s = requests.Session()
s.auth = ("mikeoliveraz@gmail.com", "vlop MpGU Os2V xDSI C6T7 2fAN")

# Search for sign-up related pages
r = s.get(f"{AZURE}/wp-json/wp/v2/pages",
          params={"per_page": 100, "context": "edit",
                  "_fields": "id,title,slug,status", "search": "sign"},
          timeout=30)
if r.status_code == 200:
    pages = r.json()
    print("=== Pages matching 'sign' ===")
    for p in pages:
        print(f"  ID: {p['id']}, Slug: {p['slug']}, Title: {p['title']['raw']}, Status: {p['status']}")

# Also search without filter to find it
r1b = s.get(f"{AZURE}/wp-json/wp/v2/pages",
            params={"per_page": 100, "context": "edit",
                    "_fields": "id,title,slug,status"},
            timeout=30)
if r1b.status_code == 200:
    pages = r1b.json()
    print("\n=== All pages ===")
    for p in pages:
        if any(term in p['slug'].lower() for term in ['sign', 'demo', 'contact', 'form']):
            print(f"  ID: {p['id']}, Slug: {p['slug']}, Title: {p['title']['raw']}, Status: {p['status']}")

# Get full WPForms form 1543 details
r2 = s.get(f"{AZURE}/wp-json/wpforms/v1/forms/1543", timeout=30)
if r2.status_code == 200:
    form_data = r2.json()
    content = json.loads(form_data.get('post_content', '{}'))
    
    print("\n=== WPForms Form 1543 ===")
    print(f"Title: {form_data.get('post_title', 'N/A')}")
    print(f"Status: {form_data.get('post_status', 'N/A')}")
    
    # Fields
    fields = content.get('fields', {})
    print(f"\nFields ({len(fields)}):")
    for fid, field in fields.items():
        print(f"  {field.get('label', 'N/A')} (type: {field.get('type')}, required: {field.get('required', 'no')})")
    
    # Settings - especially email notifications
    settings = content.get('settings', {})
    print(f"\nForm Settings:")
    print(f"  Form Title: {settings.get('form_title', 'N/A')}")
    print(f"  Notification Enable: {settings.get('notification_enable', 'N/A')}")
    print(f"  Notifications:")
    notifications = settings.get('notifications', {})
    for nid, notif in notifications.items():
        print(f"    Notification {nid}:")
        print(f"      Email: {notif.get('email', 'N/A')}")
        print(f"      Subject: {notif.get('subject', 'N/A')}")
        print(f"      Sender Name: {notif.get('sender_name', 'N/A')}")
        print(f"      Sender Address: {notif.get('sender_address', 'N/A')}")
        print(f"      Reply-To: {notif.get('replyto', 'N/A')}")
        print(f"      Message: {notif.get('message', 'N/A')[:200]}")
    
    # Confirmation settings
    confirmations = settings.get('confirmations', {})
    print(f"\n  Confirmations:")
    for cid, conf in confirmations.items():
        print(f"    Confirmation {cid}:")
        print(f"      Type: {conf.get('type', 'N/A')}")
        print(f"      Message: {conf.get('message', 'N/A')[:200]}")

    # SMTP / mail settings
    print(f"\n  Anti-spam: {settings.get('antispam', 'N/A')}")
    print(f"  AJAX Submit: {settings.get('ajax_submit', 'N/A')}")
else:
    print(f"\nForm 1543 error: {r2.status_code}")

# Check for any other forms
r3 = s.get(f"{AZURE}/wp-json/wpforms/v1/forms", timeout=30)
if r3.status_code == 200:
    forms = r3.json()
    print(f"\n=== All WPForms ({len(forms)}) ===")
    for f in forms:
        print(f"  ID: {f['ID']}, Title: {f.get('post_title', 'N/A')}, Status: {f.get('post_status', 'N/A')}")
