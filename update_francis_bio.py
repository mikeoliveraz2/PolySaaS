"""Update Francis Uy's bio text on the About Us page per his request."""
import requests, sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

AZURE = "https://azure-nightingale-589250.hostingersite.com"
s = requests.Session()
s.auth = ("mikeoliveraz@gmail.com", "vlop MpGU Os2V xDSI C6T7 2fAN")

r = s.get(f"{AZURE}/wp-json/wp/v2/pages",
          params={"slug": "about-us", "context": "edit", "_fields": "id,content"},
          timeout=30)
page = r.json()[0]
raw = page['content']['raw']
page_id = page['id']
print(f"Page ID: {page_id}, length: {len(raw)} chars")

OLD_BIO = (
    "15+ years delivering large-scale enterprise systems with ERP implementations "
    "across four continents (Australia/NZ, Vietnam, France, Italy) and 9+ years "
    "managing digital marketing, eCommerce, and loyalty applications driving "
    "hundreds of millions in retail sales."
)

NEW_BIO = (
    "15+ years architecting large-scale enterprise systems, including ERP "
    "implementations across four continents (ANZ, VN, FR, IT). 17+ years in "
    "Enterprise Architecture, spanning eCommerce solutions that enabled $6B USD "
    "in sales for an FMCG company; design of a nationwide health sector ecosystem; "
    "and service as a WHO core architect for country digital health ecosystems "
    "(DPI-Health)."
)

if OLD_BIO in raw:
    raw = raw.replace(OLD_BIO, NEW_BIO)
    print("  Bio text replaced")
else:
    print("  ERROR: Old bio text not found exactly")
    sys.exit(1)

r2 = s.post(f"{AZURE}/wp-json/wp/v2/pages/{page_id}",
            json={"content": raw}, timeout=30)
print(f"  Status: {r2.status_code}")
if r2.status_code == 200:
    print("  SUCCESS! Francis Uy bio updated.")
else:
    print(f"  ERROR: {r2.text[:500]}")
