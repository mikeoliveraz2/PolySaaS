import requests
import re

s = requests.Session()

# Get login page
r1 = s.get('http://127.0.0.1:8000/accounts/login/', timeout=10)
print(f"GET /accounts/login/ -> {r1.status_code}")

csrf_match = re.search(r'name="csrfmiddlewaretoken" value="([^"]+)"', r1.text)
if not csrf_match:
    print("No CSRF token found!")
    exit(1)
csrf = csrf_match.group(1)
print(f"CSRF: {csrf[:20]}...")

# Try login
r2 = s.post(
    'http://127.0.0.1:8000/accounts/login/',
    data={
        'csrfmiddlewaretoken': csrf,
        'login': 'olientAdmin',
        'password': 'admin',
    },
    headers={'Referer': 'http://127.0.0.1:8000/accounts/login/'},
    allow_redirects=False,
    timeout=10,
)
print(f"POST /accounts/login/ -> {r2.status_code}")
print(f"Location: {r2.headers.get('Location', 'NONE')}")

if r2.status_code == 200:
    # Check for error message
    if "incorrect" in r2.text.lower() or "invalid" in r2.text.lower():
        print("Login failed - wrong credentials")
    elif "form" in r2.text.lower():
        print("Login failed - form shown again")
        # Find error
        err = re.search(r'class="[^"]*error[^"]*"[^>]*>([^<]+)', r2.text)
        if err:
            print(f"Error: {err.group(1)}")
