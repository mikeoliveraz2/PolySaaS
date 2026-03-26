"""Check if the ps-features-centered wrapper survived WordPress save."""
import requests, sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

AZURE = "https://azure-nightingale-589250.hostingersite.com"
s = requests.Session()
s.auth = ("mikeoliveraz@gmail.com", "vlop MpGU Os2V xDSI C6T7 2fAN")

r = s.get(f"{AZURE}/wp-json/wp/v2/pages",
          params={"slug": "home", "context": "edit", "_fields": "id,content"},
          timeout=30)
page = r.json()[0]
raw = page['content']['raw']

has_wrapper = 'ps-features-centered' in raw
print(f"Wrapper div present in saved content: {has_wrapper}")

# Check what's around the Platform Features heading
pf_idx = raw.find('Platform Features')
if pf_idx > 0:
    print(f"\nContent around Platform Features ({pf_idx}):")
    print(raw[pf_idx-50:pf_idx+200])
    
    # Show what comes after the </h2>
    h2_end = raw.find('</h2>', pf_idx) + 5
    print(f"\nAfter </h2> (at {h2_end}):")
    print(raw[h2_end:h2_end+300])
