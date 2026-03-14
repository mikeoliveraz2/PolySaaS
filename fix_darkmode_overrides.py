"""
Fix the hardcoded colors in Shela's palette CSS that override dark mode variables.
Replace hardcoded colors with CSS variable references so dark mode toggle works properly.
"""
import requests, sys, re
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

AZURE = "https://azure-nightingale-589250.hostingersite.com"
s = requests.Session()
s.auth = ("mikeoliveraz@gmail.com", "vlop MpGU Os2V xDSI C6T7 2fAN")

# These are the hardcoded color replacements needed in the second CSS block
# Map hardcoded colors -> CSS variable equivalents
REPLACEMENTS = [
    # Header background
    ('background: #ffffff !important;', 'background: var(--ps-bg) !important;'),
    ('background:#ffffff !important;', 'background: var(--ps-bg) !important;'),
    ('background: #FFFFFF !important;', 'background: var(--ps-bg) !important;'),
    
    # Body text color
    ('color: #1F2937;', 'color: var(--ps-text);'),
    ('color:#1F2937;', 'color: var(--ps-text);'),
    ('color: #1F2937 !important;', 'color: var(--ps-text) !important;'),
    ('color:#1F2937 !important;', 'color: var(--ps-text) !important;'),
    
    # Primary/heading color (but NOT inside :root or body.dark-mode blocks)
    ('color: #001F3F !important;', 'color: var(--ps-primary) !important;'),
    ('color:#001F3F !important;', 'color: var(--ps-primary) !important;'),
    ('color: #001F3F;', 'color: var(--ps-primary);'),
    ('color:#001F3F;', 'color: var(--ps-primary);'),
    
    # Secondary color
    ('color: #475569 !important;', 'color: var(--ps-secondary) !important;'),
    ('color:#475569 !important;', 'color: var(--ps-secondary) !important;'),
    
    # Muted text color
    ('color: #4B5563 !important;', 'color: var(--ps-text-muted) !important;'),
    ('color:#4B5563 !important;', 'color: var(--ps-text-muted) !important;'),
    
    # Accent color for links and hovers
    ('color: #0F766E !important;', 'color: var(--ps-accent) !important;'),
    ('color:#0F766E !important;', 'color: var(--ps-accent) !important;'),
    ('color: #0F766E;', 'color: var(--ps-accent);'),
    ('color:#0F766E;', 'color: var(--ps-accent);'),
    
    # Footer background
    ('background: #001F3F !important;', 'background: var(--ps-footer-bg) !important;'),
    ('background:#001F3F !important;', 'background: var(--ps-footer-bg) !important;'),
    
    # Footer text
    ('color: #E5E7EB;', 'color: var(--ps-footer-text);'),
    ('color:#E5E7EB;', 'color: var(--ps-footer-text);'),
    
    # Card shadow
    ('box-shadow: 0 1px 3px rgba(0,0,0,0.04);', 'box-shadow: 0 1px 3px var(--ps-card-shadow);'),
    
    # CTA button backgrounds (accent)
    ('background-color: #0F766E !important;', 'background-color: var(--ps-accent) !important;'),
    ('background-color:#0F766E !important;', 'background-color: var(--ps-accent) !important;'),
    ('background-color: #115e59 !important;', 'background-color: #0d5f58 !important;'),
    
    # Header box shadow for dark mode
    ('box-shadow: 0 1px 3px rgba(0,0,0,0.06);', 'box-shadow: 0 1px 3px var(--ps-card-shadow);'),
]

# Also need to add dark-mode-specific nav overrides
DARK_NAV_ADDITIONS = """
/* Dark mode nav visibility */
body.dark-mode .header-navigation .menu > li > a,
body.dark-mode .header-navigation .menu > li > a:visited {
    color: var(--ps-text) !important;
}
body.dark-mode .header-navigation .menu > li.current-menu-item > a {
    color: var(--ps-primary) !important;
}
body.dark-mode .site-branding .site-title,
body.dark-mode .site-branding .site-title a {
    color: var(--ps-primary) !important;
}
body.dark-mode #masthead,
body.dark-mode .site-header,
body.dark-mode .site-header-inner-wrap {
    background-color: var(--ps-header-bg) !important;
    background: var(--ps-header-bg) !important;
}
body.dark-mode h1, body.dark-mode h2, body.dark-mode h3,
body.dark-mode h4, body.dark-mode h5, body.dark-mode h6 {
    color: var(--ps-primary) !important;
}
body.dark-mode p, body.dark-mode li, body.dark-mode span {
    color: var(--ps-text);
}
body.dark-mode a { color: var(--ps-primary); }
body.dark-mode a:hover { color: var(--ps-accent) !important; }
body.dark-mode .site-footer a { color: var(--ps-accent) !important; }
/* Dark mode hero/section backgrounds */
body.dark-mode .wp-block-group[style*="background-color"],
body.dark-mode div[style*="background-color:#F3F4F6"],
body.dark-mode div[style*="background-color:#f3f4f6"],
body.dark-mode div[style*="background-color:#f5f5f5"],
body.dark-mode div[style*="background-color:#FFFFFF"],
body.dark-mode div[style*="background-color:#ffffff"],
body.dark-mode div[style*="background:#F3F4F6"],
body.dark-mode div[style*="background:#f3f4f6"] {
    background-color: var(--ps-bg-alt) !important;
    background: var(--ps-bg-alt) !important;
}
body.dark-mode .entry-content-wrap {
    background-color: var(--ps-bg) !important;
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
    
    # Apply color replacements (only in the second style block, not in :root or body.dark-mode definitions)
    # Find all style blocks
    style_blocks = list(re.finditer(r'(<style[^>]*>)(.*?)(</style>)', content, re.DOTALL))
    
    for match in reversed(style_blocks):
        css = match.group(2)
        
        # Skip the first style block (dark mode variables) - it has :root and body.dark-mode defs
        if ':root {' in css and 'body.dark-mode {' in css:
            continue
        
        # This is Shela's palette block or similar - apply replacements
        for old, new in REPLACEMENTS:
            css = css.replace(old, new)
        
        # Add dark mode nav additions if not already present
        if 'Dark mode nav visibility' not in css:
            css = css + '\n' + DARK_NAV_ADDITIONS
        
        # Reconstruct
        new_block = match.group(1) + css + match.group(3)
        content = content[:match.start()] + new_block + content[match.end():]
    
    if content != original:
        r2 = s.post(f"{AZURE}/wp-json/wp/v2/pages/{pid}", json={"content": content})
        if r2.status_code == 200:
            print(f"  {slug}: dark mode overrides fixed")
            fixed += 1
        else:
            print(f"  {slug}: FAILED {r2.status_code}")

print(f"\nFixed {fixed} pages")
print("Done!")
