# Run this in your Django shell: python manage.py shell
from django.contrib.auth import authenticate

username = "polysaasIncAdmin"
password = "PolySaaS2026!"
user = authenticate(username=username, password=password)
if user is not None:
    print(f"Authenticated: True (User: {user.username})")
else:
    print("Authenticated: False (User not found or password mismatch)")
