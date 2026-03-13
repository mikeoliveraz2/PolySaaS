import requests
import re

SITE = "https://azure-nightingale-589250.hostingersite.com"

r = requests.get(f"{SITE}/blog/")
print(f"Status: {r.status_code}")
print(f"Content length: {len(r.text)} chars")

# Check if Bricks renders it
if "brxe-" in r.text:
    print("Bricks elements detected: YES")
else:
    print("Bricks elements detected: NO")

# Check for common issues
if "page_for_posts" in r.text or "blog-posts" in r.text:
    print("Blog posts container detected")

# Look for the main content area
main_match = re.search(r'<main[^>]*>(.*?)</main>', r.text, re.DOTALL)
if main_match:
    main_content = main_match.group(1)
    # Strip HTML for readable preview
    text = re.sub(r'<style[^>]*>.*?</style>', '', main_content, flags=re.DOTALL)
    text = re.sub(r'<script[^>]*>.*?</script>', '', text, flags=re.DOTALL)
    text_clean = re.sub(r'<[^>]+>', ' ', text)
    text_clean = re.sub(r'\s+', ' ', text_clean).strip()
    print(f"\nMain content preview ({len(text_clean)} chars):")
    print(text_clean[:1000])
else:
    print("\nNo <main> tag found")

# Check for Bricks content wrapper
bricks_content = re.findall(r'class="[^"]*brxe-post-content[^"]*"', r.text)
if bricks_content:
    print(f"\nBricks post content wrappers: {len(bricks_content)}")

# Check for any article or post cards
articles = re.findall(r'<article[^>]*>', r.text)
print(f"\n<article> tags found: {len(articles)}")

# Check for the blog cards we built
if "polysaas-blog-card" in r.text or "blog-card-grid" in r.text:
    print("Custom blog cards detected: YES")
else:
    print("Custom blog cards detected: NO")

# Look for post titles in the content
post_titles = re.findall(r'class="[^"]*blog-card-title[^"]*"[^>]*>(.*?)<', r.text)
if post_titles:
    print(f"\nBlog card titles found: {len(post_titles)}")
    for t in post_titles[:5]:
        print(f"  - {t.strip()}")

# Check if it's empty / minimal content
if len(r.text) < 5000:
    print("\nWARNING: Page is very small - likely empty or broken")
    print(f"\nFull HTML:\n{r.text}")
