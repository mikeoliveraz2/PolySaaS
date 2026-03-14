"""
Quality Control Audit: Check every page for consistent:
1. Header logo CSS (60px override)
2. Dark mode CSS (:root vars + body.dark-mode rules)
3. Toggle button presence + correct script
4. Top padding reduction CSS
5. Menubar color CSS (light grey / dark blue)
6. Nav font color in dark mode
"""
import requests, re, sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

AZURE = "https://azure-nightingale-589250.hostingersite.com"
s = requests.Session()
s.auth = ("mikeoliveraz@gmail.com", "vlop MpGU Os2V xDSI C6T7 2fAN")

pages = s.get(f"{AZURE}/wp-json/wp/v2/pages", params={
    "per_page": 100, "context": "edit", "_fields": "id,slug,title,content,status"
}).json()

published = [p for p in pages if p.get('status') == 'publish']
print(f"Total pages: {len(pages)}, Published: {len(published)}\n")

CHECKS = [
    ("Logo CSS (60px)", lambda r: 'max-width: 60px' in r or 'max-width:60px' in r),
    ("Root vars (--ps-primary)", lambda r: '--ps-primary' in r),
    ("Dark mode CSS (body.dark-mode)", lambda r: 'body.dark-mode' in r),
    ("Toggle button (ps-dark-toggle)", lambda r: 'ps-dark-toggle' in r),
    ("Toggle script (localStorage)", lambda r: "localStorage.getItem('ps-dark-mode')" in r),
    ("Toggle hover tooltip (title=)", lambda r: 'Switch to dark mode' in r or 'Switch to light mode' in r),
    ("Top padding CSS (entry-hero)", lambda r: '.entry-hero' in r and 'min-height' in r),
    ("Menubar light grey (#F1F5F9)", lambda r: '#F1F5F9' in r or '#f1f5f9' in r),
    ("Menubar dark blue (#1E293B)", lambda r: '#1E293B' in r or '#1e293b' in r),
    ("Nav dark mode font", lambda r: 'header-navigation' in r and 'dark-mode' in r),
    ("Content present (>200 chars text)", lambda r: len(re.sub(r'<[^>]+>', '', re.sub(r'<style[^>]*>.*?</style>', '', r, flags=re.DOTALL)).strip()) > 200),
]

issues = []
results = []

for p in published:
    title = p['title']['raw'] if isinstance(p['title'], dict) else p['title']
    raw = p['content']['raw']
    slug = p['slug']
    
    row = {"slug": slug, "title": title, "id": p['id']}
    row_issues = []
    
    for check_name, check_fn in CHECKS:
        passed = check_fn(raw)
        row[check_name] = passed
        if not passed:
            row_issues.append(check_name)
    
    results.append(row)
    if row_issues:
        issues.append((slug, title, row_issues))

# Print results table
print(f"{'SLUG':<28} {'LOGO':^5} {'VARS':^5} {'DARK':^5} {'TOGL':^5} {'SCPT':^5} {'HOVR':^5} {'PAD':^5} {'LTGR':^5} {'DKBL':^5} {'NAV':^5} {'CONT':^5}")
print("-" * 110)

for r in sorted(results, key=lambda x: x['slug']):
    cols = []
    for check_name, _ in CHECKS:
        cols.append("OK" if r[check_name] else "MISS")
    print(f"{r['slug']:<28} {cols[0]:^5} {cols[1]:^5} {cols[2]:^5} {cols[3]:^5} {cols[4]:^5} {cols[5]:^5} {cols[6]:^5} {cols[7]:^5} {cols[8]:^5} {cols[9]:^5} {cols[10]:^5}")

# Summary
print(f"\n{'='*60}")
print(f"SUMMARY: {len(published)} published pages checked")
ok_count = len([r for r in results if all(r[c] for c, _ in CHECKS)])
print(f"  Fully consistent: {ok_count}")
print(f"  With issues: {len(issues)}")

if issues:
    print(f"\n{'='*60}")
    print("PAGES WITH ISSUES:")
    for slug, title, issue_list in sorted(issues, key=lambda x: x[0]):
        print(f"\n  {slug} ({title}):")
        for iss in issue_list:
            print(f"    - MISSING: {iss}")
