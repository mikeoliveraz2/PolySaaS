"""Check investor page for missing content and restore from revisions."""
import requests, sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

BASE = "https://polysaas.online"
AUTH = ("mikeoliveraz@gmail.com", "vlop MpGU Os2V xDSI C6T7 2fAN")

# Check revisions
r = requests.get(BASE + "/wp-json/wp/v2/pages/2565/revisions",
                 params={"per_page": 10, "_fields": "id,date,content"},
                 auth=AUTH, timeout=45)
revisions = r.json()
print(f"Found {len(revisions)} revisions\n")

for rev in revisions:
    raw = rev.get('content', {}).get('raw', '') or rev.get('content', {}).get('rendered', '')
    print(f"Rev {rev['id']} ({rev['date']}): {len(raw)} chars")

# Find the last revision that had full content (>25000 chars)
for rev in revisions:
    raw = rev.get('content', {}).get('raw', '') or rev.get('content', {}).get('rendered', '')
    if len(raw) > 25000:
        print(f"\nFound good revision: {rev['id']} ({rev['date']}) with {len(raw)} chars")
        print("Has 'Quick 15-Minute':", 'Quick 15-Minute' in raw)
        print("Has 'LinkedIn':", 'linkedin.com' in raw)
        print("Has 'Disclaimer':", 'Disclaimer' in raw)
        
        # Restore this revision
        r2 = requests.post(BASE + "/wp-json/wp/v2/pages/2565",
                          auth=AUTH,
                          json={"content": raw},
                          timeout=45)
        print(f"\nRestore: {r2.status_code}")
        if r2.status_code == 200:
            print("SUCCESS - Investor page restored to full content")
        else:
            print(f"Error: {r2.text[:300]}")
        break
