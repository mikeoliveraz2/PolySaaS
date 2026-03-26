"""
Add dark mode toggle and dark mode CSS overrides to the Cross-App Sync page on polysaas.online.
"""
import requests, sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

BASE = "https://polysaas.online"
s = requests.Session()
s.auth = ("mikeoliveraz@gmail.com", "vlop MpGU Os2V xDSI C6T7 2fAN")

r = s.get(BASE + "/wp-json/wp/v2/pages", params={
    "slug": "cross-app-sync", "context": "edit", "_fields": "id,content"
})
pages = r.json()
if not pages:
    print("Cross-App Sync page not found!")
    sys.exit(1)

page = pages[0]
pid = page['id']
content = page['content']['raw']
print(f"Page found: id={pid}")

# The toggle button + script (same as all other pages)
TOGGLE_BLOCK = '''<!-- wp:html -->
<button class="ps-theme-toggle" id="ps-dark-toggle" onclick="document.body.classList.toggle('dark-mode');localStorage.setItem('ps-dark-mode',document.body.classList.contains('dark-mode'));var i=document.getElementById('ps-toggle-icon');var dm=document.body.classList.contains('dark-mode');if(i)i.innerHTML=dm?'\\u2600':'\\u263E';this.title=dm?'Switch to light mode':'Switch to dark mode';" aria-label="Toggle dark mode" title="Switch to dark mode" style="position:fixed;top:90px;right:20px;z-index:9999;background:var(--ps-card-bg,#f0f0f0);border:2px solid #94a3b8;border-radius:50%;width:44px;height:44px;cursor:pointer;font-size:20px;display:flex;align-items:center;justify-content:center;box-shadow:0 2px 12px rgba(0,0,0,0.15);transition:all 0.3s ease;color:var(--ps-primary,#001F3F);"><span id="ps-toggle-icon">&#9790;</span></button>
<script>
(function(){var s=localStorage.getItem('ps-dark-mode');var b=document.getElementById('ps-dark-toggle');if(s==='true'){document.body.classList.add('dark-mode');var i=document.getElementById('ps-toggle-icon');if(i)i.innerHTML='\\u2600';if(b)b.title='Switch to light mode';}else{if(b)b.title='Switch to dark mode';}})();
</script>
<!-- /wp:html -->

'''

# Dark mode CSS for the cross-app sync page-specific classes
DARK_MODE_CSS = '''
/* Dark mode overrides for Cross-App Sync page */
body.dark-mode {
  --ps-primary: #60A5FA;
  --ps-accent: #93C5FD;
  --ps-text: #F1F5F9;
  --ps-text-muted: #CBD5E1;
  --ps-card-bg: #1E293B;
  --ps-border: #334155;
  --ps-success: #34D399;
  --ps-bg: #0F172A;
}
body.dark-mode .cas-step {
  background: #1E293B;
  border-color: #334155;
}
body.dark-mode .cas-step h3 {
  color: #60A5FA;
}
body.dark-mode .cas-step p,
body.dark-mode .cas-step .caption {
  color: #CBD5E1;
}
body.dark-mode .cas-flow {
  background: linear-gradient(135deg, #0F172A 0%, #1E293B 100%);
  border: 1px solid #334155;
}
body.dark-mode .cas-mapping {
  background: #1E293B;
  border-left-color: #60A5FA;
}
body.dark-mode .cas-mapping h4 {
  color: #60A5FA;
}
body.dark-mode .cas-mapping code {
  background: #334155;
  color: #93C5FD;
}
body.dark-mode .cas-table th {
  background: #1E3A5F;
}
body.dark-mode .cas-table td {
  color: #F1F5F9;
  border-bottom-color: #334155;
}
body.dark-mode .cas-table tr:nth-child(even) {
  background: #1E293B;
}
body.dark-mode .cas-table code {
  background: #334155;
  color: #93C5FD;
}
body.dark-mode .cas-badge-green { background: #064E3B; color: #6EE7B7; }
body.dark-mode .cas-badge-blue { background: #1E3A5F; color: #93C5FD; }
body.dark-mode .cas-badge-amber { background: #78350F; color: #FCD34D; }
body.dark-mode h2 { color: #60A5FA !important; }
body.dark-mode a { color: #93C5FD; }
body.dark-mode p { color: #F1F5F9; }

/* Layout overrides for dark mode (same as other pages) */
body.dark-mode .entry.single-entry,
body.dark-mode .entry-content-wrap,
body.dark-mode .content-style-boxed .entry.single-entry {
  background-color: #0F172A !important;
  background: #0F172A !important;
  box-shadow: none !important;
}
body.dark-mode #wrapper,
body.dark-mode .site,
body.dark-mode #main,
body.dark-mode .site-container,
body.dark-mode .content-area,
body.dark-mode .site-main {
  background-color: #0F172A !important;
  background: #0F172A !important;
}

/* Toggle button styling */
.ps-theme-toggle {
  border: 2px solid #94a3b8 !important;
  box-shadow: 0 2px 12px rgba(0,0,0,0.15) !important;
  background: #f0f4f8 !important;
  color: #001F3F !important;
}
body.dark-mode .ps-theme-toggle {
  border-color: #60A5FA !important;
  background: #1E293B !important;
  color: #60A5FA !important;
  box-shadow: 0 2px 12px rgba(96,165,250,0.2) !important;
}

/* Top whitespace reduction */
.content-area { margin-top: 0 !important; padding-top: 0 !important; }
.entry-content-wrap { padding-top: 0 !important; margin-top: 0 !important; max-width: 1290px !important; margin: 0 auto !important; }
.entry-hero-container-inner { padding: 0 !important; min-height: 0 !important; }
.site-main { padding-top: 0 !important; margin-top: 0 !important; }
.site-content { padding-top: 0 !important; }
.entry-content { margin-top: 0 !important; padding-top: 0 !important; }
.entry-title { margin-top: 0 !important; padding-top: 5px !important; margin-bottom: 5px !important; }
header.entry-header { padding-top: 0 !important; padding-bottom: 0 !important; }
.page .entry-header { padding: 5px 0 !important; margin: 0 !important; min-height: 0 !important; }
.entry.single-entry,
.content-style-boxed .entry.single-entry {
  max-width: 100% !important;
  margin-left: 0 !important;
  margin-right: 0 !important;
  box-shadow: none !important;
}

/* Logo size */
.site-branding a.brand img,
.site-branding a.brand img.custom-logo {
  max-width: 60px !important;
  max-height: 60px !important;
  width: auto !important;
  height: auto !important;
}
'''

# Insert dark mode CSS into the existing <style> block
if 'body.dark-mode' not in content:
    # Find the closing of the :root / existing style block
    close_style_idx = content.find('</style>')
    if close_style_idx > 0:
        content = content[:close_style_idx] + DARK_MODE_CSS + '\n' + content[close_style_idx:]
        print("  Added dark mode CSS to style block")
else:
    print("  Dark mode CSS already present")

# Insert toggle button after the first style block
if 'ps-dark-toggle' not in content:
    first_wp_end = content.find('<!-- /wp:html -->')
    if first_wp_end > 0:
        insert_at = first_wp_end + len('<!-- /wp:html -->')
        content = content[:insert_at] + '\n\n' + TOGGLE_BLOCK + content[insert_at:]
        print("  Added toggle button")
else:
    print("  Toggle button already present")

# Update page
r2 = s.post(BASE + f"/wp-json/wp/v2/pages/{pid}", json={"content": content})
if r2.status_code == 200:
    print(f"  OK: Page updated with dark mode support")
else:
    print(f"  FAILED: {r2.status_code} {r2.text[:300]}")

print(f"\nPage: {BASE}/cross-app-sync/")
print("Done.")
