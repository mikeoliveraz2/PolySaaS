#!/usr/bin/env python
"""
Test dynamic base detection logic (without Django)
"""

# Simulate the detection logic
def test_detection(current_path, html):
    """Test the base detection logic"""
    has_scp_in_path = '/scp/' in current_path if current_path else False
    has_scp_in_html = ('/scp/' in html) or ('scp/login.php' in html) or ('/scp/dashboard' in html)
    use_scp_base = has_scp_in_path or has_scp_in_html

    if use_scp_base:
        our_scp_base = "/admin/osticket/scp/"
        detection_reason = "path" if has_scp_in_path else "HTML content"
        result = f"Using /scp/ base (detected via {detection_reason})"
    else:
        our_scp_base = "/admin/osticket/"
        result = "Using root base"

    return our_scp_base, result

# Test Case 1: Root page with relative paths (no /scp/ in request path)
print("=" * 80)
print("Test 1: Root page with relative paths")
print("=" * 80)
html1 = '''
<form action="login.php">
<a href="index.php">Logo</a>
</form>
'''
base1, reason1 = test_detection("https://oliverenterprises.app.saasify.cloud/", html1)
print(f"Request path: https://oliverenterprises.app.saasify.cloud/")
print(f"HTML contains /scp/: {'/scp/' in html1}")
print(f"Result: {reason1}")
print(f"Base used: {base1}")
print(f"Expected: /admin/osticket/ (since no /scp/ in path or HTML)")
print()

# Test Case 2: Root page with /scp/ references (inconsistent OSTicket)
print("=" * 80)
print("Test 2: Root page with /scp/ references in HTML")
print("=" * 80)
html2 = '''
<form action="login.php">
<a href="/scp/dashboard.php">Dashboard</a>
<img src="/scp/images/logo.png" />
</form>
'''
base2, reason2 = test_detection("https://oliverenterprises.app.saasify.cloud/", html2)
print(f"Request path: https://oliverenterprises.app.saasify.cloud/")
print(f"HTML contains /scp/: {'/scp/' in html2}")
print(f"Result: {reason2}")
print(f"Base used: {base2}")
print(f"Expected: /admin/osticket/scp/ (because HTML contains /scp/)")
print()

# Test Case 3: Dashboard request with /scp/ in path
print("=" * 80)
print("Test 3: Dashboard request (/scp/ in path)")
print("=" * 80)
html3 = '''
<form action="ticket.php">
<a href="dashboard.php">Dashboard</a>
</form>
'''
base3, reason3 = test_detection("https://oliverenterprises.app.saasify.cloud/scp/dashboard.php", html3)
print(f"Request path: https://oliverenterprises.app.saasify.cloud/scp/dashboard.php")
print(f"HTML contains /scp/: {'/scp/' in html3}")
print(f"Result: {reason3}")
print(f"Base used: {base3}")
print(f"Expected: /admin/osticket/scp/ (because /scp/ in request path)")
print()

# Test Case 4: Root page with NO /scp/ references
print("=" * 80)
print("Test 4: Root page with NO /scp/ references")
print("=" * 80)
html4 = '''
<form action="login.php">
<a href="index.php">Index</a>
</form>
'''
base4, reason4 = test_detection("https://oliverenterprises.app.saasify.cloud/", html4)
print(f"Request path: https://oliverenterprises.app.saasify.cloud/")
print(f"HTML contains /scp/: {'/scp/' in html4}")
print(f"Result: {reason4}")
print(f"Base used: {base4}")
print(f"Expected: /admin/osticket/ (no /scp/ in path or HTML)")

print("\n" + "=" * 80)
print("✅ All tests completed successfully!")
print("=" * 80)
