import requests, re
s = requests.Session()
r = s.get('http://127.0.0.1:8000/accounts/login/', timeout=10)
print('Form fields:')
for m in re.finditer(r'<input[^>]+name="([^"]+)"', r.text):
    print(f'  {m.group(1)}')
print('\nForm action:')
m = re.search(r'<form[^>]*action="([^"]*)"', r.text)
print(f'  {m.group(1) if m else "default"}')
