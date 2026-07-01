import re
import requests

js = requests.get(
    "https://static.hsappstatic.net/LoginUI/static-1.15500/bundles/project.js",
    timeout=30,
    headers={"Accept-Encoding": "identity"},
).text

# Extract all ao path= routes (React Router Route)
routes = re.findall(r'\(0,J\.jsx\)\(ao,\{path:"([^"]+)"', js)
print("Route paths:", sorted(set(routes)))

# Find basename / router setup
for needle in ["basename", "BrowserRouter", "createBrowserHistory", "getBasename"]:
    i = js.find(needle)
    if i >= 0:
        print(f"\n{needle}:", js[max(0, i - 50) : i + 250].replace("\n", " ")[:300])

# Find what renders on /connect or default /
for path in ["/connect", "/login", "/"]:
    idx = js.find(f'path:"{path}"')
    if idx >= 0:
        print(f"\npath {path}:", js[idx : idx + 200])

for m in re.finditer(r'path:"(/connect[^"]*)"', js):
    print("\nconnect route:", js[m.start() : m.start() + 220].replace("\n", " "))

i = js.find('path:"*"')
print("\nstar route:", js[i : i + 350].replace("\n", " "))
