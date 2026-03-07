"""Extract the Bricks HTML structure of the single post template."""
import requests
import re

SITE = "https://azure-nightingale-589250.hostingersite.com"

r = requests.get(f"{SITE}/polysysmon-your-24-7-system-health-guard/", timeout=20)
html = r.text

# Extract the #brx-content area
content_match = re.search(r'(<div[^>]*id="brx-content"[^>]*>.*?)(<!-- Footer|<footer|<div[^>]*id="brx-footer")', html, re.DOTALL)
if content_match:
    content = content_match.group(1)
    # Extract all brxe- elements with their tags and classes
    elements = re.findall(r'<(\w+)[^>]*(?:id="(brxe-[^"]+)"|class="([^"]*brxe-[^"]*)")', content)
    print("=== BRICKS ELEMENTS IN POST CONTENT ===")
    for tag, el_id, el_class in elements:
        if el_id:
            print(f"  <{tag} id=\"{el_id}\">")
        if el_class:
            classes = [c for c in el_class.split() if c.startswith('brxe-')]
            for c in classes:
                print(f"  <{tag} class=\"{c}\">")

# Extract the full post content section with more context
print("\n=== FULL POST STRUCTURE (simplified) ===")
# Find all elements with brxe- IDs
brxe_ids = re.findall(r'id="(brxe-[a-z0-9]+)"', content if content_match else html)
print(f"  Bricks element IDs found: {len(brxe_ids)}")
for bid in brxe_ids:
    # Find the element and its tag/class
    match = re.search(r'<(\w+)[^>]*id="' + re.escape(bid) + r'"[^>]*class="([^"]*)"', html)
    if match:
        tag = match.group(1)
        classes = match.group(2)
        print(f"  #{bid}  <{tag}>  classes: {classes}")

# Extract the post-specific Bricks classes
print("\n=== POST-SPECIFIC CLASSES ===")
post_classes = re.findall(r'class="([^"]*(?:post|blog|article|entry|comment|author|share|related|navigation)[^"]*)"', html, re.IGNORECASE)
for pc in post_classes[:30]:
    print(f"  {pc}")

# Check the archive/blog page
print("\n=== BLOG ARCHIVE PAGE ===")
r_blog = requests.get(f"{SITE}/blog/", timeout=20)
print(f"  /blog/ -> HTTP {r_blog.status_code}")
if r_blog.status_code == 200:
    if 'brxe-' in r_blog.text:
        print("  Rendered by Bricks")
    body_match = re.search(r'<body[^>]*class="([^"]*)"', r_blog.text)
    if body_match:
        print(f"  Body classes: {body_match.group(1)}")
    # Count post entries
    posts_on_page = len(re.findall(r'class="[^"]*(?:brxe-post|wp-post|entry-title)[^"]*"', r_blog.text))
    print(f"  Post entries visible: {posts_on_page}")
elif r_blog.status_code == 404:
    print("  No /blog/ page exists yet")
