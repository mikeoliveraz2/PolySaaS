"""Download LoginUI bundle and find MISSING_FRAGMENTS trigger."""
import re
import requests

url = "https://static.hsappstatic.net/LoginUI/static-1.15500/bundles/project.js"
js = requests.get(url, timeout=30, headers={"Accept-Encoding": "identity"}).text
print("len", len(js))

for label, pat in [
    ("MISSING_FRAGMENTS", r"MISSING_FRAGMENTS"),
    ("correctedUrl", r"correctedUrl"),
    ("fragments", r"fragment"),
    ("magic", r"magic"),
    ("loginPath", r"loginPath"),
    ("pathname", r"pathname"),
]:
    idx = js.lower().find(label.lower()) if label != "MISSING_FRAGMENTS" else js.find("MISSING_FRAGMENTS")
    print(label, "count", js.lower().count(label.lower()) if label != "MISSING_FRAGMENTS" else js.count(label))

pos = js.find("MISSING_FRAGMENTS")
print("\n--- context around MISSING_FRAGMENTS ---")
print(js[max(0, pos - 500) : pos + 1200][:1700])

# search for function that sets error type
for m in re.finditer(r".{0,80}MISSING_FRAGMENTS.{0,200}", js):
    print("\nMATCH:", m.group(0)[:280])
