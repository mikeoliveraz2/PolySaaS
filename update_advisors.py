"""Update the Advisors section on the About Us page:
1. Upload Feyzi Fatehi and John Shackleton headshots to WP media
2. Rename 'Board of Advisors' to 'Advisors'
3. Replace Feyzi's placeholder initials with actual headshot
4. Add John Shackleton card
"""
import requests, sys, os, json
sys.stdout.reconfigure(encoding='utf-8')

AZURE = "https://azure-nightingale-589250.hostingersite.com"
s = requests.Session()
s.auth = ("mikeoliveraz@gmail.com", "vlop MpGU Os2V xDSI C6T7 2fAN")
PAGE_ID = 1345

# --- Step 1: Upload headshots ---
def upload_image(filepath, alt_text):
    filename = os.path.basename(filepath)
    mime = "image/png"
    with open(filepath, "rb") as f:
        data = f.read()
    headers = {
        "Content-Disposition": f'attachment; filename="{filename}"',
        "Content-Type": mime
    }
    r = s.post(f"{AZURE}/wp-json/wp/v2/media", data=data, headers=headers, timeout=60)
    if r.status_code == 201:
        media = r.json()
        url = media["source_url"]
        mid = media["id"]
        print(f"  Uploaded {filename} -> ID {mid}, URL: {url}")
        s.post(f"{AZURE}/wp-json/wp/v2/media/{mid}", json={"alt_text": alt_text}, timeout=30)
        return url
    else:
        print(f"  FAILED to upload {filename}: {r.status_code} {r.text[:300]}")
        return None

print("=== Uploading headshots ===")
feyzi_url = upload_image("temp_imgs/feyzi-fatehi-headshot.png", "Feyzi Fatehi")
john_url = upload_image("temp_imgs/john-shackleton-headshot.png", "John Shackleton")

if not feyzi_url or not john_url:
    print("ERROR: One or both uploads failed. Aborting.")
    sys.exit(1)

# --- Step 2: Fetch the About Us page ---
print("\n=== Fetching About Us page ===")
r = s.get(f"{AZURE}/wp-json/wp/v2/pages/{PAGE_ID}?context=edit", timeout=30)
page = r.json()
content = page['content']['raw']
print(f"  Page length: {len(content)} chars")

# --- Step 3: Rename "Board of Advisors" to "Advisors" ---
print("\n=== Renaming section ===")
content = content.replace("Board of Advisors Section", "Advisors Section")
content = content.replace(">Board of Advisors</h2>", ">Advisors</h2>")
print("  Renamed 'Board of Advisors' -> 'Advisors'")

# --- Step 4: Replace Feyzi's placeholder initials with headshot ---
print("\n=== Updating Feyzi Fatehi headshot ===")
feyzi_placeholder = '<div style="width:100px;height:100px;border-radius:50%;background:var(--ps-icon-bg,#E5E7EB);margin:0 auto 12px auto;display:flex;align-items:center;justify-content:center;font-size:2rem;color:var(--ps-text-muted,#6B7280)">FF</div>'
feyzi_img = f'<img src="{feyzi_url}" alt="Feyzi Fatehi" style="width:100px;height:100px;border-radius:50%;object-fit:cover;margin:0 auto 12px auto;display:block;">'

if feyzi_placeholder in content:
    content = content.replace(feyzi_placeholder, feyzi_img)
    print("  Replaced placeholder with headshot image")
else:
    print("  WARNING: Feyzi placeholder not found exactly, trying flexible match...")
    import re
    pattern = r'<div style="[^"]*">FF</div>'
    match = re.search(pattern, content)
    if match:
        content = content[:match.start()] + feyzi_img + content[match.end():]
        print("  Replaced via regex match")
    else:
        print("  ERROR: Could not find Feyzi placeholder!")

# --- Step 5: Add John Shackleton card ---
print("\n=== Adding John Shackleton card ===")

john_card = f'''<p><!-- John Shackleton --></p>
<div style="flex:1 1 280px;max-width:380px;background:var(--ps-card-bg,#fff);border-radius:8px;padding:24px;box-shadow:0 2px 8px var(--ps-card-shadow,rgba(0,0,0,0.06));text-align:center">
<img src="{john_url}" alt="John Shackleton" style="width:100px;height:100px;border-radius:50%;object-fit:cover;margin:0 auto 12px auto;display:block;">
<h3 style="font-size:1.2rem;font-weight:600;margin-bottom:4px;color:var(--ps-text,#1F2937)">John Shackleton</h3>
<p style="font-size:0.9rem;color:#2563EB;font-weight:500;margin-bottom:8px">Advisor</p>
<p style="font-size:0.9rem;line-height:1.6;color:var(--ps-text-muted,#4B5563)"></p>
<p><a href="https://www.linkedin.com/in/john-shackleton-01b952163/" style="display:inline-block;margin-top:8px;color:#2563EB;text-decoration:none;font-size:0.85rem;font-weight:500">LinkedIn &rarr;</a>
</div>'''

francis_comment = '<p><!-- Francis Uy --></p>'
placeholder_comment = '<p><!-- Placeholder for additional advisors --></p>'

if francis_comment in content:
    content = content.replace(
        francis_comment + '\n\n' + placeholder_comment,
        john_card + '\n' + placeholder_comment
    )
    if francis_comment in content:
        content = content.replace(
            francis_comment + '\n' + placeholder_comment,
            john_card + '\n' + placeholder_comment
        )
    if francis_comment in content:
        content = content.replace(francis_comment, john_card)
    print("  Added John Shackleton card (replaced Francis Uy placeholder)")
elif placeholder_comment in content:
    content = content.replace(placeholder_comment, john_card + '\n' + placeholder_comment)
    print("  Added John Shackleton card before placeholder")
else:
    print("  WARNING: Could not find insertion point for John Shackleton!")

# --- Step 6: Update the page ---
print(f"\n=== Updating page (new length: {len(content)} chars) ===")
r2 = s.post(
    f"{AZURE}/wp-json/wp/v2/pages/{PAGE_ID}",
    json={"content": content},
    timeout=30
)
print(f"  Status: {r2.status_code}")
if r2.status_code == 200:
    print("  SUCCESS! About Us page updated.")
    print("  - Section renamed to 'Advisors'")
    print("  - Feyzi Fatehi headshot added")
    print("  - John Shackleton card added")
else:
    print(f"  ERROR: {r2.text[:500]}")
