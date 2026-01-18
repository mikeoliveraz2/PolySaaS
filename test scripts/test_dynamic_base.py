#!/usr/bin/env python
"""
Test the dynamic base detection in doseify_html
"""
import sys
sys.path.insert(0, r'c:\Users\PC\OneDrive\Documents\GitHub\DoseV3MasterSaaS-main-main')

from dose.osticket_admin import doseify_html

# Simulate HTML from root page (no /scp/ in path)
html_root = '''
<html>
<head>
<link rel="stylesheet" href="css/login.css" type="text/css" />
<link type="text/css" rel="stylesheet" href="/css/font-awesome.min.css"/>
<script type="text/javascript" src="/js/jquery-3.4.0.min.js"></script>
</head>
<body>
<form action="login.php" method="post" id="login">
    <input type="hidden" name="__CSRFToken__" value="test" />
    <input type="hidden" name="do" value="scplogin">
</form>
<a href="index.php">Logo</a>
<a href="pwreset.php">Forgot My Password</a>
<img src="logo.php?login" alt="logo" />
<img src="images/osticket-grey.png" alt="osticket" />
</body>
</html>
'''

# Test 1: Root page (no /scp/ in path)
print("=" * 80)
print("TEST 1: Root page (no /scp/ in path)")
print("=" * 80)
print("\nTarget URL: https://oliverenterprises.app.saasify.cloud/")
doseified = doseify_html(html_root, current_path="https://oliverenterprises.app.saasify.cloud/")

print("\n--- Original form action ---")
import re
orig_action = re.search(r'action="([^"]*)"', html_root)
if orig_action:
    print(f"  {orig_action.group(0)}")

print("\n--- Doseified form action ---")
new_action = re.search(r'action="([^"]*)"', doseified)
if new_action:
    print(f"  {new_action.group(0)}")
    if 'admin/osticket' in new_action.group(1):
        print("  ✅ PASS: Form action rewritten correctly")
    else:
        print("  ❌ FAIL: Form action NOT rewritten")

# Test 2: Dashboard page (with /scp/ in path)
print("\n" + "=" * 80)
print("TEST 2: Dashboard page (with /scp/ in path)")
print("=" * 80)

html_dashboard = '''
<html>
<head>
<link rel="stylesheet" href="css/dashboard.css" type="text/css" />
</head>
<body>
<form action="ticket.php" method="post">
    <input type="hidden" name="do" value="save">
</form>
<a href="dashboard.php">Dashboard</a>
<a href="/scp/tickets.php">Tickets</a>
</body>
</html>
'''

print("\nTarget URL: https://oliverenterprises.app.saasify.cloud/scp/dashboard.php")
doseified2 = doseify_html(html_dashboard, current_path="https://oliverenterprises.app.saasify.cloud/scp/dashboard.php")

print("\n--- Original relative PHP action ---")
orig_action2 = re.search(r'action="([^"]*)"', html_dashboard)
if orig_action2:
    print(f"  {orig_action2.group(0)}")

print("\n--- Doseified relative PHP action ---")
new_action2 = re.search(r'action="([^"]*)"', doseified2)
if new_action2:
    print(f"  {new_action2.group(0)}")
    if '/admin/osticket/scp/ticket.php' in new_action2.group(1):
        print("  ✅ PASS: Form action rewritten to /scp/ base")
    else:
        print("  ❌ FAIL: Form action NOT rewritten correctly")

print("\n--- Original /scp/ link ---")
orig_link = re.search(r'href="/scp/([^"]*)"', html_dashboard)
if orig_link:
    print(f"  href=\"/scp/{orig_link.group(1)}\"")

print("\n--- Doseified /scp/ link ---")
new_link = re.search(r'href="([^"]*tickets[^"]*)"', doseified2)
if new_link:
    print(f"  {new_link.group(0)}")
    if '/admin/osticket/scp/' in new_link.group(1):
        print("  ✅ PASS: /scp/ link rewritten correctly")
    else:
        print("  ❌ FAIL: /scp/ link NOT rewritten")

print("\n" + "=" * 80)
print("Tests complete!")
print("=" * 80)
