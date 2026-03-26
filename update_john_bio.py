"""Update John Shackleton's advisor card with proper title and bio."""
import requests, sys
sys.stdout.reconfigure(encoding='utf-8')

AZURE = "https://azure-nightingale-589250.hostingersite.com"
s = requests.Session()
s.auth = ("mikeoliveraz@gmail.com", "vlop MpGU Os2V xDSI C6T7 2fAN")

r = s.get(f"{AZURE}/wp-json/wp/v2/pages/1345?context=edit", timeout=30)
page = r.json()
content = page['content']['raw']

old_title = '>Advisor</p>'
new_title = '>Chairman, Preservica &amp; Tenovos | Retired CEO, OpenText | Former Chairman, Flexera</p>'

old_bio = 'color:var(--ps-text-muted,#4B5563)"></p>'
new_bio = ('color:var(--ps-text-muted,#4B5563)">'
    '30+ years of technology and document management leadership. '
    'As former President and CEO of OpenText Corporation (NASDAQ/TSX: OTEX), '
    'grew the company from $60M to $1.3B in revenue, making it the world-leading '
    'independent provider of Enterprise Content Management. Previously held '
    'executive positions at Oracle, Sybase, and Platinum Technology. Currently '
    'serves as Board Chair of Preservica, Inc. (Boston) and Tenovos, Inc. (New York).</p>')

changes = 0

if old_title in content:
    content = content.replace(old_title, new_title, 1)
    print("Replaced title")
    changes += 1
else:
    print("WARNING: Title marker not found")

if old_bio in content:
    content = content.replace(old_bio, new_bio, 1)
    print("Replaced bio")
    changes += 1
else:
    print("WARNING: Empty bio marker not found")

if changes > 0:
    r2 = s.post(f"{AZURE}/wp-json/wp/v2/pages/1345", json={"content": content}, timeout=30)
    print(f"Update status: {r2.status_code}")
    if r2.status_code == 200:
        print("SUCCESS - John Shackleton card updated")
    else:
        print(f"ERROR: {r2.text[:500]}")
else:
    print("No changes to make")
