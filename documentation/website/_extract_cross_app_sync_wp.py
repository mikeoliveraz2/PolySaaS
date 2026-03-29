"""One-off: pull cross-app-sync page from WP REST and list images (UTF-8)."""
import json
import re
import urllib.request

OUT = __file__.replace("_extract_cross_app_sync_wp.py", "_cross_app_sync_extract.txt")

url = "https://polysaas.online/wp-json/wp/v2/pages?slug=cross-app-sync"
with urllib.request.urlopen(url, timeout=30) as r:
    data = json.load(r)
p = data[0]
raw = p["content"]["rendered"]
imgs = re.findall(r"<img[^>]+>", raw, re.I)
lines = [
    f"modified_gmt={p.get('modified_gmt')}",
    f"id={p.get('id')}",
    f"img_count={len(imgs)}",
    "",
]
for i, m in enumerate(imgs, 1):
    sm = re.search(r'src=["\']([^"\']+)["\']', m, re.I)
    altm = re.search(r'alt=["\']([^"\']*)["\']', m, re.I)
    alt = altm.group(1) if altm else ""
    src = sm.group(1) if sm else ""
    lines.append(f"{i}. alt={alt!r}")
    lines.append(f"   {src}")
    lines.append("")

with open(OUT, "w", encoding="utf-8") as f:
    f.write("\n".join(lines))
print("Wrote", OUT)
