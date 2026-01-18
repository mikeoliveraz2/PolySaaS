#!/usr/bin/env python3
"""Simple interactive proxy to preview and click through remote pages.

Run with:
    python -m dose.interactive_proxy

Open http://localhost:8000/ and click the button to load the demo osTicket instance.
"""

from fastapi import FastAPI, Request, Response, Form
from fastapi.responses import HTMLResponse, PlainTextResponse
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlencode, quote_plus, unquote_plus


app = FastAPI()


def rewrite_html(html: str, base_url: str) -> str:
    soup = BeautifulSoup(html, "html.parser")

    # rewrite href/src
    for tag in soup.find_all(True):
        for attr in ("href", "src"):
            if tag.has_attr(attr):
                try:
                    orig = tag[attr]
                    if orig.startswith("#"):
                        continue
                    abs_url = urljoin(base_url, orig)
                    tag[attr] = f"/proxy?u={quote_plus(abs_url)}"
                except Exception:
                    continue

    # rewrite form actions
    for form in soup.find_all("form"):
        action = form.get("action") or base_url
        abs_action = urljoin(base_url, action)
        form["action"] = f"/proxy?u={quote_plus(abs_action)}"
        # keep method as-is

    # inject a small banner to indicate served via proxy
    banner = soup.new_tag("div")
    banner.attrs["style"] = "position:fixed;left:0;right:0;top:0;background:#222;color:#fff;padding:6px;z-index:9999;"
    banner.string = f"Proxy view — original: {base_url} — Click links to navigate via proxy"
    body = soup.body
    if body:
        body.insert(0, banner)

    return str(soup)


@app.get("/", response_class=HTMLResponse)
def index():
    # Only load URLs explicitly provided via env var or form input
    demo = os.environ.get('OSTICKET_URL', '')
    html = f"""
    <html><head><title>Interactive Proxy</title></head>
    <body style='font-family:Arial,sans-serif; padding:30px;'>
      <h2>Interactive Proxy Preview</h2>
      <p>Click the button below to load the demo osTicket page through the proxy.</p>
      <!-- Demo URL removed - use only explicit URLs -->
      <hr/>
      <p>Or enter a URL:</p>
      <form action="/proxy" method="get">
        <input type="text" name="u" style="width:60%" placeholder="https://example.com/" />
        <button type="submit">Open</button>
      </form>
    </body></html>
    """
    return HTMLResponse(content=html)


@app.api_route("/proxy", methods=["GET", "POST"])  # handle both get/post
async def proxy(request: Request):
    params = dict(request.query_params)
    u = params.get("u")
    if not u:
        return PlainTextResponse("Missing 'u' parameter", status_code=400)

    target = unquote_plus(u)
    try:
        if request.method == "POST":
            form = await request.form()
            resp = requests.post(target, data=form, timeout=15)
        else:
            # GET: simply proxy
            resp = requests.get(target, timeout=15)
    except Exception as e:
        return PlainTextResponse(f"Error fetching target: {e}", status_code=502)

    ctype = resp.headers.get("content-type", "")
    if "html" in ctype:
        rewritten = rewrite_html(resp.text, target)
        return HTMLResponse(content=rewritten, status_code=resp.status_code)
    else:
        # non-html, return raw bytes with same content-type
        return Response(content=resp.content, media_type=ctype)


def run():
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)


if __name__ == "__main__":
    run()
