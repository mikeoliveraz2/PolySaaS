"""
Test the form action rewriting fix
"""
import sys
sys.path.insert(0, '.')

# Import the doseify function
from dose.osticket_admin import doseify_html

# Test HTML with relative form action (like OSTicket login form)
test_html = '''
<html>
<head><title>Login</title></head>
<body>
<form action="login.php" method="post" onsubmit="attemptLoginAjax(event)">
    <input type="text" name="userid" placeholder="Email or Username">
    <input type="password" name="passwd" placeholder="Password">
    <button type="submit">Log in</button>
</form>
</body>
</html>
'''

print("=" * 60)
print("INPUT HTML:")
print("=" * 60)
print(test_html)

print("\n" + "=" * 60)
print("PROCESSING WITH doseify_html()...")
print("=" * 60)

result = doseify_html(test_html)

print("\n" + "=" * 60)
print("OUTPUT HTML:")
print("=" * 60)
print(result)

print("\n" + "=" * 60)
print("VERIFICATION:")
print("=" * 60)

# Check if form action was rewritten
if 'action="/admin/osticket/login.php"' in result:
    print("✅ Form action correctly rewritten: action=\"/admin/osticket/login.php\"")
else:
    print("❌ Form action NOT rewritten correctly")
    # Show what we got instead
    import re
    actions = re.findall(r'action="[^"]*"', result)
    print(f"   Found actions: {actions}")

# Check if JavaScript interceptors are present
if '[OSTicket Form] Rewriting form action' in result:
    print("✅ Form submit interceptor JS injected")
else:
    print("❌ Form submit interceptor JS NOT found")

if '[OSTicket jQuery] Rewriting URL' in result:
    print("✅ jQuery AJAX interceptor JS injected")
else:
    print("❌ jQuery AJAX interceptor JS NOT found")

print()
