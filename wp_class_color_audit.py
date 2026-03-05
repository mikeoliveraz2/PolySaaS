"""Audit Bricks element classes and their inline style colors across all pages.
Identifies which CSS classes carry off-brand colors so we can write class-based fixes."""
import requests
import re
from collections import defaultdict

SITE = "https://azure-nightingale-589250.hostingersite.com"

BRAND_COLORS = {
    '#003399', '#003388', '#03a9f4', '#81d4fa', '#e0e0e0',
    '#ffeb3b', '#8bc34a', '#9e9e9e', '#ffffff', '#000000',
    '#f8f8f8', '#f5f5f5', '#1e1e1e', '#32373c',
}

OFF_BRAND = {'#15ff00', '#59ff00', '#6bff9f', '#00ff59', '#d63637', '#555555'}

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
    ('Liferay', '/liferay/'),
    ('OpenAPI', '/openapi/'),
    ('Pricing', '/pricing/'),
    ('Blog', '/blog/'),
    ('About Us', '/about-us/'),
    ('Gallery Images', '/gallery-images/'),
    ('Gallery Videos', '/gallery-videos/'),
    ('CTA Templates', '/cta-templates/'),
    ('For Partners', '/for-parners-resellers-and-large-enterprises/'),
]

def extract_bricks_elements_with_styles(html):
    """Extract Bricks elements with their IDs, classes, and inline background/color styles."""
    results = []
    pattern = re.findall(
        r'<(?:section|div|a|button|span|h[1-6]|p)'
        r'[^>]*?'
        r'(?:id="([^"]*)")?'
        r'[^>]*?'
        r'class="([^"]*brxe-[^"]*)"'
        r'[^>]*?'
        r'(?:style="([^"]*)")?'
        r'[^>]*?>',
        html
    )
    for elem_id, classes, style in pattern:
        if not style:
            continue
        colors_in_style = re.findall(r'#[0-9a-fA-F]{3,8}\b', style)
        gradients_in_style = re.findall(r'(?:linear|radial)-gradient\([^)]+(?:\([^)]*\))*[^)]*\)', style)
        if colors_in_style or gradients_in_style:
            brxe_classes = [c for c in classes.split() if c.startswith('brxe-')]
            results.append({
                'id': elem_id,
                'classes': brxe_classes,
                'all_classes': classes,
                'style': style.strip(),
                'colors': [c.lower() for c in colors_in_style],
                'gradients': gradients_in_style,
            })
    return results

def extract_style_blocks(html):
    """Extract <style> blocks and find Bricks class-based color rules."""
    results = []
    style_blocks = re.findall(r'<style[^>]*>(.*?)</style>', html, re.DOTALL)
    for block in style_blocks:
        rules = re.findall(
            r'(\.brxe-[a-zA-Z0-9_-]+[^{]*)\{([^}]*(?:color|background|gradient)[^}]*)\}',
            block, re.IGNORECASE
        )
        for selector, body in rules:
            colors = re.findall(r'#[0-9a-fA-F]{3,8}\b', body)
            if colors:
                results.append({
                    'selector': selector.strip(),
                    'body': body.strip(),
                    'colors': [c.lower() for c in colors],
                })
    return results


if __name__ == '__main__':
    session = requests.Session()
    session.headers.update({'User-Agent': 'PolySaaS-Audit/1.0'})

    print("=" * 100)
    print("BRICKS CLASS + INLINE STYLE COLOR AUDIT")
    print(f"Site: {SITE}")
    print("=" * 100)

    all_offbrand = []
    page_elements = {}

    for name, slug in SLUGS:
        url = f"{SITE}{slug}"
        try:
            resp = session.get(url, timeout=15)
            if resp.status_code != 200:
                print(f"  SKIP {name}: HTTP {resp.status_code}")
                continue

            html = resp.text
            elements = extract_bricks_elements_with_styles(html)
            style_rules = extract_style_blocks(html)

            offbrand_inline = []
            for el in elements:
                for c in el['colors']:
                    if c in OFF_BRAND or (c not in BRAND_COLORS and not c.startswith('#8')):
                        offbrand_inline.append(el)
                        break

            offbrand_css = []
            for rule in style_rules:
                for c in rule['colors']:
                    if c in OFF_BRAND:
                        offbrand_css.append(rule)
                        break

            if offbrand_inline or offbrand_css:
                print(f"\n  [{name}] — {len(offbrand_inline)} off-brand inline elements, {len(offbrand_css)} off-brand CSS rules")
                for el in offbrand_inline:
                    print(f"    ID: {el['id'] or '(none)'}  Classes: {' '.join(el['classes'])}")
                    print(f"      Colors: {el['colors']}")
                    print(f"      Style: {el['style'][:120]}")
                for rule in offbrand_css:
                    print(f"    CSS: {rule['selector']}")
                    print(f"      Colors: {rule['colors']}")
                all_offbrand.extend([(name, el) for el in offbrand_inline])
            else:
                print(f"  [{name}] — clean (no off-brand inline colors)")

            page_elements[name] = elements

        except Exception as e:
            print(f"  ERROR {name}: {e}")

    print(f"\n{'=' * 100}")
    print("ELEMENT ID → PAGE MAPPING (for targeted fixes)")
    print(f"{'=' * 100}")
    for name, el in all_offbrand:
        eid = el['id'] or '(no id)'
        classes = ' '.join(el['classes'])
        colors = ', '.join(el['colors'])
        print(f"  {name:25s} #{eid:20s} {classes:30s} colors: {colors}")

    print(f"\n{'=' * 100}")
    print("SUMMARY")
    print(f"{'=' * 100}")
    print(f"  Total pages scanned: {len(page_elements)}")
    print(f"  Pages with off-brand inline colors: {len(set(n for n, _ in all_offbrand))}")
    print(f"  Total off-brand elements: {len(all_offbrand)}")
