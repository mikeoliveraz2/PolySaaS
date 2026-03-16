"""Find android-to-android image in the media library."""
import requests
AZURE = "https://azure-nightingale-589250.hostingersite.com"
s = requests.Session()
s.auth = ("mikeoliveraz@gmail.com", "vlop MpGU Os2V xDSI C6T7 2fAN")

for term in ["android", "robot", "ai as peers", "aiaspeers", "conference", "peer"]:
    r = s.get(f"{AZURE}/wp-json/wp/v2/media", params={"per_page": 100, "search": term})
    media = r.json()
    if media:
        print(f"'{term}': {len(media)} results")
        for m in media:
            print(f"  id={m['id']}  {m['title']['rendered']}")
            print(f"    {m['source_url']}")
        print()
