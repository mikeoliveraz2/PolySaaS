#!/usr/bin/env python
"""Extract and validate the Mattermost shim JavaScript."""
import os
import sys
import django

# Find the Django settings module
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
try:
    django.setup()
except Exception as e:
    print(f"Django setup error: {e}")
    print("Trying alternate settings path...")
    os.environ['DJANGO_SETTINGS_MODULE'] = 'settings'
    try:
        django.setup()
    except:
        pass

from django.contrib.auth.models import User
from django.http import HttpRequest
from dose.passthrough.handlers.mattermost_handler import MattermostPassthroughHandler
from dose.models import Endpoint

# Create a minimal request object
request = HttpRequest()
request.method = 'GET'
request.session = {}
request.COOKIES = {'display_mode': 'dark'}

# Get an endpoint (or mock one)
try:
    endpoint = Endpoint.objects.filter(slug__icontains='mattermost').first()
    if not endpoint:
        print("No Mattermost endpoint found")
        sys.exit(1)
except Exception as e:
    print(f"Error fetching endpoint: {e}")
    sys.exit(1)

handler = MattermostPassthroughHandler()

# Generate the shim
try:
    shim_html = handler._inject_client_shim(
        html="<html><body></body></html>",
        base_origin="https://mattermost.example.com",
        request=request,
        proxy_prefix="/pt/admin/mattermost.example.com"
    )
    
    # Extract just the script part
    start = shim_html.find('<script')
    end = shim_html.find('</script>') + len('</script>')
    script = shim_html[start:end]
    
    # Save to file for inspection
    with open('/tmp/mattermost_shim.js', 'w') as f:
        f.write(script)
    
    print(f"✓ Shim generated successfully ({len(script)} chars)")
    print(f"✓ Saved to /tmp/mattermost_shim.js")
    
    # Find "Full shim loaded"
    if 'Full shim loaded' in script:
        idx = script.find('Full shim loaded')
        print(f"✓ 'Full shim loaded' found at position {idx}")
        print(f"  Context: ...{script[idx-50:idx+150]}...")
    
    # Find "TEST: Code reached"
    if 'TEST: Code reached' in script:
        idx = script.find('TEST: Code reached')
        print(f"✓ 'TEST: Code reached' found at position {idx}")
        print(f"  Context: ...{script[idx-50:idx+150]}...")
    else:
        print("✗ 'TEST: Code reached' NOT FOUND IN GENERATED SCRIPT")
    
    # Check for obvious syntax errors
    open_braces = script.count('{')
    close_braces = script.count('}')
    open_parens = script.count('(')
    close_parens = script.count(')')
    
    print(f"\nBrace count: {open_braces} open, {close_braces} close (diff: {open_braces - close_braces})")
    print(f"Paren count: {open_parens} open, {close_parens} close (diff: {open_parens - close_parens})")
    
    if open_braces != close_braces:
        print("⚠️  WARNING: Mismatched braces!")
    if open_parens != close_parens:
        print("⚠️  WARNING: Mismatched parentheses!")
        
except Exception as e:
    print(f"✗ Error generating shim: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
