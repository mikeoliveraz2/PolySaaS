"""Reset WordPress admin password via REST API so we can log into Customizer."""
import requests, sys
sys.stdout.reconfigure(encoding='utf-8')

AZURE = "https://azure-nightingale-589250.hostingersite.com"
s = requests.Session()
s.auth = ("mikeoliveraz@gmail.com", "vlop MpGU Os2V xDSI C6T7 2fAN")

NEW_PASSWORD = "M@ster119611p"

# Update user 1's password
r = s.post(f"{AZURE}/wp-json/wp/v2/users/1", json={"password": NEW_PASSWORD})
print(f"Status: {r.status_code}")
if r.status_code == 200:
    print("Password updated successfully!")
    print(f"User: {r.json().get('name', 'unknown')}")
else:
    print(f"Error: {r.text[:300]}")
