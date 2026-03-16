"""Get the pricing cards section to understand structure."""
import requests

AZURE = "https://azure-nightingale-589250.hostingersite.com"
s = requests.Session()
s.auth = ("mikeoliveraz@gmail.com", "vlop MpGU Os2V xDSI C6T7 2fAN")

r = s.get(f"{AZURE}/wp-json/wp/v2/pages?slug=pricing&context=edit")
page = r.json()[0]
content = page['content']['raw']

# Get everything from "Pricing Plans" to end
idx = content.find('Pricing Plans')
start = content.rfind('<!-- wp:html -->', 0, idx)
print(content[start:])
