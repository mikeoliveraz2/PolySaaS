"""Find the PolySaaS logo image block in the homepage."""
import requests, re, sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

BASE = "https://polysaas.online"
AUTH = ("mikeoliveraz@gmail.com", "vlop MpGU Os2V xDSI C6T7 2fAN")

r = requests.get(BASE + "/wp-json/wp/v2/pages/1313",
                 params={"context": "edit", "_fields": "content"},
                 auth=AUTH, timeout=45)
content = r.json()["content"]["raw"]

# Find all image blocks with PolySaaS in them
for m in re.finditer(r'(<!-- wp:image.*?<!-- /wp:image -->)', content, re.DOTALL):
    block = m.group(1)
    if 'polysaas' in block.lower() or 'logo' in block.lower():
        print(f"=== Image block at pos {m.start()} ===")
        print(block[:500])
        print("...\n")

# Also search for any <img> with polysaas or logo in src
for m in re.finditer(r'<img[^>]*(?:polysaas|logo)[^>]*>', content, re.IGNORECASE):
    print(f"=== img tag at pos {m.start()} ===")
    print(m.group(0)[:300])
    print()
