"""Find the element that carries the body gradient on the Home page
and compare with Architecture page to write a site-wide fix."""
import requests
import re

SITE = "https://azure-nightingale-589250.hostingersite.com"

session = requests.Session()
session.headers.update({'User-Agent': 'Mozilla/5.0'})

for name, slug in [('Home', '/'), ('Architecture', '/architecture/')]:
    print(f"\n{'='*80}")
    print(f"PAGE: {name} ({slug})")
    print(f"{'='*80}")
    
    resp = session.get(f"{SITE}{slug}", timeout=15)
    html = resp.text
    
    # Find the main content wrapper and its background
    # Look for <section> and top-level <div> elements with gradient backgrounds
    style_blocks = re.findall(r'<style[^>]*>(.*?)</style>', html, re.DOTALL)
    all_css = '\n'.join(style_blocks)
    
    # Find all rules with gradient backgrounds
    gradient_rules = re.findall(
        r'(#brxe-[a-zA-Z0-9]+(?:\s[^{]*)?)\{([^}]*(?:linear-gradient|background-image)[^}]*)\}',
        all_css
    )
    
    print(f"\n  Elements with gradient backgrounds:")
    for selector, body in gradient_rules:
        gradients = re.findall(r'linear-gradient\([^)]+(?:\([^)]*\))*[^)]*\)', body)
        if gradients:
            for g in gradients:
                print(f"    {selector.strip()}")
                print(f"      {g[:100]}")
    
    # Find the outermost wrapper element with a background
    # Look for <header>, first <section>, or main content area
    wrapper_pattern = re.findall(
        r'<(section|div|header)[^>]*id="(brxe-[^"]*)"[^>]*class="([^"]*)"',
        html[:5000]  # First 5000 chars = top of page
    )
    print(f"\n  Top-level Bricks elements (first 5000 chars):")
    for tag, elem_id, classes in wrapper_pattern:
        print(f"    <{tag} id=\"{elem_id}\" class=\"{classes[:80]}\"")
    
    # Check for body-level or brxe-header backgrounds
    body_bg = re.findall(r'body\s*\{([^}]*background[^}]*)\}', all_css)
    if body_bg:
        print(f"\n  Body background CSS:")
        for bg in body_bg:
            print(f"    {bg.strip()[:200]}")
    
    # Find the first section's background
    first_section = re.search(
        r'<section[^>]*id="(brxe-[^"]*)"[^>]*class="([^"]*brxe-section[^"]*)"',
        html
    )
    if first_section:
        sect_id = first_section.group(1)
        sect_classes = first_section.group(2)
        print(f"\n  First section: #{sect_id} class=\"{sect_classes[:80]}\"")
        
        # Find its CSS rule
        sect_css = re.findall(
            f'#{sect_id}\\s*{{([^}}]+)}}',
            all_css
        )
        if sect_css:
            for rule in sect_css:
                if 'background' in rule or 'gradient' in rule:
                    print(f"    CSS: {rule.strip()[:200]}")
    
    # Look at the overall page wrapper
    content_wrapper = re.search(
        r'<div[^>]*id="(brxe-[^"]*)"[^>]*class="([^"]*brxe-container[^"]*)"',
        html[:3000]
    )
    if content_wrapper:
        wrap_id = content_wrapper.group(1)
        print(f"\n  First container: #{wrap_id}")
        wrap_css = re.findall(f'#{wrap_id}\\s*{{([^}}]+)}}', all_css)
        if wrap_css:
            for rule in wrap_css:
                print(f"    CSS: {rule.strip()[:200]}")

    # Find the #brx-content wrapper
    brx_content = re.search(r'<div[^>]*id="brx-content"[^>]*>', html)
    if brx_content:
        print(f"\n  #brx-content found at char {brx_content.start()}")
        brx_css = re.findall(r'#brx-content\s*{([^}]+)}', all_css)
        if brx_css:
            for rule in brx_css:
                print(f"    CSS: {rule.strip()[:200]}")
        else:
            print(f"    No specific CSS for #brx-content")
