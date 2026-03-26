"""Extract the dark mode toggle + CSS from About Us page."""
import requests, sys
sys.stdout.reconfigure(encoding='utf-8')

AZURE = "https://azure-nightingale-589250.hostingersite.com"
s = requests.Session()
s.auth = ("mikeoliveraz@gmail.com", "vlop MpGU Os2V xDSI C6T7 2fAN")

r = s.get(f"{AZURE}/wp-json/wp/v2/pages/1345?context=edit", timeout=30)
page = r.json()
content = page['content']['raw']

# Find toggle button block
idx = content.find('<button class="ps-theme-toggle"')
end = content.find('<!-- /wp:html -->', idx)
toggle_block = content[idx:end]
print("=== TOGGLE BUTTON BLOCK ===")
print(toggle_block)

# Find the dark mode CSS variables
idx2 = content.find('body.dark-mode')
if idx2 == -1:
    idx2 = content.find('.dark-mode')
if idx2 >= 0:
    end2 = content.find('</style>', idx2)
    print("\n=== DARK MODE CSS ===")
    print(content[idx2:end2])
else:
    print("\nNo dark-mode CSS found directly, searching broader...")
    idx3 = content.find('--ps-bg')
    if idx3 >= 0:
        print(content[max(0,idx3-100):idx3+500])
