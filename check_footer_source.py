"""Check if footer is in page content or theme. Compare About Us (has footer) vs AI As Peers (no footer)."""
import requests, sys
sys.stdout.reconfigure(encoding='utf-8')

AZURE = "https://azure-nightingale-589250.hostingersite.com"
s = requests.Session()
s.auth = ("mikeoliveraz@gmail.com", "vlop MpGU Os2V xDSI C6T7 2fAN")

# Check if the footer content is IN the page content for About Us
r = s.get(f"{AZURE}/wp-json/wp/v2/pages?slug=about-us&context=edit")
about_content = r.json()[0]['content']['raw']

has_contact_in_content = 'michael.oliver@polysaas.online' in about_content
has_address_in_content = '5900 Balcones' in about_content
has_apps_links = 'Applications' in about_content and 'Liferay' in about_content

print("=== About Us page content analysis ===")
print(f"  Contact email in content: {has_contact_in_content}")
print(f"  Address in content: {has_address_in_content}")
print(f"  App links in content: {has_apps_links}")

if has_contact_in_content:
    # Find where footer content starts in the raw content
    idx = about_content.find('5900 Balcones')
    if idx > 0:
        print(f"\n  Footer starts at char {idx} of {len(about_content)} total")
        print(f"  Last 1500 chars of content:")
        print(about_content[-1500:])
