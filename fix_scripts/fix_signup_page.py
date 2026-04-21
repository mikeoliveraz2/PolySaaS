"""Publish the Sign Up page with the Request for Demo form (WPForms 1543).
Style it to match the existing PolySaaS site design.
"""
import requests, sys, json
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

AZURE = "https://azure-nightingale-589250.hostingersite.com"
s = requests.Session()
s.auth = ("mikeoliveraz@gmail.com", "vlop MpGU Os2V xDSI C6T7 2fAN")

SIGNUP_PAGE_ID = 1399

# Get the common page styles from an existing page (e.g. About Us) for reference
r_ref = s.get(f"{AZURE}/wp-json/wp/v2/pages/1345",
              params={"context": "edit", "_fields": "content"},
              timeout=30)
ref_content = r_ref.json()['content']['raw']

# Extract the style block and dark mode toggle from the reference page
# Find the first <!-- wp:html --> style block
import re
style_blocks = []
# Get everything up to the first non-style content
lines = ref_content.split('\n')
header_html = []
for line in lines:
    header_html.append(line)
    # Stop after we find the dark mode toggle script closing tag
    if '</script>' in line and 'dark-mode' in ''.join(header_html[-5:]):
        break

header_section = '\n'.join(header_html)
print(f"Extracted header section: {len(header_section)} chars")

# Build the Sign Up page content
PAGE_CONTENT = f"""{header_section}

<!-- wp:html -->
<div style="max-width:720px;margin:0 auto;padding:40px 20px;">
<h2 style="text-align:center;color:var(--ps-primary,#001F3F);font-size:2rem;font-weight:700;margin-bottom:8px;">Sign Up for a Demo</h2>
<p style="text-align:center;color:var(--ps-text-muted,#4B5563);font-size:1.05rem;margin-bottom:32px;">See the full PolySaaS platform in action. Fill out the form below and we'll schedule a personalized demo for you.</p>
</div>
<!-- /wp:html -->

<!-- wp:wpforms/form-selector {{"formId":"1543"}} /-->

<!-- wp:html -->
<div style="max-width:720px;margin:24px auto 0;padding:0 20px;">
<p style="text-align:center;color:var(--ps-text-muted,#6B7280);font-size:0.85rem;">We'll respond within 24 hours. Your information is kept private and secure.</p>
</div>
<!-- /wp:html -->
"""

# Update the page: set content and publish
r = s.post(
    f"{AZURE}/wp-json/wp/v2/pages/{SIGNUP_PAGE_ID}",
    json={
        "content": PAGE_CONTENT,
        "status": "publish",
        "meta": {
            "_kad_post_title": "hide",
        }
    },
    timeout=30
)

if r.status_code == 200:
    page = r.json()
    print(f"SUCCESS: Sign Up page published!")
    print(f"  ID: {page['id']}")
    print(f"  Status: {page['status']}")
    print(f"  Slug: {page['slug']}")
    print(f"  Link: {page.get('link', 'N/A')}")
else:
    print(f"ERROR: {r.status_code}")
    print(r.text[:500])
