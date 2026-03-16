import requests, re
AZURE = "https://azure-nightingale-589250.hostingersite.com"
s = requests.Session()
s.auth = ("mikeoliveraz@gmail.com", "vlop MpGU Os2V xDSI C6T7 2fAN")

r = s.get(f"{AZURE}/wp-json/wp/v2/pages?slug=dynamic-orchestration&context=edit")
page = r.json()[0]
content = page['content']['raw']
pid = page['id']

imgs = list(re.finditer(r'<img[^>]+>', content))
print(f"Found {len(imgs)} images on Dynamic Orchestration (id={pid})")
for i, m in enumerate(imgs):
    tag = m.group()
    src = re.search(r'src="([^"]+)"', tag)
    alt = re.search(r'alt="([^"]+)"', tag)
    src_val = src.group(1) if src else "no src"
    alt_val = alt.group(1) if alt else "no alt"
    start = max(0, m.start() - 200)
    ctx = content[start:m.start()]
    print(f"\n[{i}] pos={m.start()}")
    print(f"    alt: {alt_val}")
    print(f"    src: {src_val}")
    print(f"    context: ...{ctx[-100:]}")
