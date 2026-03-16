"""Check all AI/Peers related images to find the android-to-android one."""
import requests

AZURE = "https://azure-nightingale-589250.hostingersite.com"
s = requests.Session()
s.auth = ("mikeoliveraz@gmail.com", "vlop MpGU Os2V xDSI C6T7 2fAN")

ids = [489, 490, 761, 980, 1471, 2470]
for mid in ids:
    r = s.get(f"{AZURE}/wp-json/wp/v2/media/{mid}")
    m = r.json()
    print(f"id={mid}  title={m['title']['rendered']}")
    print(f"  url={m['source_url']}")
    print(f"  alt={m.get('alt_text','')}")
    print(f"  desc={m.get('description',{}).get('rendered','')[:100]}")
    if 'media_details' in m:
        md = m['media_details']
        print(f"  size={md.get('width','?')}x{md.get('height','?')}")
    print()
