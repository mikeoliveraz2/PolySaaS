import re

html = '<link href="//static.hsappstatic.net/foo/hubspot-theme.stable.css" rel="stylesheet">'
fixed = re.sub(
    r"(src|href)=(['\"])(//(?:static(?:2)?\.hsappstatic\.net|wt-assets)[^'\"]*)\2",
    r"\1=\2https:\3\2",
    html,
    flags=re.IGNORECASE,
)
print("BEFORE:", html)
print("AFTER: ", fixed)
assert '.css""' not in fixed
assert 'https://static.hsappstatic.net' in fixed
print("OK")
