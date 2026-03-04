"""WordPress site-wide color and gradient audit — fetches rendered CSS from all pages."""
import requests
import re
from html import unescape
from collections import defaultdict

SITE = "https://azure-nightingale-589250.hostingersite.com"

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
]

def extract_colors_from_html(html):
    """Extract all color values from inline styles and style blocks."""
    colors = {
        'hex': [],
        'rgb': [],
        'rgba': [],
        'hsl': [],
        'named': [],
    }

    hex_pattern = re.findall(r'#([0-9a-fA-F]{3,8})\b', html)
    for h in hex_pattern:
        if len(h) in (3, 4, 6, 8):
            colors['hex'].append(f'#{h}')

    rgb_pattern = re.findall(r'rgb\(\s*\d+\s*,\s*\d+\s*,\s*\d+\s*\)', html)
    colors['rgb'] = rgb_pattern

    rgba_pattern = re.findall(r'rgba\(\s*\d+\s*,\s*\d+\s*,\s*\d+\s*,\s*[\d.]+\s*\)', html)
    colors['rgba'] = rgba_pattern

    hsl_pattern = re.findall(r'hsla?\([^)]+\)', html)
    colors['hsl'] = hsl_pattern

    return colors

def extract_gradients(html):
    """Extract all CSS gradient definitions."""
    gradients = []

    linear = re.findall(r'linear-gradient\([^)]+(?:\([^)]*\))*[^)]*\)', html)
    radial = re.findall(r'radial-gradient\([^)]+(?:\([^)]*\))*[^)]*\)', html)
    conic = re.findall(r'conic-gradient\([^)]+(?:\([^)]*\))*[^)]*\)', html)

    for g in linear:
        gradients.append(('linear-gradient', g))
    for g in radial:
        gradients.append(('radial-gradient', g))
    for g in conic:
        gradients.append(('conic-gradient', g))

    return gradients

def extract_backgrounds(html):
    """Extract background and background-color properties from inline styles."""
    backgrounds = []
    bg_pattern = re.findall(r'background(?:-color)?:\s*([^;"]+)', html)
    for bg in bg_pattern:
        bg = bg.strip()
        if bg and bg not in ('none', 'transparent', 'inherit', 'initial', 'unset'):
            if any(c in bg.lower() for c in ['#', 'rgb', 'hsl', 'gradient', 'linear', 'radial']):
                backgrounds.append(bg)
    return backgrounds

def extract_text_colors(html):
    """Extract color properties (text colors)."""
    text_colors = []
    color_pattern = re.findall(r'(?<![a-z-])color:\s*([^;"]+)', html)
    for c in color_pattern:
        c = c.strip()
        if c and c not in ('none', 'transparent', 'inherit', 'initial', 'unset', 'currentColor'):
            text_colors.append(c)
    return text_colors

def extract_container_nesting(html):
    """Detect potentially problematic container nesting in Bricks markup."""
    issues = []
    
    bricks_sections = re.findall(r'<section[^>]*class="[^"]*brxe-section[^"]*"[^>]*>', html)
    bricks_containers = re.findall(r'<div[^>]*class="[^"]*brxe-container[^"]*"[^>]*>', html)
    bricks_blocks = re.findall(r'<div[^>]*class="[^"]*brxe-block[^"]*"[^>]*>', html)
    
    section_count = len(bricks_sections)
    container_count = len(bricks_containers)
    block_count = len(bricks_blocks)
    
    nested_sections = re.findall(
        r'<section[^>]*class="[^"]*brxe-section[^"]*"[^>]*>(?:(?!<\/section>).)*?'
        r'<section[^>]*class="[^"]*brxe-section[^"]*"[^>]*>',
        html, re.DOTALL
    )
    
    nested_containers = re.findall(
        r'<div[^>]*class="[^"]*brxe-container[^"]*"[^>]*>\s*'
        r'<div[^>]*class="[^"]*brxe-container[^"]*"[^>]*>',
        html
    )

    bg_containers = re.findall(
        r'<(?:section|div)[^>]*class="[^"]*brxe-(?:section|container|block)[^"]*"[^>]*'
        r'style="[^"]*background[^"]*"[^>]*>',
        html
    )

    return {
        'sections': section_count,
        'containers': container_count,
        'blocks': block_count,
        'nested_sections': len(nested_sections),
        'nested_containers': len(nested_containers),
        'bg_containers': len(bg_containers),
    }

def normalize_hex(color):
    """Normalize hex colors to 6-digit lowercase."""
    color = color.lower().strip()
    if len(color) == 4:
        return f'#{color[1]*2}{color[2]*2}{color[3]*2}'
    return color

if __name__ == '__main__':
    print("=" * 90)
    print("WORDPRESS SITE-WIDE COLOR, GRADIENT & CONTAINER AUDIT")
    print(f"Site: {SITE}")
    print("=" * 90)

    session = requests.Session()
    session.headers.update({'User-Agent': 'PolySaaS-Audit/1.0'})

    all_hex = defaultdict(list)
    all_rgba = defaultdict(list)
    all_gradients = defaultdict(list)
    all_backgrounds = defaultdict(list)
    all_text_colors = defaultdict(list)
    container_report = {}

    for name, slug in SLUGS:
        url = f"{SITE}{slug}"
        try:
            resp = session.get(url, timeout=15)
            if resp.status_code != 200:
                print(f"  SKIP {name}: HTTP {resp.status_code}")
                continue

            html = resp.text

            colors = extract_colors_from_html(html)
            for h in colors['hex']:
                norm = normalize_hex(h)
                all_hex[norm].append(name)
            for r in colors['rgba']:
                all_rgba[r].append(name)

            gradients = extract_gradients(html)
            for gtype, gval in gradients:
                all_gradients[gval].append(name)

            backgrounds = extract_backgrounds(html)
            for bg in backgrounds:
                all_backgrounds[bg].append(name)

            text_colors = extract_text_colors(html)
            for tc in text_colors:
                all_text_colors[tc].append(name)

            nesting = extract_container_nesting(html)
            container_report[name] = nesting

            grad_count = len(gradients)
            hex_count = len(set(normalize_hex(h) for h in colors['hex']))
            print(f"  {name:30s}  {hex_count:3d} colors  {grad_count:2d} gradients  "
                  f"S:{nesting['sections']} C:{nesting['containers']} B:{nesting['blocks']} "
                  f"nested-S:{nesting['nested_sections']} nested-C:{nesting['nested_containers']}")

        except Exception as e:
            print(f"  ERROR {name}: {e}")

    # === REPORT ===
    print(f"\n{'=' * 90}")
    print("COLOR PALETTE (all hex colors used across site)")
    print(f"{'=' * 90}")
    sorted_hex = sorted(all_hex.items(), key=lambda x: len(x[1]), reverse=True)
    for color, pages in sorted_hex[:40]:
        page_list = ', '.join(sorted(set(pages)))[:70]
        print(f"  {color:10s} ({len(pages):2d} uses)  {page_list}")

    print(f"\n{'=' * 90}")
    print("RGBA COLORS")
    print(f"{'=' * 90}")
    sorted_rgba = sorted(all_rgba.items(), key=lambda x: len(x[1]), reverse=True)
    for color, pages in sorted_rgba[:20]:
        page_list = ', '.join(sorted(set(pages)))[:60]
        print(f"  {color:45s} ({len(pages):2d} uses)  {page_list}")

    print(f"\n{'=' * 90}")
    print("GRADIENTS")
    print(f"{'=' * 90}")
    sorted_gradients = sorted(all_gradients.items(), key=lambda x: len(x[1]), reverse=True)
    for grad, pages in sorted_gradients:
        page_list = ', '.join(sorted(set(pages)))[:60]
        short_grad = grad[:80] + ('...' if len(grad) > 80 else '')
        print(f"\n  {short_grad}")
        print(f"    Used on: {page_list} ({len(pages)} uses)")

    print(f"\n{'=' * 90}")
    print("CONTAINER NESTING ANALYSIS (potential layout issues)")
    print(f"{'=' * 90}")
    print(f"  {'Page':30s} {'Sections':>8s} {'Containers':>10s} {'Blocks':>6s} {'Nested-S':>8s} {'Nested-C':>8s} {'BG-Cont':>7s}")
    print(f"  {'-'*30} {'-'*8} {'-'*10} {'-'*6} {'-'*8} {'-'*8} {'-'*7}")
    for name, data in sorted(container_report.items()):
        flag = ""
        if data['nested_sections'] > 0:
            flag += " !! NESTED SECTIONS"
        if data['nested_containers'] > 1:
            flag += " !! DEEP NESTING"
        if data['bg_containers'] > 3:
            flag += " ! MANY BG LAYERS"
        print(f"  {name:30s} {data['sections']:8d} {data['containers']:10d} {data['blocks']:6d} "
              f"{data['nested_sections']:8d} {data['nested_containers']:8d} {data['bg_containers']:7d}{flag}")

    print(f"\n{'=' * 90}")
    print("SUMMARY")
    print(f"{'=' * 90}")
    print(f"  Unique hex colors:      {len(all_hex)}")
    print(f"  Unique rgba colors:     {len(all_rgba)}")
    print(f"  Unique gradients:       {len(all_gradients)}")
    print(f"  Pages with nested sections:    {sum(1 for d in container_report.values() if d['nested_sections'] > 0)}")
    print(f"  Pages with deep container nesting: {sum(1 for d in container_report.values() if d['nested_containers'] > 1)}")

    one_off_colors = [c for c, pages in all_hex.items() if len(pages) == 1]
    if one_off_colors:
        print(f"\n  ONE-OFF COLORS (used on only 1 page — potential inconsistencies):")
        for c in sorted(one_off_colors):
            print(f"    {c:10s} on {all_hex[c][0]}")

    print(f"\n{'=' * 90}")
    print("Audit complete.")
