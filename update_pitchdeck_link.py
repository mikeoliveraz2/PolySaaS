"""Update the pitch deck link on the investor page."""
import requests, sys
sys.stdout.reconfigure(encoding='utf-8')

AZURE = "https://azure-nightingale-589250.hostingersite.com"
s = requests.Session()
s.auth = ("mikeoliveraz@gmail.com", "vlop MpGU Os2V xDSI C6T7 2fAN")

PAGE_ID = 2565

r = s.get(f"{AZURE}/wp-json/wp/v2/pages/{PAGE_ID}?context=edit", timeout=30)
page = r.json()
content = page['content']['raw']

OLD_LINK = "https://docs.google.com/presentation/d/1ZdzGGqUfuUIWCHiomkmgNrxUjSmDWK6Kl71hK0WB0cc/edit?usp=sharing"
NEW_LINK = "https://docs.google.com/presentation/d/10aJicMPNOGaJF8sRUtNpXuVbes0BrKwP/edit?usp=sharing&ouid=117986726904510989322&rtpof=true&sd=true"

if OLD_LINK in content:
    content = content.replace(OLD_LINK, NEW_LINK)
    r2 = s.post(f"{AZURE}/wp-json/wp/v2/pages/{PAGE_ID}", json={"content": content}, timeout=30)
    print(f"Replaced pitch deck link. Status: {r2.status_code}")
else:
    print("Old link not found — checking if new link already present...")
    if NEW_LINK in content:
        print("New link already in place, nothing to do.")
    else:
        print("Neither link found in page content!")
        print("Searching for 'google.com/presentation'...")
        idx = content.find("google.com/presentation")
        if idx >= 0:
            print(f"Found at index {idx}: ...{content[idx-20:idx+100]}...")
