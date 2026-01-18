#!/usr/bin/env python
"""Test if Flask can start and bind to port 5000"""
import sys
import os

# Change to pass_through_service directory
os.chdir('pass_through_service')

try:
    from app import app
    print("✓ Flask app imported successfully")

    # Try to start the app
    print("Attempting to start Flask on port 5000...")
    print("If this hangs, Flask is starting. Press Ctrl+C to stop.")

    app.run(
        host='0.0.0.0',
        port=5000,
        debug=False,
        use_reloader=False
    )
except OSError as e:
    if "Address already in use" in str(e) or "address is already in use" in str(e).lower():
        print("✗ Port 5000 is already in use")
        print("  Another process is using port 5000")
        print("  Check with: netstat -ano | findstr :5000")
    else:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
except Exception as e:
    print(f"✗ Error starting Flask: {e}")
    import traceback
    traceback.print_exc()

