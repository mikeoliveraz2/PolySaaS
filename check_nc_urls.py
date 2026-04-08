import requests, re
r = requests.get('http://127.0.0.1:8888/login', timeout=5, allow_redirects=False)
urls = re.findall(r'(?:href|src|action)=["\']([^"\']+)["\']', r.text)
for u in urls[:20]:
    print(u)
print("---")
# Check if /pt/admin/nextcloud appears in the page
count = r.text.count('/pt/admin/nextcloud')
print(f"Occurrences of /pt/admin/nextcloud: {count}")
count2 = r.text.count('localhost:8000')
print(f"Occurrences of localhost:8000: {count2}")
