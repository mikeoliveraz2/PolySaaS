"""
Flip Apps As Peers row: text on left, image on right.
"""
import requests, re, sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

AZURE = "https://azure-nightingale-589250.hostingersite.com"
s = requests.Session()
s.auth = ("mikeoliveraz@gmail.com", "vlop MpGU Os2V xDSI C6T7 2fAN")

pages = s.get(f"{AZURE}/wp-json/wp/v2/pages", params={
    "slug": "home", "context": "edit", "_fields": "id,content"
}).json()
home = pages[0]
raw = home['content']['raw']

# The Apps As Peers row is a wp-block-columns with background #F3F4F6
# It has two wp-block-column children: [image] [text]
# We need to swap to: [text] [image]

# Find the columns container for Apps As Peers
# It's the wp-block-columns right before "Apps As Peers" heading
aap_idx = raw.find('Apps As Peers</h3>')
row_start = raw.rfind('<div class="wp-block-columns', 0, aap_idx)

# Find the end of this columns block - it ends before the next wp-block-columns
next_row = raw.find('<div class="wp-block-columns', row_start + 10)
# The closing </div> for the columns block is right before the next row
# Count div depth from row_start to find the closing </div>
depth = 0
i = row_start
row_end = None
while i < len(raw):
    if raw[i:i+30].startswith('<div class="wp-block-columns') and i == row_start:
        depth += 1
        i += 30
    elif raw[i:i+4] == '<div':
        depth += 1
        i += 4
    elif raw[i:i+6] == '</div>':
        depth -= 1
        if depth == 0:
            row_end = i + 6
            break
        i += 6
    else:
        i += 1

old_row = raw[row_start:row_end]
print(f"Apps As Peers row: {len(old_row)} chars")

# Extract the two columns
# Column pattern: <div class="wp-block-column ...">...</div>
col_starts = []
for m in re.finditer(r'<div class="wp-block-column ', old_row):
    col_starts.append(m.start())

print(f"Column starts at offsets: {col_starts}")

if len(col_starts) >= 2:
    # Extract column 1 (image) and column 2 (text)
    # Column 1: from col_starts[0] to col_starts[1]
    # Column 2: from col_starts[1] to end of row (before final </div>)
    
    # Parse column 1
    depth = 0
    i = col_starts[0]
    col1_end = None
    while i < len(old_row):
        if old_row[i:i+4] == '<div':
            depth += 1
            i += 4
        elif old_row[i:i+6] == '</div>':
            depth -= 1
            if depth == 0:
                col1_end = i + 6
                break
            i += 6
        else:
            i += 1
    
    col1 = old_row[col_starts[0]:col1_end]
    
    # Parse column 2
    depth = 0
    i = col_starts[1]
    col2_end = None
    while i < len(old_row):
        if old_row[i:i+4] == '<div':
            depth += 1
            i += 4
        elif old_row[i:i+6] == '</div>':
            depth -= 1
            if depth == 0:
                col2_end = i + 6
                break
            i += 6
        else:
            i += 1
    
    col2 = old_row[col_starts[1]:col2_end]
    
    # Verify: col1 should have the image, col2 should have the text
    col1_has_img = 'au-as-oers.png' in col1 or '<img' in col1
    col2_has_text = 'Apps As Peers</h3>' in col2
    print(f"Col1 has image: {col1_has_img}, Col2 has text: {col2_has_text}")
    
    if col1_has_img and col2_has_text:
        # Build new row with columns swapped: text first, then image
        row_opening = old_row[:col_starts[0]]
        row_closing = old_row[col2_end:]
        # Get any separator between cols
        between = old_row[col1_end:col_starts[1]]
        
        new_row = row_opening + col2 + between + col1 + row_closing
        new_raw = raw[:row_start] + new_row + raw[row_end:]
        
        r = s.post(f"{AZURE}/wp-json/wp/v2/pages/{home['id']}", json={"content": new_raw})
        print(f"\nUpdate: {r.status_code}")
        if r.status_code == 200:
            print("Apps As Peers flipped: text on left, image on right")
    else:
        print("Column content doesn't match expected - aborting")
else:
    print(f"Expected 2 columns, found {len(col_starts)}")
