"""Probe whether a page script can intercept window.location / Location navigation.

Read-only diagnostic for the Slack passthrough shim: determines if the fallback
redirect (window.location = '/auth?...') can be rewritten client-side.
"""
from playwright.sync_api import sync_playwright

PROBE = """
() => {
    const out = {};
    const winLoc = Object.getOwnPropertyDescriptor(window, 'location')
        || Object.getOwnPropertyDescriptor(Window.prototype, 'location');
    out.window_location_descriptor = winLoc ? {
        configurable: winLoc.configurable,
        has_set: typeof winLoc.set === 'function',
        own: !!Object.getOwnPropertyDescriptor(window, 'location'),
    } : null;

    out.location_proto_href = !!Object.getOwnPropertyDescriptor(Location.prototype, 'href');
    out.location_proto_assign = typeof Location.prototype.assign;
    out.location_own_href = !!Object.getOwnPropertyDescriptor(window.location, 'href');
    const ownHref = Object.getOwnPropertyDescriptor(window.location, 'href');
    out.location_own_href_configurable = ownHref ? ownHref.configurable : null;

    try {
        Object.defineProperty(window, 'location', { get: () => 'hijacked' });
        out.redefine_window_location = 'succeeded';
    } catch (e) {
        out.redefine_window_location = 'threw: ' + e.name;
    }
    try {
        Object.defineProperty(window.location, 'href', { set: () => {} });
        out.redefine_location_href = 'succeeded';
    } catch (e) {
        out.redefine_location_href = 'threw: ' + e.name;
    }
    out.navigation_api = typeof window.navigation !== 'undefined';
    return out;
}
"""

with sync_playwright() as p:
    browser = p.chromium.launch(channel="chrome")
    page = browser.new_page()
    page.goto("about:blank")
    for k, v in page.evaluate(PROBE).items():
        print(f"{k}: {v}")
    browser.close()
