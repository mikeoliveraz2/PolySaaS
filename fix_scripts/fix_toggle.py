"""
Fix the dark mode toggle on all pages by wrapping it in <!-- wp:html --> blocks
to prevent WordPress wpautop from corrupting it.
"""
import requests, sys, re
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

AZURE = "https://azure-nightingale-589250.hostingersite.com"
s = requests.Session()
s.auth = ("mikeoliveraz@gmail.com", "vlop MpGU Os2V xDSI C6T7 2fAN")

# The clean toggle HTML
TOGGLE_HTML = '''<!-- wp:html -->
<button class="ps-theme-toggle" id="ps-dark-toggle" onclick="document.body.classList.toggle('dark-mode');localStorage.setItem('ps-dark-mode',document.body.classList.contains('dark-mode'))" aria-label="Toggle dark mode" style="position:fixed;top:80px;right:20px;z-index:9999;background:var(--ps-card-bg,#fff);border:2px solid var(--ps-border,#e5e7eb);border-radius:50%;width:40px;height:40px;cursor:pointer;font-size:18px;display:flex;align-items:center;justify-content:center;box-shadow:0 2px 8px rgba(0,0,0,0.1);transition:all 0.3s ease;">&#9790;</button>
<script>
if(localStorage.getItem('ps-dark-mode')==='true'){document.body.classList.add('dark-mode');}
</script>
<!-- /wp:html -->'''

r = s.get(f"{AZURE}/wp-json/wp/v2/pages", params={"per_page": 100, "_fields": "id,slug,content"})
pages = r.json()
print(f"Found {len(pages)} pages")

fixed = 0
for page in pages:
    pid = page['id']
    slug = page['slug']
    content = page['content']['rendered']
    
    if not content.strip():
        continue
    
    original = content
    
    # Remove any existing broken toggle buttons (wrapped in <p> tags by wpautop)
    # Pattern: <p><button class="ps-theme-toggle"...>...</button></p>
    content = re.sub(
        r'<p>\s*<button\s+class="ps-theme-toggle"[^>]*>.*?</button>\s*</p>',
        '', content, flags=re.DOTALL
    )
    
    # Also remove any bare toggle buttons not in wp:html
    content = re.sub(
        r'(?<!<!-- wp:html -->\n)<button\s+class="ps-theme-toggle"[^>]*>.*?</button>',
        '', content, flags=re.DOTALL
    )
    
    # Remove old toggle scripts that are bare (not in wp:html)
    content = re.sub(
        r"<p>\s*<script>\s*if\s*\(\s*localStorage\.getItem\('ps-dark-mode'\).*?</script>\s*</p>",
        '', content, flags=re.DOTALL
    )
    content = re.sub(
        r"(?<!<!-- wp:html -->\n)<script>\s*if\s*\(\s*localStorage\.getItem\('ps-dark-mode'\).*?</script>",
        '', content, flags=re.DOTALL
    )
    
    # Remove existing wp:html wrapped toggles to avoid duplicates
    content = re.sub(
        r'<!-- wp:html -->\s*<button\s+class="ps-theme-toggle".*?<!-- /wp:html -->',
        '', content, flags=re.DOTALL
    )
    
    # Clean up multiple blank lines
    content = re.sub(r'\n{3,}', '\n\n', content)
    
    # Now insert the clean toggle after the first <!-- wp:html --> CSS block
    # or at the beginning if no CSS block exists
    # Find the end of the first wp:html block (our CSS injection)
    first_wp_html_end = content.find('<!-- /wp:html -->')
    if first_wp_html_end >= 0:
        insert_pos = first_wp_html_end + len('<!-- /wp:html -->')
        content = content[:insert_pos] + '\n' + TOGGLE_HTML + '\n' + content[insert_pos:]
    else:
        # Prepend
        content = TOGGLE_HTML + '\n' + content
    
    if content != original:
        r2 = s.post(f"{AZURE}/wp-json/wp/v2/pages/{pid}", json={"content": content})
        if r2.status_code == 200:
            # Verify toggle is in rendered output
            rendered = r2.json()['content']['rendered']
            if 'ps-theme-toggle' in rendered and 'ps-dark-toggle' in rendered:
                print(f"  {slug}: toggle fixed and VERIFIED")
                fixed += 1
            else:
                print(f"  {slug}: toggle inserted but NOT verified in render")
        else:
            print(f"  {slug}: FAILED {r2.status_code}")

print(f"\nFixed toggle on {fixed} pages")
print("Done!")
