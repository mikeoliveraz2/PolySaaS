"""
Two fixes:
1. Menu bar: light grey in light mode, slightly lighter blue in dark mode
2. Toggle button: add hover tooltip showing "Switch to dark/light mode"
"""
import requests, re, sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

AZURE = "https://azure-nightingale-589250.hostingersite.com"
s = requests.Session()
s.auth = ("mikeoliveraz@gmail.com", "vlop MpGU Os2V xDSI C6T7 2fAN")

r = s.get(f"{AZURE}/wp-json/wp/v2/pages", params={
    "per_page": 100, "context": "edit", "_fields": "id,slug,content"
})
all_pages = r.json()

# New toggle block with title attribute for hover tooltip + dynamic title update
NEW_TOGGLE = '''<button class="ps-theme-toggle" id="ps-dark-toggle" onclick="document.body.classList.toggle('dark-mode');localStorage.setItem('ps-dark-mode',document.body.classList.contains('dark-mode'));var i=document.getElementById('ps-toggle-icon');var dm=document.body.classList.contains('dark-mode');if(i)i.innerHTML=dm?'\\u2600':'\\u263E';this.title=dm?'Switch to light mode':'Switch to dark mode';" aria-label="Toggle dark mode" title="Switch to dark mode" style="position:fixed;top:90px;right:20px;z-index:9999;background:var(--ps-card-bg,#f0f0f0);border:2px solid #94a3b8;border-radius:50%;width:44px;height:44px;cursor:pointer;font-size:20px;display:flex;align-items:center;justify-content:center;box-shadow:0 2px 12px rgba(0,0,0,0.15);transition:all 0.3s ease;color:var(--ps-primary,#001F3F);"><span id="ps-toggle-icon">&#9790;</span></button>
<script>
(function(){var s=localStorage.getItem('ps-dark-mode');var b=document.getElementById('ps-dark-toggle');if(s==='true'){document.body.classList.add('dark-mode');var i=document.getElementById('ps-toggle-icon');if(i)i.innerHTML='\\u2600';if(b)b.title='Switch to light mode';}else{if(b)b.title='Switch to dark mode';}})();
</script>'''

# Old toggle pattern to find and replace
TOGGLE_PATTERN = re.compile(
    r'<button class="ps-theme-toggle".*?</button>\s*<script>\s*\(function\(\)\{var s=localStorage.*?\}\)\(\);\s*</script>',
    re.DOTALL
)

updated = 0
for page in all_pages:
    slug = page['slug']
    raw = page['content']['raw']
    new_raw = raw
    changed = False

    # Fix 1: Menu bar colors
    if '--ps-header-bg: #FFFFFF' in new_raw:
        new_raw = new_raw.replace('--ps-header-bg: #FFFFFF', '--ps-header-bg: #F1F5F9')
        changed = True
    if '--ps-header-bg: #0F172A' in new_raw:
        new_raw = new_raw.replace('--ps-header-bg: #0F172A', '--ps-header-bg: #1E293B')
        changed = True
    if 'background: #ffffff !important' in new_raw:
        new_raw = new_raw.replace('background: #ffffff !important', 'background: #F1F5F9 !important')
        changed = True

    # Fix 2: Replace toggle with new version that has hover tooltip
    if 'ps-theme-toggle' in new_raw:
        match = TOGGLE_PATTERN.search(new_raw)
        if match:
            old_toggle = match.group(0)
            if 'this.title=' not in old_toggle:
                new_raw = new_raw.replace(old_toggle, NEW_TOGGLE)
                changed = True

    if changed:
        r2 = s.post(f"{AZURE}/wp-json/wp/v2/pages/{page['id']}", json={"content": new_raw})
        if r2.status_code == 200:
            updated += 1
            print(f"  {slug}: updated")
        else:
            print(f"  {slug}: FAILED {r2.status_code}")

print(f"\nUpdated {updated} pages")
