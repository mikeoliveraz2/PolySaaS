"""Upload Ringo Rivera headshot to WordPress media library."""
import requests

AZURE = "https://azure-nightingale-589250.hostingersite.com"
s = requests.Session()
s.auth = ("mikeoliveraz@gmail.com", "vlop MpGU Os2V xDSI C6T7 2fAN")

img_path = r"C:\Users\PC\.cursor\projects\d-PolySaaS\assets\c__Users_PC_AppData_Roaming_Cursor_User_workspaceStorage_77452477b6ce94d3acba53b24d1f01c9_images_rrheadshot-c5179758-3730-476a-8d10-64536567c93a.png"

with open(img_path, 'rb') as f:
    data = f.read()

print(f"Image size: {len(data)} bytes")

headers = {
    'Content-Disposition': 'attachment; filename="ringo-rivera-headshot.png"',
    'Content-Type': 'image/png',
}

r = s.post(
    f"{AZURE}/wp-json/wp/v2/media",
    headers=headers,
    data=data
)

print(f"Upload status: {r.status_code}")
if r.status_code == 201:
    media = r.json()
    print(f"Success! Media id={media['id']}")
    print(f"URL: {media['source_url']}")
    print(f"Title: {media['title']['rendered']}")
    
    # Update alt text and title
    r2 = s.post(f"{AZURE}/wp-json/wp/v2/media/{media['id']}", json={
        "title": "Ringo Rivera",
        "alt_text": "Ringo Rivera - PolySaaS Team",
        "caption": "Ringo Rivera"
    })
    print(f"Metadata update: {r2.status_code}")
else:
    print(f"Error: {r.text[:400]}")
