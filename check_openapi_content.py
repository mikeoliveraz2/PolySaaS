"""Check what actual content the OpenAPI page has (strip CSS/style blocks)."""
import requests, re

AZURE = "https://azure-nightingale-589250.hostingersite.com"
s = requests.Session()
s.auth = ("mikeoliveraz@gmail.com", "vlop MpGU Os2V xDSI C6T7 2fAN")

r = s.get(f"{AZURE}/wp-json/wp/v2/pages?slug=openapi-2&context=edit")
page = r.json()[0]
content = page['content']['raw']

# Strip all <style>...</style> blocks
stripped = re.sub(r'<style>.*?</style>', '', content, flags=re.DOTALL)
# Strip wp:html comments
stripped = re.sub(r'<!--\s*/?wp:html\s*-->', '', stripped)
# Strip empty lines
stripped = re.sub(r'\n\s*\n', '\n', stripped).strip()

print(f"Content after stripping styles ({len(stripped)} chars):")
print(stripped[:3000])
print("\n...")
if len(stripped) > 3000:
    print(stripped[-500:])
