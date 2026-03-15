"""
Check Mattermost page structure to find where to insert after AI Peers Integration block.
Also check media library for the Business Plan Group Chat screenshot.
"""
import requests, re, sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

AZURE = "https://azure-nightingale-589250.hostingersite.com"
s = requests.Session()
s.auth = ("mikeoliveraz@gmail.com", "vlop MpGU Os2V xDSI C6T7 2fAN")

# Check Mattermost page structure
pages = s.get(f"{AZURE}/wp-json/wp/v2/pages", params={
    "slug": "mattermost", "context": "edit", "_fields": "id,content"
}).json()
mm = pages[0]
raw = mm['content']['raw']

# Find AI Peers Integration section
ai_idx = raw.find('AI Peers Integration')
if ai_idx < 0:
    ai_idx = raw.find('AI Peers')
    if ai_idx < 0:
        ai_idx = raw.find('AI as Peers')

print(f"'AI Peers' found at: {ai_idx}")
if ai_idx > 0:
    area = raw[ai_idx:ai_idx+800]
    print(f"\nContent around AI Peers Integration:")
    print(area[:800])

# Search media library for Business Plan or group chat screenshots
media = s.get(f"{AZURE}/wp-json/wp/v2/media", params={
    "per_page": 100, "search": "chat", "_fields": "id,source_url,title"
}).json()
print(f"\nMedia with 'chat': {len(media)}")
for m in media:
    title = m['title']['rendered'] if isinstance(m['title'], dict) else m['title']
    print(f"  id={m['id']}: {title} - {m['source_url']}")

media2 = s.get(f"{AZURE}/wp-json/wp/v2/media", params={
    "per_page": 100, "search": "mattermost", "_fields": "id,source_url,title"
}).json()
print(f"\nMedia with 'mattermost': {len(media2)}")
for m in media2:
    title = m['title']['rendered'] if isinstance(m['title'], dict) else m['title']
    print(f"  id={m['id']}: {title} - {m['source_url']}")

media3 = s.get(f"{AZURE}/wp-json/wp/v2/media", params={
    "per_page": 100, "search": "business", "_fields": "id,source_url,title"
}).json()
print(f"\nMedia with 'business': {len(media3)}")
for m in media3:
    title = m['title']['rendered'] if isinstance(m['title'], dict) else m['title']
    print(f"  id={m['id']}: {title} - {m['source_url']}")
