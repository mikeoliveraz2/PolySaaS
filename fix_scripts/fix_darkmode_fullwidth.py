"""Remove white gaps in dark mode - make content area truly full-bleed dark."""
import requests, re, sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

BASE = "https://polysaas.online"
AUTH = ("mikeoliveraz@gmail.com", "vlop MpGU Os2V xDSI C6T7 2fAN")

r = requests.get(BASE + "/wp-json/wp/v2/pages/1313",
                 params={"context": "edit", "_fields": "content"},
                 auth=AUTH, timeout=45)
content = r.json()["content"]["raw"]

# The white gaps come from:
# 1. .entry.single-entry has box-shadow and white background (boxed style)
# 2. .entry-content-wrap has padding: 2rem
# 3. The site wrapper / main content area has a white background
#
# We need to add dark mode CSS to override these

dark_fullbleed_css = """
/* Dark mode: remove boxed content white background and gaps */
body.dark-mode .entry.single-entry,
body.dark-mode .entry-content-wrap,
body.dark-mode .content-style-boxed .entry.single-entry {
    background-color: var(--ps-bg, #0F172A) !important;
    background: var(--ps-bg, #0F172A) !important;
    box-shadow: none !important;
}
body.dark-mode #wrapper,
body.dark-mode .site,
body.dark-mode #main,
body.dark-mode .site-container,
body.dark-mode .content-area,
body.dark-mode .site-main {
    background-color: var(--ps-bg, #0F172A) !important;
    background: var(--ps-bg, #0F172A) !important;
}
body.dark-mode .wp-block-group__inner-container {
    background: transparent !important;
}
"""

# Find the existing dark mode CSS style block and append to it
# Look for the dark mode body background rule
marker = "body.dark-mode .site-branding .site-title a {"
pos = content.find(marker)
if pos < 0:
    # Try another known dark mode rule
    marker = "body.dark-mode {"
    pos = content.find(marker)

if pos < 0:
    print("Could not find dark mode CSS block")
    sys.exit(1)

# Find the </style> that closes this block
style_end = content.find("</style>", pos)
if style_end < 0:
    # It might be </p></style> due to WordPress formatting
    style_end = content.find("</p>", pos)

# Check what's right before the closing tag
print(f"Found style block end at {style_end}")
snippet = content[style_end-200:style_end+20]
print(f"Before style end:\n{snippet}")

# Insert our CSS before the closing </style> (or </p> if WP wrapped it)
close_tag = content[style_end:style_end+10]
if '</p>' in close_tag:
    insert_point = style_end
    content = content[:insert_point] + dark_fullbleed_css + content[insert_point:]
elif '</style>' in close_tag:
    insert_point = style_end
    content = content[:insert_point] + dark_fullbleed_css + content[insert_point:]
else:
    print(f"Unexpected close tag: {close_tag}")
    sys.exit(1)

print("Inserted dark mode full-bleed CSS")

r2 = requests.post(BASE + "/wp-json/wp/v2/pages/1313",
                   auth=AUTH,
                   json={"content": content},
                   timeout=45)
print(f"Update: {r2.status_code}")
if r2.status_code == 200:
    print("SUCCESS - Dark mode now has full-width/height dark background")
else:
    print(f"Error: {r2.text[:300]}")
