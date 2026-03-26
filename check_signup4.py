"""Get Sign Up page content and WPForms details via wp_posts."""
import requests, sys, json
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

AZURE = "https://azure-nightingale-589250.hostingersite.com"
s = requests.Session()
s.auth = ("mikeoliveraz@gmail.com", "vlop MpGU Os2V xDSI C6T7 2fAN")

# Get the Sign Up page (draft, ID 1399)
r = s.get(f"{AZURE}/wp-json/wp/v2/pages/1399",
          params={"context": "edit", "_fields": "id,title,slug,status,content"},
          timeout=30)
if r.status_code == 200:
    page = r.json()
    print(f"=== Sign Up Page ===")
    print(f"ID: {page['id']}")
    print(f"Title: {page['title']['raw']}")
    print(f"Status: {page['status']}")
    print(f"Content:\n{page['content']['raw']}")
else:
    print(f"Error: {r.status_code} - {r.text[:300]}")

# Also check the Schedule a Demo page (ID 1720) since it's the published demo signup
print("\n\n=== Schedule a Demo Page ===")
r2 = s.get(f"{AZURE}/wp-json/wp/v2/pages/1720",
           params={"context": "edit", "_fields": "id,title,slug,status,content"},
           timeout=30)
if r2.status_code == 200:
    page = r2.json()
    print(f"ID: {page['id']}")
    print(f"Title: {page['title']['raw']}")
    print(f"Status: {page['status']}")
    print(f"Content:\n{page['content']['raw']}")

# Try getting WPForms data through the wpforms post type
print("\n\n=== WPForms via wpforms post type ===")
r3 = s.get(f"{AZURE}/wp-json/wp/v2/types", timeout=15)
types = r3.json()
wpf_types = {k: v for k, v in types.items() if 'form' in k.lower() or 'wpform' in k.lower()}
print(f"Form-related post types: {list(wpf_types.keys())}")

# WPForms stores forms as 'wpforms' custom post type
# Let's try accessing directly
for form_id in [1543, 1493]:
    # Try via generic posts endpoint with post type filter
    r4 = s.get(f"{AZURE}/wp-json/wp/v2/posts/{form_id}",
               params={"context": "edit"},
               timeout=15)
    print(f"\n  posts/{form_id}: {r4.status_code}")
    
    # Try direct database-like approach via pages endpoint
    r5 = s.get(f"{AZURE}/wp-json/wp/v2/pages/{form_id}",
               params={"context": "edit"},
               timeout=15)
    print(f"  pages/{form_id}: {r5.status_code}")

# The WPForms list endpoint worked earlier - get full details from it
r6 = s.get(f"{AZURE}/wp-json/wpforms/v1/forms", timeout=30)
if r6.status_code == 200:
    forms = r6.json()
    for form in forms:
        fid = form['ID']
        title = form.get('post_title', 'N/A')
        try:
            content = json.loads(form.get('post_content', '{}'))
            settings = content.get('settings', {})
            notifications = settings.get('notifications', {})
            fields = content.get('fields', {})
            
            print(f"\n=== Form {fid}: {title} ===")
            print(f"  Fields: {[f.get('label') for f in fields.values()]}")
            print(f"  Notification enabled: {settings.get('notification_enable', 'not set')}")
            for nid, notif in notifications.items():
                print(f"  Notification {nid}:")
                print(f"    Email: {notif.get('email', 'N/A')}")
                print(f"    Subject: {notif.get('subject', 'N/A')}")
                print(f"    Sender: {notif.get('sender_name', 'N/A')} <{notif.get('sender_address', 'N/A')}>")
                print(f"    Reply-To: {notif.get('replyto', 'N/A')}")
        except:
            print(f"\n  Form {fid}: Could not parse content")
