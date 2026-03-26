import requests, sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
AZURE = 'https://azure-nightingale-589250.hostingersite.com'
s = requests.Session()
s.auth = ('mikeoliveraz@gmail.com', 'vlop MpGU Os2V xDSI C6T7 2fAN')
r = s.get(f'{AZURE}/wp-json/wp/v2/pages',
          params={'slug': 'about-us', 'context': 'edit', '_fields': 'id,content'},
          timeout=30)
about = r.json()[0]
raw = about['content']['raw']

print("=== Who is on the About Us page? ===")
for name in ['Scott Chate', 'Feyzi Fatehi', 'Francis Uy', 'John Shackleton',
             'Ringo Rivera', 'Mike Oliver', 'Stephen Bird']:
    idx = raw.find(name)
    status = f"FOUND at {idx}" if idx >= 0 else "MISSING"
    print(f"  {name}: {status}")

adv_idx = raw.find('Advisors')
print(f"\nAdvisors heading at: {adv_idx}")

if adv_idx > 0:
    section = raw[adv_idx:adv_idx+3000]
    print("\n--- Advisors section (first 3000 chars) ---")
    print(section)
