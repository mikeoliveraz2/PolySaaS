"""Debug why header logo CSS isn't taking effect"""
import requests, re, sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

AZURE = "https://azure-nightingale-589250.hostingersite.com"
r = requests.get(AZURE)
html = r.text

# Find header section
header_start = html.find('<header')
header_end = html.find('</header>')
if header_start >= 0 and header_end >= 0:
    header_html = html[header_start:header_end+9]
    print("=== HEADER HTML (first 2000 chars) ===")
    print(header_html[:2000])
    print()

    # Find all img tags in header
    imgs = re.findall(r'<img[^>]*>', header_html)
    print(f"=== Images in header: {len(imgs)} ===")
    for i, img in enumerate(imgs):
        print(f"  IMG {i}: {img[:300]}")
    print()

    # Find the brand/logo link structure
    brand = re.findall(r'<a[^>]*class="[^"]*brand[^"]*"[^>]*>.*?</a>', header_html, re.DOTALL)
    print(f"=== Brand links: {len(brand)} ===")
    for b in brand:
        print(f"  {b[:300]}")
    print()
else:
    print("Header not found!")

# Now check ALL style blocks that mention logo/branding
styles = re.findall(r'<style[^>]*>(.*?)</style>', html, re.DOTALL)
print(f"\n=== Style blocks: {len(styles)} ===")
for i, s in enumerate(styles):
    if any(kw in s.lower() for kw in ['brand', 'logo', 'custom-logo', 'site-branding']):
        print(f"\n--- Style block {i} (logo-related) ---")
        # Print only the logo-related rules
        for line in s.split('\n'):
            if any(kw in line.lower() for kw in ['brand', 'logo', 'custom-logo', 'site-branding', 'max-width']):
                print(f"  {line.strip()}")

# Check if our CSS is in page content or in a theme style
print("\n\n=== Checking if our CSS is in entry-content ===")
entry_start = html.find('class="entry-content')
if entry_start >= 0:
    # Our CSS is injected into page content, which renders inside entry-content
    # Check if the style block is inside entry-content
    entry_section = html[entry_start:entry_start+5000]
    if 'Header Logo Size Override' in entry_section:
        print("  Our header logo CSS IS inside entry-content")
    else:
        # Check broader
        logo_css_pos = html.find('Header Logo Size Override')
        if logo_css_pos >= 0:
            print(f"  Our CSS at position {logo_css_pos}")
            print(f"  entry-content at position {entry_start}")
            if logo_css_pos > entry_start:
                print("  CSS is AFTER entry-content start")
            else:
                print("  CSS is BEFORE entry-content start")
        else:
            print("  Our header logo CSS NOT FOUND at all!")
else:
    print("  entry-content not found")

# Check for Kadence inline style that sets the logo size
print("\n=== Kadence inline logo styles ===")
kadence_logo_styles = re.findall(r'\.site-branding\s+a\.brand\s+img\s*\{[^}]*\}', html)
for s in kadence_logo_styles:
    print(f"  {s}")

# Also check for any max-width on the logo image itself
print("\n=== Inline styles on logo img ===")
logo_imgs = re.findall(r'<img[^>]*custom-logo[^>]*>', html)
for img in logo_imgs:
    print(f"  {img[:400]}")
