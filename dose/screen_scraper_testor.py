#!/usr/bin/env python3
"""
Small utility moved into the `dose` package for debugging external HTML resources.

Usage as a script:
    python -m dose.screen_scraper_testor

Also importable: call `debug_external_html()` from other code.
"""

import requests
from bs4 import BeautifulSoup


def debug_external_html(url: str = "https://demozone.surpaascompaas.com/surpaas/"):
    """Get the external HTML and analyze its structure.

    Returns a dict with summary info for programmatic use.
    """
    summary = {
        "url": url,
        "status_code": None,
        "content_type": None,
        "content_length": 0,
        "counts": {"links": 0, "scripts": 0, "images": 0},
        "samples": {"links": [], "scripts": [], "images": []},
        "surpaas_lines": [],
        "html_snippet": "",
        "error": None,
    }

    try:
        response = requests.get(url, timeout=10)
        summary["status_code"] = response.status_code
        summary["content_type"] = response.headers.get("content-type", "")
        summary["content_length"] = len(response.text)

        soup = BeautifulSoup(response.text, "html.parser")

        links = soup.find_all("link", href=True)
        scripts = soup.find_all("script", src=True)
        images = soup.find_all("img", src=True)

        summary["counts"]["links"] = len(links)
        summary["counts"]["scripts"] = len(scripts)
        summary["counts"]["images"] = len(images)

        summary["samples"]["links"] = [link.get("href", "") for link in links[:5]]
        summary["samples"]["scripts"] = [script.get("src", "") for script in scripts[:5]]
        summary["samples"]["images"] = [img.get("src", "") for img in images[:5]]

        summary["html_snippet"] = response.text[:1000]

        if "/surpaas/" in response.text:
            lines_with_surpaas = [line.strip() for line in response.text.split("\n") if "/surpaas/" in line]
            summary["surpaas_lines"] = lines_with_surpaas[:50]

    except Exception as e:
        summary["error"] = str(e)

    return summary


def _print_summary(summary: dict):
    if not summary:
        print("No summary available")
        return

    print(f"URL: {summary.get('url')}")
    print(f"Response status: {summary.get('status_code')}")
    print(f"Content type: {summary.get('content_type')}")
    print(f"Content length: {summary.get('content_length')} characters")
    print("\nFound elements:")
    for k, v in summary.get("counts", {}).items():
        print(f"  {k.capitalize()}: {v}")

    print("\nSample links:")
    for i, href in enumerate(summary.get("samples", {}).get("links", []) or []):
        print(f"  {i+1}. href='{href}'")

    print("\nSample scripts:")
    for i, src in enumerate(summary.get("samples", {}).get("scripts", []) or []):
        print(f"  {i+1}. src='{src}'")

    print("\nSample images:")
    for i, src in enumerate(summary.get("samples", {}).get("images", []) or []):
        print(f"  {i+1}. src='{src}'")

    print("\nFirst 1000 characters of HTML:")
    print(summary.get("html_snippet", "")[:1000])
    print("\n" + "=" * 50)

    if summary.get("surpaas_lines"):
        print(f"\nFound {len(summary.get('surpaas_lines'))} lines containing /surpaas/:")
        for i, line in enumerate(summary.get("surpaas_lines")[:10]):
            print(f"  {i+1}. {line[:200]}...")

    if summary.get("error"):
        print(f"\nError: {summary.get('error')}")


def _extract_links(soup, base_url=""):
    anchors = []
    for a in soup.find_all("a", href=True):
        href = a.get("href")
        text = a.get_text(strip=True)
        anchors.append({"href": href, "text": text})
    return anchors


def interactive_repl(start_url: str = None):
    """Simple interactive session to navigate links and submit forms.

    Commands:
      open <url>     - navigate to a URL
      links          - list links on the current page
      follow <n>     - follow link number n
      forms          - list forms on the current page
      submit <n>     - submit form number n (prompts for inputs)
      back           - go back to previous page
      summary        - show summary for current page
      save <path>    - save current HTML to path
      help           - show commands
      exit           - quit
    """
    # Default to OSTicket proxy endpoint if no URL provided
    if start_url is None:
        start_url = "http://127.0.0.1:8001/admin/osticket/login.php"

    session = requests.Session()
    history = []
    current = {"url": start_url, "resp": None, "soup": None}

    def load(url):
        try:
            resp = session.get(url, timeout=10)
            soup = BeautifulSoup(resp.text, "html.parser")
            return {"url": url, "resp": resp, "soup": soup}
        except Exception as e:
            print(f"Error loading {url}: {e}")
            return None

    if start_url:
        node = load(start_url)
        if node:
            current = node
        else:
            print(f"Warning: Could not load default URL {start_url}")

    print("Interactive scraper REPL. Type 'help' for commands.")
    while True:
        try:
            cmd = input("scraper> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break

        if not cmd:
            continue
        parts = cmd.split()
        c = parts[0].lower()

        if c == "help":
            print(interactive_repl.__doc__)
        elif c == "open" and len(parts) > 1:
            url = parts[1]
            node = load(url)
            if node:
                if current.get("resp"):
                    history.append(current)
                current = node
                print(f"Loaded {url} (status {current['resp'].status_code})")
        elif c == "links":
            if not current.get("soup"):
                print("No page loaded")
                continue
            links = _extract_links(current["soup"], current.get("url"))
            for i, a in enumerate(links, start=1):
                print(f"{i}. {a['text'][:60]} -> {a['href']}")
        elif c == "follow" and len(parts) > 1:
            try:
                idx = int(parts[1]) - 1
            except ValueError:
                print("Invalid index")
                continue
            links = _extract_links(current.get("soup") or BeautifulSoup("", "html.parser"))
            if idx < 0 or idx >= len(links):
                print("Index out of range")
                continue
            href = links[idx]["href"]
            # resolve relative URLs
            url = requests.compat.urljoin(current.get("url") or "", href)
            node = load(url)
            if node:
                history.append(current)
                current = node
                print(f"Loaded {url} (status {current['resp'].status_code})")
        elif c == "back":
            if not history:
                print("No history")
                continue
            current = history.pop()
            print(f"Back to {current.get('url')}")
        elif c == "summary":
            if not current.get("resp"):
                print("No page loaded")
                continue
            s = {
                "url": current.get("url"),
                "status_code": current["resp"].status_code,
                "content_type": current["resp"].headers.get("content-type", ""),
                "content_length": len(current["resp"].text),
            }
            print(f"URL: {s['url']}")
            print(f"Status: {s['status_code']}")
            print(f"Content-Type: {s['content_type']}")
            print(f"Length: {s['content_length']}")
        elif c == "forms":
            if not current.get("soup"):
                print("No page loaded")
                continue
            forms = current["soup"].find_all("form")
            if not forms:
                print("No forms found")
                continue
            for i, f in enumerate(forms, start=1):
                action = f.get("action", "")
                method = f.get("method", "get").lower()
                inputs = [inp.get("name") for inp in f.find_all(["input", "textarea"]) if inp.get("name")]
                print(f"{i}. action={action} method={method} inputs={inputs}")
        elif c == "submit" and len(parts) > 1:
            try:
                idx = int(parts[1]) - 1
            except ValueError:
                print("Invalid index")
                continue
            forms = current.get("soup").find_all("form")
            if idx < 0 or idx >= len(forms):
                print("Index out of range")
                continue
            form = forms[idx]
            action = form.get("action") or current.get("url")
            method = form.get("method", "get").lower()
            data = {}
            for inp in form.find_all(["input", "textarea"]):
                name = inp.get("name")
                if not name:
                    continue
                v = inp.get("value", "")
                prompt = f"{name} (default='{v}'): "
                try:
                    nv = input(prompt).strip()
                except (EOFError, KeyboardInterrupt):
                    nv = ""
                data[name] = nv if nv else v
            url = requests.compat.urljoin(current.get("url") or "", action)
            if method == "post":
                resp = session.post(url, data=data)
            else:
                resp = session.get(url, params=data)
            node = {"url": url, "resp": resp, "soup": BeautifulSoup(resp.text, "html.parser")}
            history.append(current)
            current = node
            print(f"Submitted form, loaded {url} (status {resp.status_code})")
        elif c == "save" and len(parts) > 1:
            path = parts[1]
            if not current.get("resp"):
                print("No page loaded")
                continue
            with open(path, "w", encoding="utf-8") as fh:
                fh.write(current["resp"].text)
            print(f"Saved to {path}")
        elif c == "exit":
            break
        else:
            print("Unknown command. Type 'help' for commands.")


if __name__ == "__main__":
    # Default behavior: non-interactive summary
    s = debug_external_html()
    _print_summary(s)
    # To enter interactive mode, run: python -m dose.screen_scraper_testor interactive <url>

