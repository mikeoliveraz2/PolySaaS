"""Find PolySniffer images in the media library."""
import requests
AZURE = "https://azure-nightingale-589250.hostingersite.com"
s = requests.Session()
s.auth = ("mikeoliveraz@gmail.com", "vlop MpGU Os2V xDSI C6T7 2fAN")

# Search for polysniffer
r = s.get(f"{AZURE}/wp-json/wp/v2/media", params={"per_page": 100, "search": "polysniffer"})
media = r.json()
print(f"Found {len(media)} media items matching 'polysniffer'")
for m in media:
    mid = m["id"]
    title = m["title"]["rendered"]
    url = m["source_url"]
    print(f"  id={mid}  title={title}")
    print(f"    url={url}")

# Also search for sniffer
r2 = s.get(f"{AZURE}/wp-json/wp/v2/media", params={"per_page": 100, "search": "sniffer"})
media2 = r2.json()
seen = {m["id"] for m in media}
extra = [m for m in media2 if m["id"] not in seen]
if extra:
    print(f"\nAdditional {len(extra)} items matching 'sniffer':")
    for m in extra:
        mid = m["id"]
        title = m["title"]["rendered"]
        url = m["source_url"]
        print(f"  id={mid}  title={title}")
        print(f"    url={url}")

# Also search for passthrough / capture
for term in ["passthrough", "capture", "endpoint"]:
    r3 = s.get(f"{AZURE}/wp-json/wp/v2/media", params={"per_page": 100, "search": term})
    media3 = r3.json()
    if media3:
        print(f"\n{len(media3)} items matching '{term}':")
        for m in media3:
            mid = m["id"]
            title = m["title"]["rendered"]
            url = m["source_url"]
            print(f"  id={mid}  title={title}")
            print(f"    url={url}")
