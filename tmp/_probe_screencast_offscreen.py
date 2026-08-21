"""Does an off-screen Chrome window still produce screencast frames?

Launches with the same arguments the Native capture uses and reports how many
frames arrive, so pane-blankness can be told apart from launch problems.
"""
import base64
import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "mysite.settings")
os.environ.pop("PLAYWRIGHT_BROWSERS_PATH", None)

import django

django.setup()

from dose.polysniffer.native_browser_capture import _LAUNCH_ARGS

from playwright.sync_api import sync_playwright

print("launch args:", _LAUNCH_ARGS)

with tempfile.TemporaryDirectory() as profile:
    with sync_playwright() as p:
        context = p.chromium.launch_persistent_context(
            profile, headless=False, no_viewport=True, args=_LAUNCH_ARGS
        )
        page = context.pages[0] if context.pages else context.new_page()
        pending = []
        cdp = context.new_cdp_session(page)
        cdp.on("Page.screencastFrame", lambda frame: pending.append(frame))
        cdp.send(
            "Page.startScreencast",
            {"format": "jpeg", "quality": 70, "maxWidth": 1920,
             "maxHeight": 1200, "everyNthFrame": 1},
        )
        page.goto("https://example.com", wait_until="domcontentloaded")

        total = 0
        sizes = []
        for _ in range(80):
            page.wait_for_timeout(50)
            while pending:
                frame = pending.pop(0)
                total += 1
                sizes.append(len(base64.b64decode(frame["data"])))
                try:
                    cdp.send(
                        "Page.screencastFrameAck",
                        {"sessionId": frame["sessionId"]},
                    )
                except Exception as exc:
                    print("ack failed:", exc)
            if total >= 5:
                break

        print("frames received:", total)
        if sizes:
            print("frame bytes:", sizes[:5])
            meta = None
            print("verdict: OFF-SCREEN SCREENCAST WORKS")
        else:
            print("verdict: NO FRAMES from an off-screen window")
        context.close()
