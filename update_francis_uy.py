"""Add Francis Uy's advisor card to the About Us page.
His card was previously removed — this re-adds it with:
- Actual headshot (already uploaded as ID 2570)
- Updated title and bio from OpenGroup/LinkedIn credentials
- Correct LinkedIn URL
Inserts between Feyzi Fatehi and John Shackleton.
"""
import requests, re, sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

AZURE = "https://azure-nightingale-589250.hostingersite.com"
s = requests.Session()
s.auth = ("mikeoliveraz@gmail.com", "vlop MpGU Os2V xDSI C6T7 2fAN")

FRANCIS_IMG_URL = "https://azure-nightingale-589250.hostingersite.com/wp-content/uploads/2026/03/francis-uy-headshot.jpg"

FRANCIS_CARD = f'''<p><!-- Francis Uy --></p>
<div style="flex:1 1 280px;max-width:380px;background:var(--ps-card-bg,#fff);border-radius:8px;padding:24px;box-shadow:0 2px 8px var(--ps-card-shadow,rgba(0,0,0,0.06));text-align:center">
<img src="{FRANCIS_IMG_URL}" alt="Francis Uy" style="width:100px;height:100px;border-radius:50%;object-fit:cover;margin:0 auto 12px auto;display:block;">
<h3 style="font-size:1.2rem;font-weight:600;margin-bottom:4px;color:var(--ps-text,#1F2937)">Francis Uy</h3>
<p style="font-size:0.9rem;color:#2563EB;font-weight:500;margin-bottom:8px">CEO, Katapult Digital &amp; Sinag Solutions</p>
<p style="font-size:0.9rem;line-height:1.6;color:var(--ps-text-muted,#4B5563)">Founding Chairman of the Association of Enterprise Architects Philippines. TOGAF-certified enterprise architect and PMP with a Master&rsquo;s in Enterprise Architecture Management. Led the Philippine Covid Vaccine Information Management System and World Bank Group digital government initiatives. 15+ years delivering large-scale enterprise systems with ERP implementations across four continents (Australia/NZ, Vietnam, France, Italy) and 9+ years managing digital marketing, eCommerce, and loyalty applications driving hundreds of millions in retail sales.</p>
<p><a href="https://www.linkedin.com/in/francisduy/" style="display:inline-block;margin-top:8px;color:#2563EB;text-decoration:none;font-size:0.85rem;font-weight:500">LinkedIn &rarr;</a></p>
</div>'''

# --- Fetch About Us page ---
print("=== Fetching About Us page ===")
r = s.get(f"{AZURE}/wp-json/wp/v2/pages",
          params={"slug": "about-us", "context": "edit", "_fields": "id,content"},
          timeout=30)
about = r.json()[0]
raw = about['content']['raw']
page_id = about['id']
print(f"  Page ID: {page_id}, length: {len(raw)} chars")

if 'Francis Uy' in raw:
    print("  Francis Uy already on page — aborting to avoid duplicate.")
    sys.exit(0)

# --- Find insertion point: after Feyzi Fatehi's card, before John Shackleton ---
print("\n=== Finding insertion point ===")

john_comment = '<p><!-- John Shackleton --></p>'
john_idx = raw.find(john_comment)

if john_idx > 0:
    print(f"  Found John Shackleton comment at {john_idx}")
    print("  Inserting Francis card before John Shackleton")
    raw = raw[:john_idx] + FRANCIS_CARD + "\n" + raw[john_idx:]
else:
    feyzi_idx = raw.find('Feyzi Fatehi')
    if feyzi_idx > 0:
        feyzi_card_start = raw.rfind('<div style="flex:1 1 280px', 0, feyzi_idx)
        depth = 0
        i = feyzi_card_start
        feyzi_card_end = None
        while i < len(raw):
            if raw[i:i+4] == '<div':
                depth += 1
                i += 4
            elif raw[i:i+6] == '</div>':
                depth -= 1
                if depth == 0:
                    feyzi_card_end = i + 6
                    break
                i += 6
            else:
                i += 1
        if feyzi_card_end:
            print(f"  Inserting after Feyzi's card (ends at {feyzi_card_end})")
            raw = raw[:feyzi_card_end] + "\n" + FRANCIS_CARD + "\n" + raw[feyzi_card_end:]
        else:
            print("  ERROR: Could not find end of Feyzi's card")
            sys.exit(1)
    else:
        print("  ERROR: Could not find Feyzi Fatehi on the page")
        sys.exit(1)

# --- Update the page ---
print(f"\n=== Updating page (new length: {len(raw)} chars) ===")
r2 = s.post(
    f"{AZURE}/wp-json/wp/v2/pages/{page_id}",
    json={"content": raw},
    timeout=30,
)
print(f"  Status: {r2.status_code}")
if r2.status_code == 200:
    print("\n  SUCCESS! Francis Uy advisor card added.")
    print("  - Headshot: francis-uy-headshot.jpg")
    print("  - Title: CEO, Katapult Digital & Sinag Solutions")
    print("  - Bio: OpenGroup + LinkedIn credentials")
    print("  - LinkedIn: https://www.linkedin.com/in/francisduy/")
    print("  - Position: between Feyzi Fatehi and John Shackleton")
else:
    print(f"  ERROR: {r2.text[:500]}")
