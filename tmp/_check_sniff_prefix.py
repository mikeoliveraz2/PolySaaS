from dose.polysniffer.sniff_pt_proxy import _prefix_sniff_root_urls

html = (
    '<link href="/core/css/server.css">'
    '<script src="/pt/polysniff/3/dist/x.js"></script>'
    '<a href="/admin/x">'
    '<img src="/apps/theming/icon">'
)
out = _prefix_sniff_root_urls(html, "/pt/polysniff/3")
assert "/pt/polysniff/3/core/css/server.css" in out
assert out.count("/pt/polysniff/3/dist/x.js") == 1
assert 'href="/admin/x"' in out
assert "/pt/polysniff/3/apps/theming/icon" in out
print("ok", out)
