"""Remove old conflicting nav CSS rules from the homepage, keep only the new consolidated ones."""
import requests, re, sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

BASE = "https://polysaas.online"
AUTH = ("mikeoliveraz@gmail.com", "vlop MpGU Os2V xDSI C6T7 2fAN")

r = requests.get(BASE + "/wp-json/wp/v2/pages/1313",
                 params={"context": "edit", "_fields": "content"},
                 auth=AUTH, timeout=45)
content = r.json()["content"]["raw"]

# Old conflicting nav rules to remove (keeping only the new consolidated block)
old_rules = [
    # Dark mode nav from first style block
    """/* Dark mode nav visibility */
body.dark-mode .header-navigation .menu > li > a,
body.dark-mode .header-navigation .menu > li > a:visited {
    color: var(--ps-text) !important;
}
body.dark-mode .header-navigation .menu > li.current-menu-item > a {
    color: var(--ps-primary) !important;
}""",
    # Light mode nav rules
    """/* Navigation */
.header-navigation .menu > li > a {
    color: #1F2937 !important;
    font-weight: 500;
    font-size: 0.9rem;
    letter-spacing: 0.01em;
}
.header-navigation .menu > li > a:hover {
    color: #0F766E !important;
}
.header-navigation .menu > li.current-menu-item > a {
    color: #001F3F !important;
}""",
    # Generic dark mode nav overrides
    """body.dark-mode .header-navigation .menu > li > a,
body.dark-mode .header-navigation .menu > li > a:visited,
body.dark-mode .site-header .header-navigation a {
    color: #F1F5F9 !important;
}
body.dark-mode .header-navigation .menu > li.current-menu-item > a {
    color: #60A5FA !important;
}""",
    # From the generic dark mode block
    """.header-navigation .menu > li > a,
.header-navigation .menu > li > a:visited {
    color: var(--ps-text) !important;
}
.header-navigation .menu > li > a:hover {
    color: var(--ps-accent) !important;
}""",
]

count = 0
for old in old_rules:
    if old in content:
        content = content.replace(old, '')
        count += 1
        print(f"Removed old nav rule block #{count}")

print(f"\nRemoved {count} old conflicting nav rule blocks")

# Verify the new consolidated block is still there
if "Nav menu: light mode - current=blue" in content:
    print("New consolidated nav CSS is present")
else:
    print("WARNING: New nav CSS not found!")

r2 = requests.post(BASE + "/wp-json/wp/v2/pages/1313",
                   auth=AUTH,
                   json={"content": content},
                   timeout=45)
print(f"Update: {r2.status_code}")
if r2.status_code == 200:
    print("SUCCESS - Old nav rules cleaned up")
else:
    print(f"Error: {r2.text[:300]}")
