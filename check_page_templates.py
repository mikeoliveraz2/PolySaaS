"""Check page template settings for Dynamic Orchestration vs About Us."""
import requests, sys, json
sys.stdout.reconfigure(encoding='utf-8')

AZURE = "https://azure-nightingale-589250.hostingersite.com"
s = requests.Session()
s.auth = ("mikeoliveraz@gmail.com", "vlop MpGU Os2V xDSI C6T7 2fAN")

for slug in ['dynamic-orchestration', 'about-us']:
    r = s.get(f"{AZURE}/wp-json/wp/v2/pages?slug={slug}&context=edit")
    page = r.json()[0]
    print(f"=== {slug} (ID: {page['id']}) ===")
    print(f"  template: {page.get('template', 'N/A')}")
    print(f"  status: {page.get('status', 'N/A')}")
    
    # Check Kadence meta
    meta = page.get('meta', {})
    if meta:
        for k, v in meta.items():
            if v and v != '' and v != '0' and v != 'default':
                print(f"  meta.{k}: {v}")
    print()
