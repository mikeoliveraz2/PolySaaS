"""Confirm Playwright resolves chromium the way the Django server process will.

Clears PLAYWRIGHT_BROWSERS_PATH so the lookup matches the server's environment,
then launches headless (no window) and reports the resolved executable.
"""
import os

os.environ.pop("PLAYWRIGHT_BROWSERS_PATH", None)

from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    print("executable:", p.chromium.executable_path)
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()
    page.goto("about:blank")
    print("launch: OK, version:", browser.version)
    browser.close()
