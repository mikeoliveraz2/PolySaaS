"""
Tighten footer vertical spacing across all pages.
Footer marker: background-color:#001F3F or the Applications/Features/Gallery h4 columns.
"""
import requests, sys, re
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

AZURE = "https://azure-nightingale-589250.hostingersite.com"
s = requests.Session()
s.auth = ("mikeoliveraz@gmail.com", "vlop MpGU Os2V xDSI C6T7 2fAN")

GRID_CSS = """
.wp-block-columns.is-layout-flex { display: flex !important; flex-wrap: wrap !important; flex-direction: row !important; gap: 20px; }
.wp-block-columns.is-layout-flex > .wp-block-column { flex: 1 1 30% !important; min-width: 250px !important; max-width: 33% !important; word-wrap: break-word !important; overflow-wrap: break-word !important; }
@media (max-width: 900px) { .wp-block-columns.is-layout-flex > .wp-block-column { flex: 1 1 45% !important; max-width: 48% !important; } }
@media (max-width: 600px) { .wp-block-columns.is-layout-flex > .wp-block-column { flex: 1 1 100% !important; max-width: 100% !important; } }
.wp-block-column p, .wp-block-column h3 { word-wrap: break-word !important; overflow-wrap: break-word !important; white-space: normal !important; }
"""

r_all = s.get(f"{AZURE}/wp-json/wp/v2/pages", params={"per_page": 50})
pages = r_all.json()
print(f"Processing {len(pages)} pages...\n")

for page in pages:
    pid = page['id']
    slug = page['slug']
    content = page['content']['rendered']
    if not content.strip():
        continue
    
    # Find footer by looking for the Applications column header
    fidx = content.find('Applications</h4>')
    if fidx < 0:
        fidx = content.find('#001F3F')
    if fidx < 0:
        continue
    
    # Go back to find the start of the footer container
    footer_start = content.rfind('<div', 0, fidx)
    for _ in range(10):
        prev = content.rfind('<div', 0, footer_start)
        if prev < 0:
            break
        chunk = content[prev:footer_start]
        if '#001F3F' in chunk or 'padding' in chunk:
            footer_start = prev
            break
        footer_start = prev

    original = content
    before = content[:footer_start]
    footer = content[footer_start:]
    
    # Tighten footer spacing
    # h4 margin-bottom
    footer = footer.replace('margin-bottom:16px;font-weight:600', 'margin-bottom:8px;font-weight:600')
    # Link margins
    footer = footer.replace('margin:6px 0', 'margin:3px 0')
    # Bottom bar
    footer = footer.replace('margin-top:18px;padding:20px 0', 'margin-top:10px;padding:8px 0')
    footer = footer.replace('margin-top:40px;padding:20px 0', 'margin-top:10px;padding:8px 0')
    footer = footer.replace('gap:12px', 'gap:8px')
    # Footer outer padding
    footer = re.sub(r'padding:(\d+)px (\d+)px;max-width:1200px', 
                    lambda m: f'padding:{max(12, int(m.group(1))//2)}px {m.group(2)}px;max-width:1200px', footer)
    
    content = before + footer
    
    if pid == 1313:
        if 'flex: 1 1 30%' not in content:
            content = content.replace('</style>', GRID_CSS + '\n</style>', 1)
    
    if content != original:
        r2 = s.post(f"{AZURE}/wp-json/wp/v2/pages/{pid}", json={"content": content})
        print(f"  {slug}: tightened -> {'OK' if r2.status_code == 200 else f'FAILED {r2.status_code}'}")
    else:
        print(f"  {slug}: already tight")

print("\nDone!")
