"""Deep inspection of Bricks container nesting on problematic pages."""
import requests
import re
from html.parser import HTMLParser

SITE = "https://azure-nightingale-589250.hostingersite.com"

class BricksNestingInspector(HTMLParser):
    """Parse HTML and track Bricks element nesting with their styles."""
    
    def __init__(self):
        super().__init__()
        self.stack = []
        self.elements = []
        self.depth = 0
        self.in_main = False
        self.bricks_depth = 0
    
    def handle_starttag(self, tag, attrs):
        attrs_dict = dict(attrs)
        classes = attrs_dict.get('class', '')
        style = attrs_dict.get('style', '')
        element_id = attrs_dict.get('id', '')
        data_id = attrs_dict.get('data-script-id', '') or attrs_dict.get('data-element-id', '')
        
        if tag == 'main':
            self.in_main = True
        
        is_bricks = any(c.startswith('brxe-') for c in classes.split())
        
        if self.in_main and is_bricks:
            bricks_type = ''
            for c in classes.split():
                if c.startswith('brxe-'):
                    bricks_type = c.replace('brxe-', '')
                    break
            
            bg_props = {}
            if style:
                for prop in ['background', 'background-color', 'background-image', 
                             'border', 'border-left', 'border-right', 'border-top', 'border-bottom',
                             'padding', 'margin', 'max-width', 'width']:
                    match = re.search(rf'{prop}\s*:\s*([^;]+)', style)
                    if match:
                        bg_props[prop] = match.group(1).strip()
            
            self.elements.append({
                'tag': tag,
                'type': bricks_type,
                'classes': classes,
                'id': element_id,
                'data_id': data_id,
                'style_props': bg_props,
                'full_style': style[:200] if style else '',
                'depth': self.bricks_depth,
            })
            self.bricks_depth += 1
        
        self.stack.append((tag, is_bricks))
        self.depth += 1
    
    def handle_endtag(self, tag):
        if tag == 'main':
            self.in_main = False
        while self.stack:
            stag, was_bricks = self.stack.pop()
            self.depth -= 1
            if was_bricks:
                self.bricks_depth -= 1
            if stag == tag:
                break

def inspect_page(url, name):
    print(f"\n{'='*90}")
    print(f"INSPECTING: {name}")
    print(f"URL: {url}")
    print(f"{'='*90}")
    
    resp = requests.get(url, timeout=15)
    html = resp.text
    
    inspector = BricksNestingInspector()
    inspector.feed(html)
    
    print(f"\nTotal Bricks elements found: {len(inspector.elements)}")
    
    # Show full nesting tree
    print(f"\n--- BRICKS ELEMENT TREE ---")
    for el in inspector.elements:
        indent = "  " * el['depth']
        type_str = f"[{el['type'].upper()}]"
        id_str = f" id={el['id']}" if el['id'] else ''
        
        # Flag problematic elements
        flags = []
        props = el['style_props']
        if any(k.startswith('border') for k in props):
            flags.append(f"BORDER: {', '.join(f'{k}:{v}' for k,v in props.items() if k.startswith('border'))}")
        if any(k.startswith('background') for k in props):
            flags.append(f"BG: {', '.join(f'{k}:{v}' for k,v in props.items() if k.startswith('background'))}")
        if 'padding' in props:
            flags.append(f"PAD: {props['padding']}")
        if 'margin' in props:
            flags.append(f"MAR: {props['margin']}")
        if 'max-width' in props:
            flags.append(f"MAX-W: {props['max-width']}")
        if 'width' in props:
            flags.append(f"W: {props['width']}")
        
        flag_str = f" >>> {' | '.join(flags)}" if flags else ''
        print(f"{indent}{type_str:20s}{id_str}{flag_str}")
    
    # Identify specific problems
    print(f"\n--- PROBLEM ANALYSIS ---")
    
    # Find elements with borders
    bordered = [el for el in inspector.elements if any(k.startswith('border') for k in el['style_props'])]
    if bordered:
        print(f"\nElements with BORDERS ({len(bordered)}):")
        for el in bordered:
            border_props = {k:v for k,v in el['style_props'].items() if k.startswith('border')}
            print(f"  [{el['type']}] id={el['id']} depth={el['depth']}")
            for k,v in border_props.items():
                print(f"    {k}: {v}")
    
    # Find elements with backgrounds at depth > 0
    bg_nested = [el for el in inspector.elements 
                 if el['depth'] > 0 and any(k.startswith('background') for k in el['style_props'])]
    if bg_nested:
        print(f"\nNested elements with BACKGROUNDS ({len(bg_nested)}):")
        for el in bg_nested:
            bg_props = {k:v for k,v in el['style_props'].items() if k.startswith('background')}
            print(f"  [{el['type']}] id={el['id']} depth={el['depth']}")
            for k,v in bg_props.items():
                val = v[:100] + ('...' if len(v) > 100 else '')
                print(f"    {k}: {val}")
    
    # Find deep nesting chains
    max_depth = max(el['depth'] for el in inspector.elements) if inspector.elements else 0
    if max_depth > 2:
        print(f"\nDEEP NESTING (max depth: {max_depth}):")
        for el in inspector.elements:
            if el['depth'] >= 3:
                print(f"  depth={el['depth']} [{el['type']}] id={el['id']}")
    
    # Find sections with background properties
    sections_with_bg = [el for el in inspector.elements 
                        if el['type'] == 'section' and el['style_props']]
    if sections_with_bg:
        print(f"\nSECTIONS with inline styles ({len(sections_with_bg)}):")
        for el in sections_with_bg:
            print(f"  [{el['type']}] id={el['id']}")
            for k,v in el['style_props'].items():
                val = v[:100] + ('...' if len(v) > 100 else '')
                print(f"    {k}: {val}")

    # Also extract all CSS classes used on Bricks elements that suggest styling
    print(f"\n--- ALL BRICKS ELEMENT IDs AND CLASSES ---")
    for el in inspector.elements:
        if el['type'] in ('section', 'container', 'block'):
            classes_short = ' '.join(c for c in el['classes'].split() if not c.startswith('brxe-') and not c.startswith('css-'))
            style_summary = el['full_style'][:120] if el['full_style'] else '(no inline style)'
            print(f"  depth={el['depth']} [{el['type']:12s}] id={el['id']:30s} classes={classes_short[:50]}")
            if el['full_style']:
                print(f"         style: {style_summary}")

if __name__ == '__main__':
    print("BRICKS CONTAINER NESTING DEEP INSPECTION")
    print("Examining problematic pages for exact elements causing issues")
    
    inspect_page(f"{SITE}/", "HOME PAGE")
    inspect_page(f"{SITE}/pricing/", "PRICING PAGE")
