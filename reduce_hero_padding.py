"""Reduce hero background height/padding to reveal the header above."""
import requests, re, sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

BASE = "https://polysaas.online"
AUTH = ("mikeoliveraz@gmail.com", "vlop MpGU Os2V xDSI C6T7 2fAN")

r = requests.get(BASE + "/wp-json/wp/v2/pages/1313",
                 params={"context": "edit", "_fields": "content"},
                 auth=AUTH, timeout=45)
content = r.json()["content"]["raw"]

old_style = "padding:30px 20px 35px;margin:0 -2rem"
new_style = "padding:15px 20px 20px;margin:0 -2rem"

if old_style in content:
    content = content.replace(old_style, new_style)
    print("Reduced top/bottom padding")
else:
    print("Style not found, checking...")
    pos = content.find("hero-bg-serverroom")
    if pos > 0:
        print(content[max(0,pos-50):pos+200])
    sys.exit(1)

r2 = requests.post(BASE + "/wp-json/wp/v2/pages/1313",
                   auth=AUTH,
                   json={"content": content},
                   timeout=45)
print(f"Update: {r2.status_code}")
if r2.status_code == 200:
    print("SUCCESS - Hero background height reduced")
else:
    print(f"Error: {r2.text[:300]}")
