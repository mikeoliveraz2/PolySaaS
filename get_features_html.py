"""Extract the Platform Features section HTML from the homepage."""
import requests, sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

AZURE = "https://azure-nightingale-589250.hostingersite.com"
s = requests.Session()
s.auth = ("mikeoliveraz@gmail.com", "vlop MpGU Os2V xDSI C6T7 2fAN")

r = s.get(f"{AZURE}/wp-json/wp/v2/pages",
          params={"slug": "home", "context": "edit", "_fields": "id,content"},
          timeout=30)
page = r.json()[0]
raw = page['content']['raw']
page_id = page['id']
print(f"Page ID: {page_id}, length: {len(raw)} chars")

start = raw.find('Platform Features')
if start < 0:
    print("Platform Features not found")
    sys.exit(1)

section_start = raw.rfind('<!--', max(0, start - 200), start)
if section_start < 0:
    section_start = start - 100

end_marker = raw.find('Stop Managing Tools', start)
if end_marker < 0:
    end_marker = start + 5000

section = raw[section_start:end_marker]
print(f"\n=== Platform Features section ({section_start}:{end_marker}, {len(section)} chars) ===")
print(section[:4000])
print("\n... (truncated)")
