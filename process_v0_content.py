"""
Process V0.dev content through helper functions

This script:
1. Fetches real HTML from v0.dev
2. Runs it through the content-block approach
3. Shows the processed result
"""

import requests
from bs4 import BeautifulSoup
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import helper functions
from dose.passthrough_handlers.v0_handler import (
    rewrite_get_links_to_proxy,
    rewrite_assets_to_full_paths,
    inject_base_tag
)

def fetch_v0_content(url="https://v0.dev"):
    """Fetch HTML content from v0.dev"""
    print(f"Fetching content from: {url}")

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }

    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()

        # Handle content encoding
        if response.headers.get('Content-Encoding') == 'br':
            try:
                import brotli
                content = brotli.decompress(response.content)
                html = content.decode('utf-8', errors='replace')
            except ImportError:
                print("Brotli not available, using raw content")
                html = response.content.decode('utf-8', errors='replace')
        else:
            html = response.text

        print(f"✅ Fetched {len(html)} characters")
        return html

    except Exception as e:
        print(f"❌ Error fetching content: {e}")
        return None

def process_v0_content(html_content, proxy_base="/admin/polysniffer/proxy/123/", endpoint_id="123"):
    """Process HTML through content-block approach"""

    print("\n" + "="*60)
    print("PROCESSING V0 CONTENT THROUGH HELPER FUNCTIONS")
    print("="*60)

    # Parse HTML
    soup = BeautifulSoup(html_content, 'html.parser')

    # Extract body content
    body_content = soup.body if soup.body else soup
    content_wrapper = soup.new_tag('div', **{'class': 'v0-content-block'})

    if soup.body:
        for child in list(body_content.children):
            content_wrapper.append(child)
    else:
        content_wrapper.append(body_content)

    print("✅ Extracted body content into wrapper")

    # Apply helper functions
    content_html = str(content_wrapper)

    print("\n1. Rewriting GET links to proxy paths...")
    content_html = rewrite_get_links_to_proxy(content_html, proxy_base, endpoint_id)
    print("   ✅ Links rewritten")

    print("\n2. Rewriting asset paths to full URLs...")
    content_html = rewrite_assets_to_full_paths(content_html, 'https://v0.dev')
    print("   ✅ Assets rewritten")

    print("\n3. Injecting base tag...")
    content_html = inject_base_tag(content_html, 'https://v0.dev/')
    print("   ✅ Base tag injected")

    # Wrap in minimal HTML
    final_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>V0.dev via Dose - Processed Content</title>
    <base href="https://v0.dev/">
</head>
<body>
{content_html}
</body>
</html>"""

    print("✅ Final HTML constructed")
    return final_html

def main():
    print("="*80)
    print("V0.DEV CONTENT PROCESSOR")
    print("="*80)

    # Fetch content
    html_content = fetch_v0_content()
    if not html_content:
        return

    # Process through helper functions
    processed_html = process_v0_content(html_content)

    # Save results
    with open('v0_processed_content.html', 'w', encoding='utf-8') as f:
        f.write(processed_html)

    print(f"\n✅ Processed content saved to: v0_processed_content.html")
    print(f"   File size: {len(processed_html)} characters")

    # Show some stats
    soup = BeautifulSoup(processed_html, 'html.parser')
    links = soup.find_all('a', href=True)
    scripts = soup.find_all('script', src=True)
    styles = soup.find_all('link', rel='stylesheet')

    print("
📊 Content Analysis:"    print(f"   - Navigation links: {len(links)}")
    print(f"   - Scripts: {len(scripts)}")
    print(f"   - Stylesheets: {len(styles)}")

    print("
🔗 Sample processed links:"    for i, link in enumerate(links[:3]):
        print(f"   {i+1}. {link.get('href')}")

    print("
📁 Sample processed assets:"    for i, script in enumerate(scripts[:2]):
        print(f"   {i+1}. {script.get('src')}")

    print("
🎯 Ready to use! Open v0_processed_content.html in browser to see the result."    print("="*80)

if __name__ == "__main__":
    main()