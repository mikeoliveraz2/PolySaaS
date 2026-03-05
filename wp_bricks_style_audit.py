"""Extract ALL Bricks <style> block rules per page to map element IDs to their colors."""
import requests
import re
from collections import defaultdict

SITE = "https://azure-nightingale-589250.hostingersite.com"

BRAND_PALETTE = {
    '#003399', '#003388', '#03a9f4', '#81d4fa', '#e0e0e0',
    '#ffeb3b', '#8bc34a', '#9e9e9e', '#ffffff', '#000000',
    '#f8f8f8', '#f5f5f5', '#1e1e1e', '#32373c', '#072027',
}

SLUGS = [
    ('Home', '/'),
    ('Architecture', '/architecture/'),
    ('Portal', '/portal/'),
    ('Atomic Services', '/atomic-services/'),
    ('Dynamic Orchestration', '/dynamic-orchestration/'),
    ('PolySniffer', '/polysniffer/'),
    ('AI As Peers', '/ai-as-peers/'),
    ('Apps As Peers', '/apps-as-peers/'),
    ('Bundled Applications', '/bundled-applications/'),
    ('External Applications', '/external-applications/'),
    ('Odoo', '/odoo/'),
    ('NextCloud', '/nextcloud/'),
    ('MatterMost', '/mattermost/'),
    ('WordPress', '/wordpress/'),
    ('PolySysMon', '/polysysmon/'),
    ('Monitor Logger', '/monitor-logger/'),
    ('Sign Up', '/sign-up/'),
    ('Dolibarr', '/dolibarr/'),
    ('Pricing', '/pricing/'),
    ('Blog', '/blog/'),
    ('About Us', '/about-us/'),
    ('Gallery Images', '/gallery-images/'),
    ('Gallery Videos', '/gallery-videos/'),
    ('CTA Templates', '/cta-templates/'),
]

session = requests.Session()
session.headers.update({'User-Agent': 'PolySaaS-Audit/1.0'})

print("=" * 100)
print("BRICKS <style> BLOCK AUDIT — PER-PAGE COLOR RULES")
print("=" * 100)

all_page_rules = {}

for name, slug in SLUGS:
    url = f"{SITE}{slug}"
    try:
        resp = session.get(url, timeout=15)
        if resp.status_code != 200:
            continue
        html = resp.text

        style_blocks = re.findall(r'<style[^>]*>(.*?)</style>', html, re.DOTALL)
        full_css = '\n'.join(style_blocks)

        brxe_rules = re.findall(
            r'(#brxe-[a-zA-Z0-9]+[^{]*)\{([^}]+)\}',
            full_css
        )

        page_color_rules = []
        for selector, body in brxe_rules:
            hex_colors = re.findall(r'#[0-9a-fA-F]{6}\b', body)
            hex_colors = [c.lower() for c in hex_colors]
            gradients = re.findall(r'(?:linear|radial)-gradient\([^)]+(?:\([^)]*\))*[^)]*\)', body)
            
            if hex_colors or gradients:
                off_brand = [c for c in hex_colors if c not in BRAND_PALETTE]
                page_color_rules.append({
                    'selector': selector.strip(),
                    'body': body.strip(),
                    'hex_colors': hex_colors,
                    'off_brand': off_brand,
                    'gradients': gradients,
                })

        all_page_rules[name] = page_color_rules

        off_count = sum(1 for r in page_color_rules if r['off_brand'])
        total = len(page_color_rules)
        if off_count > 0:
            print(f"\n  [{name}] — {total} color rules, {off_count} with OFF-BRAND colors:")
            for r in page_color_rules:
                if r['off_brand']:
                    print(f"    {r['selector']}")
                    print(f"      Off-brand: {r['off_brand']}")
                    body_short = r['body'][:150].replace('\n', ' ')
                    print(f"      Rule: {body_short}")
                    if r['gradients']:
                        for g in r['gradients']:
                            print(f"      Gradient: {g[:100]}")
        else:
            print(f"  [{name}] — {total} color rules, all on-brand")

    except Exception as e:
        print(f"  ERROR {name}: {e}")

print(f"\n{'=' * 100}")
print("PAGES NEEDING FIXES:")
print(f"{'=' * 100}")
for name, rules in all_page_rules.items():
    off = [r for r in rules if r['off_brand']]
    if off:
        print(f"\n  {name}:")
        for r in off:
            print(f"    {r['selector']} → {r['off_brand']}")

print(f"\n{'=' * 100}")
print("ALL UNIQUE OFF-BRAND COLORS SITE-WIDE:")
print(f"{'=' * 100}")
off_brand_map = defaultdict(list)
for name, rules in all_page_rules.items():
    for r in rules:
        for c in r['off_brand']:
            off_brand_map[c].append((name, r['selector']))

for color, usages in sorted(off_brand_map.items()):
    print(f"\n  {color}:")
    for page, selector in usages:
        print(f"    {page:25s} {selector}")
