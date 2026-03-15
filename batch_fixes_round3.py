"""
Batch fixes:
1. Upload 3 Monitor Logger images + add to page
2. Check/restore Francis Uy on About Us
3. Update timeline: Monitor Logger Q2 release, Q3 update
4. Whitespace reduction on About Us
"""
import requests, re, sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

AZURE = "https://azure-nightingale-589250.hostingersite.com"
s = requests.Session()
s.auth = ("mikeoliveraz@gmail.com", "vlop MpGU Os2V xDSI C6T7 2fAN")

# ══════════════════════════════════════════
# PART 1: Upload Monitor Logger images
# ══════════════════════════════════════════
ML_IMAGES = [
    (r"C:\Users\PC\.cursor\projects\d-PolySaaS\assets\c__Users_PC_AppData_Roaming_Cursor_User_workspaceStorage_77452477b6ce94d3acba53b24d1f01c9_images_Monitor_Logger_Uptrace-6c0f87c7-f27b-4231-8583-13c43cc30ee2.png",
     "monitor-logger-uptrace.png", "Monitor Logger — Uptrace", "Uptrace — real-time log aggregation with search, filtering, time-series visualization, and span-level detail"),
    (r"C:\Users\PC\.cursor\projects\d-PolySaaS\assets\c__Users_PC_AppData_Roaming_Cursor_User_workspaceStorage_77452477b6ce94d3acba53b24d1f01c9_images_Monitor_Logger_Grafana-b2fbb516-c0cd-4514-8784-90457ff8b62f.png",
     "monitor-logger-grafana.png", "Monitor Logger — Grafana Loki", "Grafana with Loki — log exploration, Prometheus integration, and real-time alerting"),
    (r"C:\Users\PC\.cursor\projects\d-PolySaaS\assets\c__Users_PC_AppData_Roaming_Cursor_User_workspaceStorage_77452477b6ce94d3acba53b24d1f01c9_images_Monitor_Logger_Trafik-de34bc65-23fd-4ed2-91bd-365a4ca58596.png",
     "monitor-logger-opensearch.png", "Monitor Logger — OpenSearch Dashboards", "OpenSearch Dashboards — web traffic analysis, RAM usage trends, and error response tracking"),
]

ml_uploaded = []
for path, filename, alt, caption in ML_IMAGES:
    with open(path, 'rb') as f:
        data = f.read()
    r = s.post(f"{AZURE}/wp-json/wp/v2/media",
        headers={"Content-Disposition": f'attachment; filename="{filename}"', "Content-Type": "image/png"},
        data=data)
    if r.status_code == 201:
        url = r.json()['source_url']
        ml_uploaded.append((url, alt, caption))
        print(f"[1] Uploaded {filename}: {url}")
    else:
        print(f"[1] Failed {filename}: {r.status_code}")

# Add to Monitor Logger page
pages = s.get(f"{AZURE}/wp-json/wp/v2/pages", params={
    "per_page": 100, "context": "edit", "_fields": "id,slug,content"
}).json()
page_map = {p['slug']: p for p in pages}

ml_page = page_map.get('monitor-logger-4')
if ml_page and ml_uploaded:
    raw = ml_page['content']['raw']
    img_parts = []
    for url, alt, caption in ml_uploaded:
        img_parts.append(f'''<div style="text-align:center;margin:20px auto;">
<img src="{url}" alt="{alt}" style="width:100%;max-width:800px;border-radius:10px;box-shadow:0 3px 15px rgba(0,0,0,0.1);">
<p style="color:var(--ps-muted,#6B7280);font-size:0.85rem;margin-top:8px;font-style:italic;">{caption}</p>
</div>''')
    img_block = "\n".join(img_parts)
    
    key_cap_idx = raw.find('Key Capabilities')
    if key_cap_idx > 0:
        insert_before = raw.rfind('<h2', max(0, key_cap_idx - 100), key_cap_idx)
        if insert_before < 0:
            insert_before = key_cap_idx
        raw = raw[:insert_before] + img_block + "\n" + raw[insert_before:]
    
    r = s.post(f"{AZURE}/wp-json/wp/v2/pages/{ml_page['id']}", json={"content": raw})
    print(f"[1] Monitor Logger page: {r.status_code} ({len(ml_uploaded)} images)")

# ══════════════════════════════════════════
# PART 2: Check/restore Francis Uy on About Us
# ══════════════════════════════════════════
about = page_map.get('about-us')
if about:
    raw = about['content']['raw']
    
    francis_present = 'Francis Uy' in raw
    stephen_present = 'Stephen Bird' in raw
    print(f"\n[2] Francis Uy: {'PRESENT' if francis_present else 'MISSING'}")
    print(f"[2] Stephen Bird: {'PRESENT' if stephen_present else 'REMOVED'}")
    
    if not francis_present:
        print("[2] Restoring Francis Uy...")
        FRANCIS_CARD = '''<div style="flex:1 1 280px;max-width:380px;background:#fff;border-radius:8px;padding:24px;box-shadow:0 2px 8px rgba(0,0,0,0.06);text-align:center">
<div style="width:100px;height:100px;border-radius:50%;background:#E5E7EB;margin:0 auto 12px auto;display:flex;align-items:center;justify-content:center;font-size:2rem;color:#6B7280">FU</div>
<h3 style="font-size:1.2rem;font-weight:600;margin-bottom:4px;color:var(--ps-primary,#001F3F)">Francis Uy</h3>
<p style="color:var(--ps-muted,#6B7280);font-size:0.85rem;margin-bottom:10px">Salesforce Cloud Administrator &mdash; Yudrio, Inc.</p>
<p style="color:var(--ps-text,#374151);font-size:0.9rem;line-height:1.5;margin-bottom:12px">Salesforce platform specialist with expertise in cloud administration and IT operations. Known for deep technical knowledge, cross-team collaboration, and a positive, solutions-driven approach to enterprise IT challenges.</p>
<a href="https://www.linkedin.com/in/francisuy/" style="display:inline-block;margin-top:8px;color:#2563EB;text-decoration:none;font-size:0.85rem;font-weight:500">LinkedIn &rarr;</a>
</div>'''
        
        # Find Feyzi's card end to insert after
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
                raw = raw[:feyzi_card_end] + "\n" + FRANCIS_CARD + "\n" + raw[feyzi_card_end:]
                print("[2] Francis Uy restored after Feyzi")
    
    # ══════════════════════════════════════════
    # PART 3: Update timeline - Monitor Logger Q2/Q3
    # ══════════════════════════════════════════
    # Q2: add Monitor Logger release
    q2_idx = raw.find('Q2 2026')
    if q2_idx > 0:
        # Find the </ul> in Q2 section to add Monitor Logger before it
        q2_ul_end = raw.find('</ul>', q2_idx)
        if q2_ul_end > 0:
            ml_q2_item = '\n<li><strong>Monitor Logger Release</strong> &mdash; Uptrace, Grafana/Loki, and OpenSearch integration for comprehensive logging and monitoring</li>'
            raw = raw[:q2_ul_end] + ml_q2_item + "\n" + raw[q2_ul_end:]
            print("[3] Added Monitor Logger to Q2 timeline")
    
    # Q3: add Monitor Logger update
    q3_idx = raw.find('Q3 2026')
    if q3_idx > 0:
        q3_ul_end = raw.find('</ul>', q3_idx)
        if q3_ul_end > 0:
            ml_q3_item = '\n<li><strong>Monitor Logger Updates</strong> &mdash; Enhanced alerting, custom dashboards, and advanced log correlation</li>'
            raw = raw[:q3_ul_end] + ml_q3_item + "\n" + raw[q3_ul_end:]
            print("[3] Added Monitor Logger update to Q3 timeline")
    
    # ══════════════════════════════════════════
    # PART 4: Whitespace reduction on About Us
    # ══════════════════════════════════════════
    if 'Homepage-specific gap reduction' in raw or 'Aggressive top whitespace' in raw:
        print("[4] About Us already has whitespace CSS")
    else:
        # Check if it has the logo CSS block and add whitespace rules
        logo_css_idx = raw.find('Header Logo Size Override')
        if logo_css_idx > 0:
            style_end = raw.find('</style>', logo_css_idx)
            if style_end > 0:
                EXTRA_CSS = '''
/* Aggressive top whitespace reduction */
.content-area { margin-top: 0 !important; padding-top: 0 !important; }
.entry-content-wrap { padding-top: 0 !important; margin-top: 0 !important; }
.entry-hero-container-inner { padding: 0 !important; min-height: 0 !important; }
.entry-hero .entry-header { min-height: 0 !important; padding: 5px 0 !important; margin: 0 !important; }
.entry-hero-container { min-height: 0 !important; padding: 0 !important; margin: 0 !important; }
.wp-site-blocks > .entry-content { margin-top: 0 !important; padding-top: 0 !important; }
.site-main { padding-top: 0 !important; margin-top: 0 !important; }
.site-content { padding-top: 0 !important; }
.hentry { margin-top: 0 !important; }
.entry-content { margin-top: 0 !important; padding-top: 0 !important; }
#inner-wrap > .content-area { margin-top: 0 !important; }
.page .entry-header { padding: 5px 0 !important; margin: 0 !important; min-height: 0 !important; }
.page .entry-hero-section { padding: 0 !important; margin: 0 !important; min-height: 0 !important; }
.entry-hero-section-overlay { padding: 0 !important; min-height: 0 !important; }
.hero-section-overlay { padding: 0 !important; min-height: 0 !important; }
.page-hero-section { padding: 0 !important; margin: 0 !important; }
.kadence-page-hero { padding: 0 !important; margin: 0 !important; min-height: 0 !important; }
.wp-block-post-title { margin-top: 0 !important; padding-top: 5px !important; }
.entry-title { margin-top: 0 !important; padding-top: 5px !important; margin-bottom: 5px !important; }
header.entry-header { padding-top: 0 !important; padding-bottom: 0 !important; }
.site-main > article { margin-top: 0 !important; padding-top: 0 !important; }
.site-container > .site-content { padding-top: 0 !important; }
.content-wrap { padding-top: 0 !important; }
'''
                raw = raw[:style_end] + EXTRA_CSS + raw[style_end:]
                print("[4] Added whitespace reduction CSS to About Us")
        else:
            print("[4] No logo CSS block found on About Us")
    
    # Save About Us
    r = s.post(f"{AZURE}/wp-json/wp/v2/pages/{about['id']}", json={"content": raw})
    print(f"\n[2-4] About Us update: {r.status_code}")

print("\nAll done!")
