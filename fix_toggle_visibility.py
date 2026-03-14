"""
1. Make toggle button more visible in light mode (darker border, slight background tint)
2. Make dark mode text white instead of grey across all pages
"""
import requests, sys, re
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

AZURE = "https://azure-nightingale-589250.hostingersite.com"
s = requests.Session()
s.auth = ("mikeoliveraz@gmail.com", "vlop MpGU Os2V xDSI C6T7 2fAN")

# --- Fix 1: Toggle button visibility ---
# Current toggle style: border:2px solid var(--ps-border,#e5e7eb) - too subtle in light mode
# New: darker border, slight shadow, background tint

OLD_TOGGLE_STYLE = 'style="position:fixed;top:80px;right:20px;z-index:9999;background:var(--ps-card-bg,#fff);border:2px solid var(--ps-border,#e5e7eb);border-radius:50%;width:40px;height:40px;cursor:pointer;font-size:18px;display:flex;align-items:center;justify-content:center;box-shadow:0 2px 8px rgba(0,0,0,0.1);transition:all 0.3s ease;"'

NEW_TOGGLE_STYLE = 'style="position:fixed;top:80px;right:20px;z-index:9999;background:var(--ps-card-bg,#f0f0f0);border:2px solid #94a3b8;border-radius:50%;width:44px;height:44px;cursor:pointer;font-size:20px;display:flex;align-items:center;justify-content:center;box-shadow:0 2px 12px rgba(0,0,0,0.15);transition:all 0.3s ease;color:var(--ps-primary,#001F3F);"'

# --- Fix 2: Dark mode text should be white, not grey ---
# Current: --ps-text: #E2E8F0 (light slate) and --ps-text-muted: #94A3B8 (grey)
# New: --ps-text: #F1F5F9 (near-white) and --ps-text-muted: #CBD5E1 (lighter grey)
# Also nav text in dark mode needs to be white

DARK_TEXT_FIXES = """
/* Dark mode: whiter text */
body.dark-mode {
    --ps-text: #F1F5F9 !important;
    --ps-text-muted: #CBD5E1 !important;
}
body.dark-mode p,
body.dark-mode li,
body.dark-mode span,
body.dark-mode div,
body.dark-mode td,
body.dark-mode th,
body.dark-mode label {
    color: #F1F5F9 !important;
}
body.dark-mode .header-navigation .menu > li > a,
body.dark-mode .header-navigation .menu > li > a:visited,
body.dark-mode .site-header .header-navigation a {
    color: #F1F5F9 !important;
}
body.dark-mode .header-navigation .menu > li.current-menu-item > a {
    color: #60A5FA !important;
}
body.dark-mode .site-branding .site-title,
body.dark-mode .site-branding .site-title a {
    color: #60A5FA !important;
}
/* Toggle button visibility in light mode */
.ps-theme-toggle {
    border: 2px solid #94a3b8 !important;
    box-shadow: 0 2px 12px rgba(0,0,0,0.15) !important;
    background: #f0f4f8 !important;
    color: #001F3F !important;
}
body.dark-mode .ps-theme-toggle {
    border-color: #60A5FA !important;
    background: #1E293B !important;
    color: #60A5FA !important;
    box-shadow: 0 2px 12px rgba(96,165,250,0.2) !important;
}
"""

r = s.get(f"{AZURE}/wp-json/wp/v2/pages", params={"per_page": 100, "_fields": "id,slug,content"})
pages = r.json()
print(f"Found {len(pages)} pages")

fixed = 0
for page in pages:
    pid = page['id']
    slug = page['slug']
    content = page['content']['rendered']
    
    if not content.strip():
        continue
    
    original = content
    
    # Fix toggle button inline style
    if OLD_TOGGLE_STYLE in content:
        content = content.replace(OLD_TOGGLE_STYLE, NEW_TOGGLE_STYLE)
    
    # Update dark mode text variables in the first style block (the dark mode system)
    # Change --ps-text from #E2E8F0 to #F1F5F9
    content = content.replace('--ps-text: #E2E8F0;', '--ps-text: #F1F5F9;')
    content = content.replace('--ps-text-muted: #94A3B8;', '--ps-text-muted: #CBD5E1;')
    # Also in the second dark mode variables block
    content = content.replace('--ps-secondary: #94A3B8;', '--ps-secondary: #CBD5E1;')
    
    # Add the dark text fixes CSS if not already present
    if 'Dark mode: whiter text' not in content:
        # Find the last </style> before content and add there
        # Or add to the second style block
        style_blocks = list(re.finditer(r'(<style[^>]*>)(.*?)(</style>)', content, re.DOTALL))
        if style_blocks:
            last_style = style_blocks[-1]
            css = last_style.group(2)
            css = css + '\n' + DARK_TEXT_FIXES
            new_block = last_style.group(1) + css + last_style.group(3)
            content = content[:last_style.start()] + new_block + content[last_style.end():]
    
    if content != original:
        r2 = s.post(f"{AZURE}/wp-json/wp/v2/pages/{pid}", json={"content": content})
        if r2.status_code == 200:
            print(f"  {slug}: updated")
            fixed += 1
        else:
            print(f"  {slug}: FAILED {r2.status_code}")

print(f"\nFixed {fixed} pages")
print("Done!")
