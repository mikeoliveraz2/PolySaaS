"""Extract HTML context around problematic Bricks elements from the live page."""
import requests
import re

SITE = "https://azure-nightingale-589250.hostingersite.com"

PROBLEM_ELEMENTS = [
    ('brxe-9d3229', 'GREEN STRIPE container - linear-gradient(90deg, #15ff00, #15ff00)'),
    ('brxe-spdnfe', 'LIME GREEN button - background-color: #59ff00'),
    ('brxe-108a27', 'MINT GREEN button - background-color: #6bff9f'),
    ('brxe-5a8e5d', 'SPLIT BG container - linear-gradient(90deg, #e0e0e0, #81d4fa)'),
    ('brxe-a41c97', 'SPLIT BG container - linear-gradient(270deg, #9e9e9e, #81d4fa)'),
    ('brxe-d09dd8', 'YELLOW-GREY gradient - linear-gradient(0deg, #ffeb3b, #9e9e9e)'),
    ('brxe-c84666', 'NESTED BG container - background-color: #f5f9fa'),
]

def get_element_context(html, element_id, context_chars=500):
    """Find element in HTML and return surrounding context with parent/child info."""
    
    # Find the element tag
    pattern = rf'<[^>]*id="{element_id}"[^>]*>'
    match = re.search(pattern, html)
    if not match:
        return None, None, None
    
    start = match.start()
    end = match.end()
    
    # Get surrounding context
    ctx_start = max(0, start - context_chars)
    ctx_end = min(len(html), end + context_chars)
    
    before = html[ctx_start:start]
    element_tag = html[start:end]
    after = html[end:ctx_end]
    
    # Find parent elements (look backwards for unclosed tags)
    parents = []
    search_back = html[max(0, start-2000):start]
    parent_tags = re.findall(r'<(section|div)[^>]*(?:id="([^"]*)")?[^>]*class="([^"]*)"[^>]*>', search_back)
    for tag, pid, pclass in reversed(parent_tags[-5:]):
        if 'brxe-' in pclass:
            bricks_type = ''
            for c in pclass.split():
                if c.startswith('brxe-'):
                    bricks_type = c
                    break
            parents.append(f'{tag}#{pid} .{bricks_type}')
    
    # Find immediate children
    children = []
    child_search = after[:1000]
    child_tags = re.findall(r'<[^/][^>]*(?:id="([^"]*)")?[^>]*class="([^"]*)"[^>]*>', child_search)
    for cid, cclass in child_tags[:5]:
        if 'brxe-' in cclass:
            bricks_type = ''
            for c in cclass.split():
                if c.startswith('brxe-'):
                    bricks_type = c
                    break
            children.append(f'#{cid} .{bricks_type}')
    
    # Extract visible text near this element
    text_after = re.sub(r'<[^>]+>', ' ', after[:500])
    text_after = re.sub(r'\s+', ' ', text_after).strip()[:200]
    
    return element_tag, parents, children, text_after

resp = requests.get(f"{SITE}/", timeout=15)
html = resp.text

print("=" * 90)
print("PROBLEM ELEMENT CONTEXT — HOME PAGE")
print("=" * 90)

for element_id, description in PROBLEM_ELEMENTS:
    print(f"\n{'─' * 90}")
    print(f"ELEMENT: #{element_id}")
    print(f"ISSUE:   {description}")
    print(f"{'─' * 90}")
    
    result = get_element_context(html, element_id)
    if result[0] is None:
        print("  NOT FOUND in page HTML")
        continue
    
    element_tag, parents, children, nearby_text = result
    
    # Clean up the tag for display
    tag_display = element_tag.replace('>', '>\n         ')
    print(f"\n  TAG:     {element_tag[:200]}")
    
    if parents:
        print(f"\n  PARENT CHAIN (innermost first):")
        for i, p in enumerate(parents):
            indent = "    " + "  " * i
            print(f"{indent}└─ {p}")
    
    if children:
        print(f"\n  CHILDREN:")
        for c in children:
            print(f"    ├─ {c}")
    
    if nearby_text:
        print(f"\n  VISIBLE TEXT NEARBY:")
        print(f"    \"{nearby_text[:150]}\"")

# Also show the full section structure
print(f"\n{'=' * 90}")
print("FULL PAGE SECTION MAP (sections and their direct containers)")
print("=" * 90)

sections = re.finditer(r'<section[^>]*id="([^"]*)"[^>]*class="([^"]*)"[^>]*>', html)
for match in sections:
    sid = match.group(1)
    sclass = match.group(2)
    
    # Get content after this section start
    after = html[match.end():match.end()+3000]
    
    # Find containers directly inside this section
    containers = re.findall(r'<div[^>]*id="([^"]*)"[^>]*class="[^"]*brxe-container[^"]*"[^>]*>', after)
    
    # Find headings for context
    headings = re.findall(r'<h[1-6][^>]*>(.*?)</h[1-6]>', after[:2000])
    headings = [re.sub(r'<[^>]+>', '', h).strip() for h in headings[:3]]
    
    bricks_type = ''
    for c in sclass.split():
        if c.startswith('brxe-'):
            bricks_type = c
            break
    
    print(f"\n  SECTION #{sid} ({bricks_type})")
    if headings:
        print(f"    Content: {' | '.join(headings[:3])}")
    for cid in containers[:6]:
        print(f"    └─ container #{cid}")
