import sys
try:
    from dose.passthrough.handlers.mattermost_handler import MattermostHandler
    print("SUCCESS: MattermostHandler imported")
except Exception as e:
    print(f"ERROR: {e}")
    import traceback
    traceback.print_exc()
