#!/usr/bin/env python
"""Check if TEST log code is in the generated shim."""
import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')

# Setup Django
try:
    django.setup()
except ModuleNotFoundError:
    print("Cannot set up Django (config.settings not found)")
    sys.exit(1)

from dose.passthrough.handlers.mattermost_handler import MattermostPassthroughHandler
from django.http import HttpRequest

# Create minimal request
request = HttpRequest()
request.session = {'display_mode': 'dark'}
request.COOKIES = {'display_mode': 'dark'}

# Generate shim
handler = MattermostPassthroughHandler()
try:
    shim = handler._inject_client_shim(
        html="<html><body></body></html>",
        base_origin="https://mm.test.com",
        request=request,
        proxy_prefix="/pt/admin/mm.test.com"
    )
    
    print("Generated shim length:", len(shim))
    
    # Check for test log
    if '[PolySaaS MM] TEST: Code reached' in shim:
        print("✓ TEST log FOUND in generated shim")
        idx = shim.find('[PolySaaS MM] TEST:')
        print(f"  Position: {idx}")
        print(f"  Context: ...{shim[max(0,idx-100):idx+200]}...")
    else:
        print("✗ TEST log NOT FOUND in generated shim")
        
        # Check what comes after "Full shim loaded"
        if '[PolySaaS Mattermost] Full shim loaded' in shim:
            idx = shim.find('[PolySaaS Mattermost] Full shim loaded')
            print(f"✓ 'Full shim loaded' found at {idx}")
            nextpart = shim[idx:idx+800]
            print(f"  What comes next (800 chars):")
            print(f"  {nextpart}")
        else:
            print("✗ 'Full shim loaded' not found either")

except Exception as e:
    print(f"Error generating shim: {e}")
    import traceback
    traceback.print_exc()
