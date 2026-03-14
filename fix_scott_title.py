"""
Update Scott Chate's title to: VP Partner & Market Development, Corent Technology, Inc
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

# Find Scott's section and check current title
scott_idx = raw.find('Scott Chate')
if scott_idx < 0:
    print("Scott not found!")
    sys.exit(1)

# Show context around Scott
area = raw[scott_idx:scott_idx+400]
print(f"Scott area:\n{area[:400]}\n")

# Look for his current title/role text after his name
# It might be something generic - let's find and replace
# Find the paragraph or span after his name that contains his role
# Look for patterns like "VP" or "Advisor" or a generic role after the name
title_patterns = [
    # Try to find existing title text
    re.compile(r'(Scott Chate</[^>]+>\s*<[^>]*>)([^<]*)(</)', re.DOTALL),
    re.compile(r'(Scott Chate</h\d>\s*<p[^>]*>)([^<]*)(</p>)', re.DOTALL),
]

replaced = False
for pat in title_patterns:
    m = pat.search(raw[scott_idx-10:scott_idx+500])
    if m:
        old_title = m.group(2)
        print(f"Found title: '{old_title}'")
        new_title = "VP Partner &amp; Market Development, Corent Technology, Inc"
        if old_title.strip() != new_title:
            full_old = m.group(0)
            full_new = m.group(1) + new_title + m.group(3)
            raw = raw.replace(full_old, full_new, 1)
            replaced = True
            print(f"Replaced with: '{new_title}'")
        break

if not replaced:
    # Brute force: find whatever role text is near Scott
    # Search for common role containers
    after_scott = raw[scott_idx:scott_idx+500]
    print(f"After Scott (500 chars):\n{after_scott}")
    
    # Try replacing any existing role text
    # Look for a line like: Technology Advisor, or Board of Advisors, etc
    for old_text in ['Technology Advisor', 'Board of Advisors', 'Advisor', 'Board Member']:
        if old_text in after_scott:
            # Only replace the first occurrence after Scott
            pos = raw.find(old_text, scott_idx)
            if pos > 0 and pos < scott_idx + 500:
                raw = raw[:pos] + 'VP Partner &amp; Market Development, Corent Technology, Inc' + raw[pos+len(old_text):]
                replaced = True
                print(f"Replaced '{old_text}' with new title")
                break

if replaced:
    r = s.post(f"{AZURE}/wp-json/wp/v2/pages/{about['id']}", json={"content": raw})
    print(f"\nUpdate: {r.status_code}")
else:
    print("\nCould not find/replace title - manual check needed")
    print("Showing 600 chars around Scott:")
    print(raw[max(0,scott_idx-100):scott_idx+500])
