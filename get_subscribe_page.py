"""Get the current subscribe/pricing page content."""
import requests

AZURE = "https://azure-nightingale-589250.hostingersite.com"
s = requests.Session()
s.auth = ("mikeoliveraz@gmail.com", "vlop MpGU Os2V xDSI C6T7 2fAN")

# Try multiple possible slugs
for slug in ["subscribe", "pricing", "sign-up", "signup"]:
    r = s.get(f"{AZURE}/wp-json/wp/v2/pages?slug={slug}&context=edit")
    pages = r.json()
    if pages:
        page = pages[0]
        print(f"Found: slug='{slug}', id={page['id']}, title={page['title']['raw']}")
        print(f"Content length: {len(page['content']['raw'])}")
        print("---CONTENT START---")
        print(page['content']['raw'][:8000])
        print("---END (first 8000 chars)---")
        break
else:
    # Search by title
    print("No slug match. Searching by title...")
    for term in ["subscribe", "pricing", "price"]:
        r = s.get(f"{AZURE}/wp-json/wp/v2/pages?search={term}&context=edit&per_page=10")
        pages = r.json()
        if pages:
            for p in pages:
                print(f"  id={p['id']} title='{p['title']['raw']}' slug='{p['slug']}'")
