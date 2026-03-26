"""Extract the CSS custom property definitions from About Us page."""
import requests, sys
sys.stdout.reconfigure(encoding='utf-8')

AZURE = "https://azure-nightingale-589250.hostingersite.com"
s = requests.Session()
s.auth = ("mikeoliveraz@gmail.com", "vlop MpGU Os2V xDSI C6T7 2fAN")

r = s.get(f"{AZURE}/wp-json/wp/v2/pages/1345?context=edit", timeout=30)
page = r.json()
content = page['content']['raw']

idx = content.find(':root')
if idx >= 0:
    end = content.find('}', idx)
    print("=== :root CSS vars ===")
    print(content[idx:end+1])

idx2 = content.find('body.dark-mode {')
if idx2 == -1:
    idx2 = content.find('.dark-mode {')
if idx2 >= 0:
    end2 = content.find('}', idx2)
    print("\n=== dark-mode vars ===")
    print(content[idx2:end2+1])
else:
    print("\nNo .dark-mode { block found, searching --ps- definitions...")
    import re
    matches = re.findall(r'--ps-[\w-]+\s*:\s*[^;]+;', content)
    for m in matches[:30]:
        print(f"  {m}")
