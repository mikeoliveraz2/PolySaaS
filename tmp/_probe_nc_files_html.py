"""Inspect Nextcloud /apps/files/ HTML: auth page vs files UI, CSS links, base tags."""
import re
import requests

r = requests.get("http://127.0.0.1:8888/apps/files/", timeout=15, allow_redirects=True)
text = r.text
print("status", r.status_code, "final", r.url, "len", len(text))
print("ct", (r.headers.get("Content-Type") or "")[:80])
low = text.lower()
print("has password confirm", "confirm your password" in low)
print("has skip to main", "Skip to main content" in text)
print("has files-list", "files-list" in text or "id=\"app-content\"" in text)
print("base tags", re.findall(r"<base[^>]*>", text, re.I)[:5])
links = re.findall(
    r"<(?:link|script)[^>]*(?:href|src)=[\"']([^\"']+)[\"']",
    text,
    re.I,
)
print("asset count", len(links))
for u in links[:30]:
    print(" ", u[:140])
for m in re.findall(r"<title[^>]*>(.*?)</title>", text, re.I | re.S)[:2]:
    print("title", re.sub(r"\s+", " ", m).strip()[:100])
# snippet around password
idx = low.find("confirm your password")
if idx >= 0:
    print("snippet:", re.sub(r"\s+", " ", text[max(0, idx - 80) : idx + 120]))
