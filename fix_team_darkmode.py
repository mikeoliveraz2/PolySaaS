"""Fix team member cards on About Us page for dark mode compatibility."""
import requests

AZURE = "https://azure-nightingale-589250.hostingersite.com"
s = requests.Session()
s.auth = ("mikeoliveraz@gmail.com", "vlop MpGU Os2V xDSI C6T7 2fAN")

r = s.get(f"{AZURE}/wp-json/wp/v2/pages?slug=about-us&context=edit")
page = r.json()[0]
pid = page['id']
content = page['content']['raw']
print(f"About Us page id={pid}, length={len(content)}")

# Replace hardcoded card styles with CSS variable versions
replacements = [
    # Card backgrounds
    ('background:#fff;border-radius:8px;padding:24px;box-shadow:0 2px 8px rgba(0,0,0,0.06);text-align:center',
     'background:var(--ps-card-bg,#fff);border-radius:8px;padding:24px;box-shadow:0 2px 8px var(--ps-card-shadow,rgba(0,0,0,0.06));text-align:center'),
    # Name headings (h3)
    ('font-size:1.2rem;font-weight:600;margin-bottom:4px;color:#1F2937',
     'font-size:1.2rem;font-weight:600;margin-bottom:4px;color:var(--ps-text,#1F2937)'),
    # Bio text
    ('font-size:0.9rem;line-height:1.6;color:#4B5563',
     'font-size:0.9rem;line-height:1.6;color:var(--ps-text-muted,#4B5563)'),
    # Placeholder circle backgrounds (for FF, FU initials)
    ('border-radius:50%;background:#E5E7EB;margin:0 auto 12px auto;display:flex;align-items:center;justify-content:center;font-size:2rem;color:#6B7280',
     'border-radius:50%;background:var(--ps-icon-bg,#E5E7EB);margin:0 auto 12px auto;display:flex;align-items:center;justify-content:center;font-size:2rem;color:var(--ps-text-muted,#6B7280)'),
]

count = 0
for old, new in replacements:
    occurrences = content.count(old)
    if occurrences > 0:
        content = content.replace(old, new)
        count += occurrences
        print(f"Replaced {occurrences}x: {old[:50]}...")

print(f"\nTotal replacements: {count}")

if count > 0:
    r2 = s.post(f"{AZURE}/wp-json/wp/v2/pages/{pid}", json={"content": content})
    print(f"Update: {r2.status_code}")
    if r2.status_code == 200:
        print("Done — team cards now use CSS variables for dark mode.")
    else:
        print(f"Error: {r2.text[:300]}")
else:
    print("No replacements needed or patterns not found.")
