"""Get the full pricing page to find insertion point for value proposition."""
import requests

AZURE = "https://azure-nightingale-589250.hostingersite.com"
s = requests.Session()
s.auth = ("mikeoliveraz@gmail.com", "vlop MpGU Os2V xDSI C6T7 2fAN")

r = s.get(f"{AZURE}/wp-json/wp/v2/pages?slug=pricing&context=edit")
page = r.json()[0]
content = page['content']['raw']
print(f"Total length: {len(content)}")

# Find the title block and pricing cards section
import re
# Look for the title H2 and the pricing heading
title_idx = content.find('>Pricing</h2>')
pricing_plans_idx = content.find('Pricing Plans')
print(f"Title H2 at: {title_idx}")
print(f"'Pricing Plans' at: {pricing_plans_idx}")

# Show content around the title and before pricing cards
if title_idx > 0:
    # Find end of the title wp:html block
    wp_close = content.find('<!-- /wp:html -->', title_idx)
    if wp_close > 0:
        after_title = wp_close + len('<!-- /wp:html -->')
        print(f"\nAfter title block ends at: {after_title}")
        print(f"Content after title (500 chars):")
        print(content[after_title:after_title+500])
        print("---")

# Show the pricing plans heading area
if pricing_plans_idx > 0:
    print(f"\nAround 'Pricing Plans' (500 chars before):")
    print(content[max(0,pricing_plans_idx-200):pricing_plans_idx+300])
