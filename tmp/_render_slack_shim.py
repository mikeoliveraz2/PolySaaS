"""Render the Slack shim and syntax-check it with node (if available)."""
import os
import sys

import django

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "mysite.settings")
django.setup()

from dose.passthrough.handlers.slack_handler import SlackPassthroughHandler  # noqa: E402

handler = SlackPassthroughHandler()
js = handler._client_shim("/pt/polysniff/app.slack.com", "olient", "https://app.slack.com")
body = js.split('<script data-polysaas-slack-shim="1">', 1)[1].rsplit("</script>", 1)[0]

out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "_shim_render.js")
with open(out, "w", encoding="utf-8") as fh:
    fh.write(body)

print("rendered chars:", len(body))
print("stray_root_paths:", handler.stray_root_paths())
print("wrote:", out)
