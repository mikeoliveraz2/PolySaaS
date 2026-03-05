"""Clean up the accidental blog post and properly apply CSS."""
import requests

SITE = "https://azure-nightingale-589250.hostingersite.com"
USER = "mikeoliveraz@gmail.com"
APP_PASS = "vlop MpGU Os2V xDSI C6T7 2fAN"

session = requests.Session()
session.auth = (USER, APP_PASS)

# Delete the accidental "bricks" blog post (ID 1713)
print("Deleting accidental blog post ID 1713 ('bricks')...")
resp = session.delete(f"{SITE}/wp-json/wp/v2/posts/1713", params={"force": True})
if resp.status_code == 200:
    print("  Deleted successfully.")
else:
    print(f"  Delete response: HTTP {resp.status_code}")
    print(f"  {resp.text[:200]}")

# Verify it's gone
resp2 = session.get(f"{SITE}/wp-json/wp/v2/posts/1713")
print(f"  Verify: HTTP {resp2.status_code} (should be 404)")

# Check recent posts to make sure blog is clean
print("\nRecent posts after cleanup:")
resp3 = session.get(f"{SITE}/wp-json/wp/v2/posts", params={"per_page": 5, "orderby": "date", "order": "desc"})
if resp3.status_code == 200:
    for p in resp3.json():
        print(f"  ID={p['id']}: {p.get('title',{}).get('rendered','?')}")

# Now try the CORRECT way to set custom CSS
# WordPress stores Additional CSS as: post_type=custom_css, post_name={theme_stylesheet}
# This requires the customize_changeset approach or direct options API

# Try creating the proper custom_css post using wp_options
print("\nAttempting proper custom_css application...")

# Method: Direct option via settings if available
resp4 = session.get(f"{SITE}/wp-json/wp/v2/settings")
if resp4.status_code == 200:
    settings = resp4.json()
    print(f"  Settings keys: {list(settings.keys())[:20]}")

# Method: Try updating via wp-json/wp/v2/global-styles
resp5 = session.get(f"{SITE}/wp-json/wp/v2/global-styles")
if resp5.status_code == 200:
    styles = resp5.json()
    if isinstance(styles, list) and len(styles) > 0:
        gs_id = styles[0].get('id')
        print(f"  Global styles ID: {gs_id}")
        # Check current global styles
        current = styles[0].get('styles', {})
        print(f"  Current styles keys: {list(current.keys()) if isinstance(current, dict) else 'N/A'}")

print("\n" + "=" * 70)
print("CONCLUSION: Use browser to paste CSS into Customizer")
print("=" * 70)
print("The WordPress REST API cannot directly write to the custom_css")
print("post type for the Bricks theme. The CSS must be applied via:")
print("  1. WordPress Admin > Appearance > Customize > Additional CSS")
print("  2. OR: Bricks > Settings > Custom Code > Custom CSS")
print("\nThe CSS is saved in draft page ID 1709 for easy copy-paste.")
