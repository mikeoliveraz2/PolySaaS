"""Extract CSS rules for Bricks elements from the rendered page."""
import requests
import re

SITE = "https://azure-nightingale-589250.hostingersite.com"

def extract_bricks_css(html):
    """Extract all CSS from style blocks and find rules for Bricks element IDs."""
    
    # Get all style blocks
    style_blocks = re.findall(r'<style[^>]*>(.*?)</style>', html, re.DOTALL)
    all_css = '\n'.join(style_blocks)
    
    # Find all Bricks element IDs used in the HTML
    bricks_ids = re.findall(r'id="(brxe-[a-z0-9]+)"', html)
    other_ids = re.findall(r'id="([a-z0-9]{6})"', html)  # short hash IDs Bricks uses
    all_ids = set(bricks_ids + other_ids)
    
    # Extract CSS rules that reference these IDs or Bricks classes
    results = {}
    
    for element_id in sorted(all_ids):
        # Look for #element_id rules
        patterns = [
            rf'#{element_id}\s*\{{([^}}]+)\}}',
            rf'#{element_id}[^{{]*\{{([^}}]+)\}}',
        ]
        rules = []
        for pattern in patterns:
            matches = re.findall(pattern, all_css)
            for m in matches:
                rules.append(m.strip())
        
        if rules:
            # Filter for interesting properties
            interesting = False
            for rule in rules:
                if any(prop in rule.lower() for prop in [
                    'background', 'gradient', 'border', 'padding', 'margin',
                    'max-width', 'width', 'color', 'box-shadow'
                ]):
                    interesting = True
            if interesting:
                results[element_id] = rules
    
    return results, all_css

def analyze_page(url, name):
    print(f"\n{'='*90}")
    print(f"CSS ANALYSIS: {name}")
    print(f"{'='*90}")
    
    resp = requests.get(url, timeout=15)
    html = resp.text
    
    rules, all_css = extract_bricks_css(html)
    
    # Find ALL gradient rules
    gradient_rules = re.findall(r'([#.][^{]+)\{([^}]*(?:gradient|background)[^}]*)\}', all_css)
    
    print(f"\n--- ELEMENTS WITH BACKGROUND/BORDER/GRADIENT STYLES ---")
    for element_id, element_rules in sorted(rules.items()):
        for rule in element_rules:
            props = [p.strip() for p in rule.split(';') if p.strip()]
            relevant = [p for p in props if any(k in p.lower() for k in [
                'background', 'gradient', 'border', 'padding', 'margin', 'width', 'box-shadow'
            ])]
            if relevant:
                print(f"\n  #{element_id}")
                for p in relevant:
                    print(f"    {p}")
    
    # Find section-level backgrounds
    print(f"\n--- SECTION/CONTAINER BACKGROUNDS IN CSS ---")
    for selector, body in gradient_rules:
        selector = selector.strip()
        if 'brxe' in selector or any(eid in selector for eid in rules.keys()):
            props = [p.strip() for p in body.split(';') if p.strip()]
            bg_props = [p for p in props if 'background' in p.lower() or 'gradient' in p.lower()]
            if bg_props:
                print(f"\n  {selector}")
                for p in bg_props:
                    print(f"    {p[:120]}")
    
    # Find any green/lime color references
    print(f"\n--- GREEN/LIME COLOR REFERENCES ---")
    green_patterns = [
        r'#(?:00ff59|59ff00|15ff00|0f0|00ff00|32cd32|7cfc00|adff2f|7fff00)',
        r'rgb\(\s*(?:0|21|50),\s*(?:255|250|200),\s*(?:0|50|89)\s*\)',
        r'(?:lime|green|limegreen)',
    ]
    for pattern in green_patterns:
        matches = list(re.finditer(pattern, all_css, re.IGNORECASE))
        for m in matches:
            start = max(0, m.start() - 100)
            end = min(len(all_css), m.end() + 50)
            context = all_css[start:end].replace('\n', ' ').strip()
            print(f"  Found: {m.group(0)}")
            print(f"  Context: ...{context}...")
    
    # Find border rules
    print(f"\n--- ALL BORDER RULES ---")
    border_matches = re.findall(r'([#.][^{]+)\{([^}]*border[^}]*)\}', all_css)
    for selector, body in border_matches:
        selector = selector.strip()
        if 'brxe' in selector:
            props = [p.strip() for p in body.split(';') if 'border' in p.lower()]
            if props:
                print(f"  {selector}")
                for p in props:
                    print(f"    {p[:120]}")

if __name__ == '__main__':
    analyze_page(f"{SITE}/", "HOME PAGE")
