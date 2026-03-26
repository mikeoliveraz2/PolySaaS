"""Restructure feature blocks: single column, image above text, line separators."""
import requests, re, sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

BASE = "https://azure-nightingale-589250.hostingersite.com"
AUTH = ("mikeoliveraz@gmail.com", "vlop MpGU Os2V xDSI C6T7 2fAN")

r = requests.get(f"{BASE}/wp-json/wp/v2/pages/1313?context=edit&_fields=content",
                 auth=AUTH, timeout=30)
content = r.json()['content']['raw']

# Find the features wrapper
wrapper_start = content.find('<div class="wp-block-group" style="max-width:960px;margin:0 auto')
if wrapper_start < 0:
    print("Features wrapper not found!")
    # Check what's there
    pf = content.find('platform-features')
    if pf > 0:
        print(f"Context around platform-features:")
        print(content[max(0,pf-500):pf+200])
    sys.exit(1)

# Find the end of the wrapper
# Count div nesting to find the matching closing div
pos = wrapper_start
depth = 0
wrapper_end = -1
while pos < len(content):
    if content[pos:pos+4] == '<div':
        depth += 1
    elif content[pos:pos+6] == '</div>':
        depth -= 1
        if depth == 0:
            wrapper_end = pos + 6
            break
    pos += 1

if wrapper_end < 0:
    print("Could not find end of features wrapper!")
    sys.exit(1)

features_section = content[wrapper_start:wrapper_end]
print(f"Features section length: {len(features_section)} chars")

# Extract each feature's data: title, description, link, image
# Each feature is a wp-block-columns with two wp-block-column children
features = []

# Parse feature blocks - find all wp-block-columns within the section
col_blocks = re.finditer(r'<!-- wp:columns.*?-->.*?<!-- /wp:columns -->', features_section, re.DOTALL)

for match in col_blocks:
    block = match.group(0)
    
    # Extract title (h3)
    title_match = re.search(r'<h3[^>]*>(.*?)</h3>', block, re.DOTALL)
    title = title_match.group(1).strip() if title_match else ""
    # Clean any spans/styles from title
    title = re.sub(r'<[^>]+>', '', title).strip()
    
    # Extract description (p tags, skip empty ones)
    desc_matches = re.findall(r'<p[^>]*>(.*?)</p>', block, re.DOTALL)
    desc = ""
    for d in desc_matches:
        clean = re.sub(r'<[^>]+>', '', d).strip()
        if clean and 'Learn More' not in clean:
            desc = clean
            break
    
    # Extract Learn More link
    link_match = re.search(r'<a[^>]*href="([^"]*)"[^>]*>Learn More', block)
    link_url = link_match.group(1) if link_match else ""
    
    # Extract image
    img_match = re.search(r'<img[^>]+src="([^"]+)"[^>]*/?>|<figure[^>]*>.*?<img[^>]+src="([^"]+)"', block, re.DOTALL)
    img_url = ""
    if img_match:
        img_url = img_match.group(1) or img_match.group(2)
    
    # Get full img tag for alt text etc
    full_img = re.search(r'<img[^>]+/?>', block)
    img_tag = full_img.group(0) if full_img else ""
    
    # Get figure block if exists
    figure_match = re.search(r'(<!-- wp:image.*?-->.*?<!-- /wp:image -->)', block, re.DOTALL)
    figure_block = figure_match.group(1) if figure_match else ""
    
    if title:
        features.append({
            'title': title,
            'desc': desc,
            'link_url': link_url,
            'img_url': img_url,
            'img_tag': img_tag,
            'figure_block': figure_block,
        })
        print(f"  Feature: {title} | img: {'yes' if img_url else 'no'} | link: {link_url[:30] if link_url else 'none'}")

print(f"\nFound {len(features)} features")

# Build new single-column layout
new_blocks = []

# Platform Features heading (keep existing)
heading = '<!-- wp:heading {"textAlign":"center","className":"has-primary-color has-text-color","style":{"typography":{"fontSize":"1.6rem","fontWeight":"600"},"spacing":{"margin":{"bottom":"18px"}}}} -->\n'
heading += '<h2 class="wp-block-heading has-text-align-center has-primary-color has-text-color" style="margin-bottom:18px;font-size:1.6rem;font-weight:600" id="platform-features">Platform Features</h2>\n'
heading += '<!-- /wp:heading -->'
new_blocks.append(heading)

for i, feat in enumerate(features):
    # Add separator between features (not before first)
    if i > 0:
        new_blocks.append('<!-- wp:separator {"className":"is-style-wide","style":{"color":{"background":"#334155"}}} -->\n<hr class="wp-block-separator has-text-color has-alpha-channel-opacity has-background is-style-wide" style="background-color:#334155;color:#334155"/>\n<!-- /wp:separator -->')
    
    # Image (if exists) - centered
    if feat['figure_block']:
        # Use existing figure block
        new_blocks.append(feat['figure_block'])
    elif feat['img_tag']:
        img_block = f'<!-- wp:image {{"align":"center","sizeSlug":"large"}} -->\n<figure class="wp-block-image aligncenter size-large">{feat["img_tag"]}</figure>\n<!-- /wp:image -->'
        new_blocks.append(img_block)
    
    # Title - centered
    title_block = f'<!-- wp:heading {{"textAlign":"center","level":3,"style":{{"color":{{"text":"#0F766E"}},"typography":{{"fontSize":"1.3rem","fontWeight":"600"}},"spacing":{{"margin":{{"top":"16px","bottom":"8px"}}}}}}}} -->\n'
    title_block += f'<h3 class="wp-block-heading has-text-align-center" style="color:#0F766E;font-size:1.3rem;font-weight:600;margin-top:16px;margin-bottom:8px">{feat["title"]}</h3>\n'
    title_block += '<!-- /wp:heading -->'
    new_blocks.append(title_block)
    
    # Description - centered
    if feat['desc']:
        desc_block = f'<!-- wp:paragraph {{"align":"center","style":{{"typography":{{"fontSize":"0.9rem"}},"spacing":{{"margin":{{"bottom":"10px"}}}}}}}} -->\n'
        desc_block += f'<p class="has-text-align-center" style="font-size:0.9rem;margin-bottom:10px">{feat["desc"]}</p>\n'
        desc_block += '<!-- /wp:paragraph -->'
        new_blocks.append(desc_block)
    
    # Learn More link - centered
    if feat['link_url']:
        link_block = f'<!-- wp:paragraph {{"align":"center","style":{{"typography":{{"fontSize":"0.85rem"}},"spacing":{{"margin":{{"bottom":"20px"}}}}}}}} -->\n'
        link_block += f'<p class="has-text-align-center" style="font-size:0.85rem;margin-bottom:20px"><a href="{feat["link_url"]}" style="color:#0F766E;text-decoration:none;font-weight:500">Learn More →</a></p>\n'
        link_block += '<!-- /wp:paragraph -->'
        new_blocks.append(link_block)

# Build new features section
new_features = '<div class="wp-block-group" style="max-width:960px;margin:0 auto;padding-top:10px;padding-bottom:12px">\n<div class="wp-block-group__inner-container">\n'
new_features += '\n\n'.join(new_blocks)
new_features += '\n</div>\n</div>'

# Replace old features section
new_content = content[:wrapper_start] + new_features + content[wrapper_end:]

r2 = requests.post(
    f"{BASE}/wp-json/wp/v2/pages/1313",
    auth=AUTH,
    json={"content": new_content},
    timeout=30
)
print(f"\nUpdate: {r2.status_code}")
if r2.status_code == 200:
    print("SUCCESS - Features restructured: single column, image above text, line separators")
else:
    print(f"Error: {r2.text[:500]}")
