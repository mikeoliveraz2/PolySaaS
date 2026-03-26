"""Get OpenAPI page and a reference feature page for comparison."""
import requests, sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

BASE = "https://polysaas.online"
AUTH = ("mikeoliveraz@gmail.com", "vlop MpGU Os2V xDSI C6T7 2fAN")

# OpenAPI page
r1 = requests.get(BASE + "/wp-json/wp/v2/pages/1640",
                  params={"context": "edit", "_fields": "content,title,slug"},
                  auth=AUTH, timeout=45)
p1 = r1.json()
print("=== OpenAPI Page (ID 1640) ===")
print("Title:", p1["title"]["raw"])
print("Slug:", p1["slug"])
print("Content length:", len(p1["content"]["raw"]))
print(p1["content"]["raw"])

print("\n\n" + "="*60)

# Get a working feature page for reference (e.g., Architecture or Portal)
# Let's find one
r2 = requests.get(BASE + "/wp-json/wp/v2/pages",
                  params={"search": "Architecture", "_fields": "id,title,slug,status", "per_page": 5},
                  auth=AUTH, timeout=30)
pages = r2.json()
for p in pages:
    print(f"  ID {p['id']}: {p['title']['rendered']} ({p['slug']})")

# Get the Architecture or Portal page as reference
r3 = requests.get(BASE + "/wp-json/wp/v2/pages",
                  params={"search": "PolySniffer", "_fields": "id,title,slug", "per_page": 3},
                  auth=AUTH, timeout=30)
for p in r3.json():
    print(f"  ID {p['id']}: {p['title']['rendered']} ({p['slug']})")
    if "sniffer" in p["slug"].lower() or "sniffer" in p["title"]["rendered"].lower():
        r4 = requests.get(BASE + f"/wp-json/wp/v2/pages/{p['id']}",
                          params={"context": "edit", "_fields": "content"},
                          auth=AUTH, timeout=45)
        ref = r4.json()["content"]["raw"]
        print(f"\n=== Reference page ({p['title']['rendered']}) content ({len(ref)} chars) ===")
        print(ref[:3000])
        break
