"""
Fix: the previous script removed Francis Uy instead of Stephen Bird.
1. Check current state
2. Find and remove the correct Stephen Bird card
3. Restore Francis Uy if missing
"""
import requests, re, sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

AZURE = "https://azure-nightingale-589250.hostingersite.com"
s = requests.Session()
s.auth = ("mikeoliveraz@gmail.com", "vlop MpGU Os2V xDSI C6T7 2fAN")

pages = s.get(f"{AZURE}/wp-json/wp/v2/pages", params={
    "slug": "about-us", "context": "edit", "_fields": "id,content"
}).json()
about = pages[0]
raw = about['content']['raw']

# Check who is still on the page
for name in ['Scott Chate', 'Feyzi Fatehi', 'Francis Uy', 'Stephen Bird', 'Mike Oliver', 'Ringo Rivera']:
    idx = raw.find(name)
    # Also check HTML comments
    comment_idx = raw.find(f'<!-- {name}')
    present = idx >= 0
    print(f"  {name}: {'FOUND at ' + str(idx) if present else 'MISSING'} (comment: {comment_idx})")

print()

# Find Stephen Bird's actual card
# The comment <!-- Stephen Bird --> marks the start of his section
stephen_comment = raw.find('<!-- Stephen Bird')
if stephen_comment >= 0:
    print(f"Stephen Bird comment at: {stephen_comment}")
    # The card div comes after the comment
    card_start = raw.find('<div style="flex:1 1 280px', stephen_comment)
    if card_start >= 0 and card_start < stephen_comment + 200:
        # Find end of card
        depth = 0
        i = card_start
        card_end = None
        while i < len(raw):
            if raw[i:i+4] == '<div':
                depth += 1
                i += 4
            elif raw[i:i+6] == '</div>':
                depth -= 1
                if depth == 0:
                    card_end = i + 6
                    break
                i += 6
            else:
                i += 1
        
        if card_end:
            stephen_card = raw[card_start:card_end]
            text = re.sub(r'<[^>]+>', ' ', stephen_card)
            text = re.sub(r'\s+', ' ', text).strip()
            print(f"Stephen's card ({len(stephen_card)} chars): {text[:200]}")
            
            # Also remove the comment line before it
            comment_line_start = raw.rfind('<p>', 0, card_start)
            if comment_line_start >= stephen_comment - 10:
                comment_line_end = raw.find('</p>', comment_line_start) + 4
                remove_start = comment_line_start
            else:
                remove_start = card_start
            
            print(f"Removing from {remove_start} to {card_end}")
            raw = raw[:remove_start] + raw[card_end:]
            print("Stephen Bird card removed")
    else:
        print(f"Card div not found near comment (next flex div at {card_start})")
else:
    print("Stephen Bird comment not found - may already be removed")

# Check if Francis Uy is still present
if 'Francis Uy' not in raw:
    print("\nFrancis Uy is MISSING - need to restore")
    # Insert Francis back before the remaining advisors' closing section
    # Find the position - should be after Feyzi and before Stephen (now removed)
    # or at the end of the advisors flex container
    
    FRANCIS_CARD = '''<div style="flex:1 1 280px;max-width:380px;background:#fff;border-radius:8px;padding:24px;box-shadow:0 2px 8px rgba(0,0,0,0.06);text-align:center">
<div style="width:100px;height:100px;border-radius:50%;background:#E5E7EB;margin:0 auto 12px auto;display:flex;align-items:center;justify-content:center;font-size:2rem;color:#6B7280">FU</div>
<h3 style="font-size:1.2rem;font-weight:600;margin-bottom:4px;color:var(--ps-primary,#001F3F)">Francis Uy</h3>
<p style="color:var(--ps-muted,#6B7280);font-size:0.85rem;margin-bottom:10px">Salesforce Cloud Administrator &mdash; Yudrio, Inc.</p>
<p style="color:var(--ps-text,#374151);font-size:0.9rem;line-height:1.5;margin-bottom:12px">Salesforce platform specialist with expertise in cloud administration and IT operations. Known for deep technical knowledge, cross-team collaboration, and a positive, solutions-driven approach to enterprise IT challenges.</p>
<a href="https://www.linkedin.com/in/francisuy/" style="display:inline-block;margin-top:8px;color:#2563EB;text-decoration:none;font-size:0.85rem;font-weight:500">LinkedIn &rarr;</a>
</div>'''
    
    # Find the last advisor card position (after Feyzi)
    feyzi_idx = raw.find('Feyzi Fatehi')
    if feyzi_idx > 0:
        # Find end of Feyzi's card
        feyzi_card_start = raw.rfind('<div style="flex:1 1 280px', 0, feyzi_idx)
        depth = 0
        i = feyzi_card_start
        feyzi_card_end = None
        while i < len(raw):
            if raw[i:i+4] == '<div':
                depth += 1
                i += 4
            elif raw[i:i+6] == '</div>':
                depth -= 1
                if depth == 0:
                    feyzi_card_end = i + 6
                    break
                i += 6
            else:
                i += 1
        
        if feyzi_card_end:
            raw = raw[:feyzi_card_end] + "\n" + FRANCIS_CARD + "\n" + raw[feyzi_card_end:]
            print("Francis Uy restored after Feyzi")
else:
    print("\nFrancis Uy is still present - good")

# Final check
print("\nFinal check:")
for name in ['Scott Chate', 'Feyzi Fatehi', 'Francis Uy', 'Stephen Bird']:
    present = name in raw
    print(f"  {name}: {'PRESENT' if present else 'REMOVED'}")

r = s.post(f"{AZURE}/wp-json/wp/v2/pages/{about['id']}", json={"content": raw})
print(f"\nUpdate: {r.status_code}")
