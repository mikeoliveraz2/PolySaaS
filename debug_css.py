"""Fetch all CSS from the page and find rules affecting block group widths."""
import requests, re, sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

BASE = "https://azure-nightingale-589250.hostingersite.com"

r = requests.get(BASE, timeout=30)
html = r.text

# Extract all inline <style> blocks
styles = re.findall(r'<style[^>]*>(.*?)</style>', html, re.DOTALL)
all_css = '\n'.join(styles)

# Also get linked stylesheets
css_links = re.findall(r"<link[^>]+href=['\"]([^'\"]+\.css[^'\"]*)['\"]", html)
for link in css_links:
    try:
        if link.startswith('//'):
            link = 'https:' + link
        elif link.startswith('/'):
            link = BASE + link
        cr = requests.get(link, timeout=10)
        if cr.status_code == 200:
            all_css += '\n' + cr.text
    except:
        pass

print(f"Total CSS length: {len(all_css)} chars")

# Search for rules related to wp-block-group and width
patterns_to_find = [
    r'[^\n{}]*wp-block-group[^\n{}]*\{[^}]*(?:max-width|width)[^}]*\}',
    r'[^\n{}]*entry-content[^\n{}]*\{[^}]*(?:max-width|width)[^}]*\}',
    r'[^\n{}]*is-layout[^\n{}]*\{[^}]*(?:max-width|width)[^}]*\}',
    r'[^\n{}]*content-area[^\n{}]*\{[^}]*(?:max-width|width)[^}]*\}',
]

for pat in patterns_to_find:
    matches = re.findall(pat, all_css)
    if matches:
        print(f"\n=== Pattern: {pat[:50]}... ===")
        for m in matches[:10]:
            m_clean = m.strip()
            if len(m_clean) > 300:
                m_clean = m_clean[:300] + '...'
            print(f"  {m_clean}")

# Specifically look for !important on width/max-width near wp-block-group
print("\n\n=== Searching for !important width rules ===")
important_rules = re.findall(r'[^\n{}]*\{[^}]*(?:max-)?width[^;]*!important[^}]*\}', all_css)
for rule in important_rules[:20]:
    rule_clean = rule.strip()
    if len(rule_clean) > 300:
        rule_clean = rule_clean[:300] + '...'
    print(f"  {rule_clean}")
