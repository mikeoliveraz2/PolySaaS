"""Find the sign-up page and check WPForms email notification settings."""
import requests, sys, json
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

AZURE = "https://azure-nightingale-589250.hostingersite.com"
s = requests.Session()
s.auth = ("mikeoliveraz@gmail.com", "vlop MpGU Os2V xDSI C6T7 2fAN")

# Search more broadly for sign-up page
for status in ['publish', 'draft', 'private']:
    r = s.get(f"{AZURE}/wp-json/wp/v2/pages",
              params={"per_page": 100, "status": status,
                      "_fields": "id,title,slug,status,link"},
              timeout=30)
    if r.status_code == 200:
        for p in r.json():
            if 'sign' in p.get('slug', '').lower() or 'sign' in p.get('title', {}).get('rendered', '').lower():
                print(f"Found: ID={p['id']}, Slug={p['slug']}, Title={p['title']['rendered']}, Status={p['status']}, Link={p.get('link','')}")

# Also check page 2 of published pages
r2 = s.get(f"{AZURE}/wp-json/wp/v2/pages",
           params={"per_page": 100, "page": 2, "_fields": "id,title,slug,status"},
           timeout=30)
if r2.status_code == 200 and r2.json():
    for p in r2.json():
        if 'sign' in p.get('slug', '').lower():
            print(f"Page2 Found: ID={p['id']}, Slug={p['slug']}")

# Check what the /sign-up/ URL resolves to
r3 = s.get(f"{AZURE}/sign-up/", allow_redirects=True, timeout=30)
print(f"\n/sign-up/ response: {r3.status_code}, final URL: {r3.url}")
# Look for the page ID in the body
if 'page-id-' in r3.text:
    import re
    page_ids = re.findall(r'page-id-(\d+)', r3.text)
    print(f"Page IDs found in body: {page_ids}")
# Look for wpforms shortcode
if 'wpforms' in r3.text:
    wpforms_matches = re.findall(r'wpforms.*?id[=\s]*["\']?(\d+)', r3.text)
    print(f"WPForms IDs found: {wpforms_matches}")

# Get WPForms details for each form
print("\n=== WPForms Details ===")
for form_id in [1543, 1493, 758, 756]:
    # Try the entries/individual endpoint
    r4 = s.get(f"{AZURE}/wp-json/wpforms/v1/forms/{form_id}", timeout=15)
    if r4.status_code == 200:
        form = r4.json()
        content = json.loads(form.get('post_content', '{}'))
        settings = content.get('settings', {})
        notifications = settings.get('notifications', {})
        print(f"\nForm {form_id}: {form.get('post_title', 'N/A')}")
        print(f"  Notification enabled: {settings.get('notification_enable', 'N/A')}")
        for nid, notif in notifications.items():
            print(f"  Notification {nid}:")
            print(f"    Email: {notif.get('email', 'N/A')}")
            print(f"    Subject: {notif.get('subject', 'N/A')}")
            print(f"    Sender: {notif.get('sender_name', 'N/A')} <{notif.get('sender_address', 'N/A')}>")
    else:
        # Try as a WordPress post
        r5 = s.get(f"{AZURE}/wp-json/wp/v2/posts/{form_id}",
                    params={"context": "edit"},
                    timeout=15)
        if r5.status_code == 200:
            post = r5.json()
            print(f"\nForm {form_id} (via posts): {post.get('title', {}).get('raw', 'N/A')}")
            try:
                content = json.loads(post.get('content', {}).get('raw', '{}'))
                settings = content.get('settings', {})
                notifications = settings.get('notifications', {})
                print(f"  Notification enabled: {settings.get('notification_enable', 'N/A')}")
                for nid, notif in notifications.items():
                    print(f"  Notification {nid}:")
                    print(f"    Email: {notif.get('email', 'N/A')}")
                    print(f"    Subject: {notif.get('subject', 'N/A')}")
                    print(f"    Sender: {notif.get('sender_name', 'N/A')} <{notif.get('sender_address', 'N/A')}>")
            except json.JSONDecodeError:
                print(f"  Content is not JSON: {post.get('content', {}).get('raw', '')[:200]}")
        else:
            print(f"\nForm {form_id}: Could not retrieve ({r4.status_code} / {r5.status_code})")
