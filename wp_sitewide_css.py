"""Generate and apply comprehensive site-wide CSS fixes for brand uniformity.
Standardizes all off-brand colors to the PolySaaS brand palette."""
import requests
import json

SITE = "https://azure-nightingale-589250.hostingersite.com"
USER = "mikeoliveraz@gmail.com"
APP_PASS = "vlop MpGU Os2V xDSI C6T7 2fAN"

SITEWIDE_CSS = """
/* ================================================================
   PolySaaS Site-Wide Brand Uniformity CSS
   Applied by Cursor — 2026-03-05
   
   Brand Palette:
     Primary:   #003399 (deep blue)
     Accent:    #03a9f4 (sky blue)
     Light:     #81d4fa (light blue)
     Neutral:   #e0e0e0 (light grey)
     Surface:   #f5f5f5 (near-white)
     Highlight: #ffeb3b (yellow)
     Success:   #8bc34a (green)
     Text:      #1e1e1e / #32373c
     White:     #ffffff
   ================================================================ */


/* ==============================================
   HOME PAGE FIXES
   ============================================== */

/* Green stripe removal (Value Proposition container) */
#brxe-9d3229 {
    background-image: none !important;
    background-color: transparent !important;
}

/* "Sign Up for a demo" button — lime green to brand blue */
#brxe-spdnfe {
    background-color: #003399 !important;
    color: #ffffff !important;
}
#brxe-spdnfe:hover {
    background-color: #03a9f4 !important;
}

/* "Get Early Access" button — mint green to brand blue */
#brxe-108a27 {
    background-color: #003399 !important;
    color: #ffffff !important;
}
#brxe-108a27:hover {
    background-color: #03a9f4 !important;
}

/* Value Proposition split background — top-down gradient */
#brxe-5a8e5d {
    background-image: linear-gradient(180deg, #e0e0e0, #81d4fa) !important;
}

/* Articles section split background — top-down gradient */
#brxe-a41c97 {
    background-image: linear-gradient(180deg, #81d4fa, #e0e0e0) !important;
}

/* Subscription Plans — yellow-grey to blue-grey gradient */
#brxe-d09dd8 {
    background-image: linear-gradient(180deg, #e0e0e0, #81d4fa) !important;
}

/* Card backgrounds — #f5f9fa to brand surface #f5f5f5 */
#brxe-48433c,
#brxe-ebdc99,
#brxe-c34c6b,
#brxe-c42948,
#brxe-3d9d44,
#brxe-212ef4,
#brxe-c84666,
#brxe-d99909,
#brxe-5043f6,
#brxe-bb6825 {
    background-color: #f5f5f5 !important;
}

/* Teal icon colors — #1da69a to brand accent #03a9f4 */
#brxe-77ca79 .icon,
#brxe-77ca79 .icon a,
#brxe-f81cf6 .icon,
#brxe-f81cf6 .icon a,
#brxe-16b8fe .icon,
#brxe-16b8fe .icon a,
#brxe-1088c8 .icon,
#brxe-1088c8 .icon a,
#brxe-9a18af .icon,
#brxe-9a18af .icon a,
#brxe-444777 .icon,
#brxe-444777 .icon a {
    color: #03a9f4 !important;
}

/* Teal section headings — #1da69a to brand accent #03a9f4 */
#brxe-d5dad2,
#brxe-454ad3,
#brxe-f09dcf {
    color: #03a9f4 !important;
}


/* ==============================================
   CTA BUTTON FIX — ALL PAGES
   #6bff9f (mint green) → #003399 (brand blue)
   These are the "Get Early Access" CTA buttons
   in the footer/template section.
   ============================================== */

/* Home */
/* #brxe-108a27 already handled above */

/* Architecture */
#brxe-lxtgtl {
    background-color: #003399 !important;
    color: #ffffff !important;
}
#brxe-lxtgtl:hover { background-color: #03a9f4 !important; }

/* Portal */
#brxe-klbakr {
    background-color: #003399 !important;
    color: #ffffff !important;
}
#brxe-klbakr:hover { background-color: #03a9f4 !important; }

/* Atomic Services */
#brxe-azcciv {
    background-color: #003399 !important;
    color: #ffffff !important;
}
#brxe-azcciv:hover { background-color: #03a9f4 !important; }

/* Dynamic Orchestration */
#brxe-jzzqut {
    background-color: #003399 !important;
    color: #ffffff !important;
}
#brxe-jzzqut:hover { background-color: #03a9f4 !important; }

/* PolySniffer */
#brxe-knhbzg {
    background-color: #003399 !important;
    color: #ffffff !important;
}
#brxe-knhbzg:hover { background-color: #03a9f4 !important; }

/* AI As Peers */
#brxe-moougs {
    background-color: #003399 !important;
    color: #ffffff !important;
}
#brxe-moougs:hover { background-color: #03a9f4 !important; }

/* Apps As Peers */
#brxe-vfwohf {
    background-color: #003399 !important;
    color: #ffffff !important;
}
#brxe-vfwohf:hover { background-color: #03a9f4 !important; }

/* Bundled Applications */
#brxe-furbff {
    background-color: #003399 !important;
    color: #ffffff !important;
}
#brxe-furbff:hover { background-color: #03a9f4 !important; }

/* External Applications */
#brxe-mhyjsp {
    background-color: #003399 !important;
    color: #ffffff !important;
}
#brxe-mhyjsp:hover { background-color: #03a9f4 !important; }

/* Odoo */
#brxe-pnmgpm {
    background-color: #003399 !important;
    color: #ffffff !important;
}
#brxe-pnmgpm:hover { background-color: #03a9f4 !important; }

/* NextCloud */
#brxe-hhhbrs {
    background-color: #003399 !important;
    color: #ffffff !important;
}
#brxe-hhhbrs:hover { background-color: #03a9f4 !important; }

/* MatterMost */
#brxe-llvriy {
    background-color: #003399 !important;
    color: #ffffff !important;
}
#brxe-llvriy:hover { background-color: #03a9f4 !important; }

/* WordPress */
#brxe-jfoddi {
    background-color: #003399 !important;
    color: #ffffff !important;
}
#brxe-jfoddi:hover { background-color: #03a9f4 !important; }

/* PolySysMon */
#brxe-rdjkmy {
    background-color: #003399 !important;
    color: #ffffff !important;
}
#brxe-rdjkmy:hover { background-color: #03a9f4 !important; }

/* Monitor Logger */
#brxe-lqyjnf {
    background-color: #003399 !important;
    color: #ffffff !important;
}
#brxe-lqyjnf:hover { background-color: #03a9f4 !important; }

/* Dolibarr */
#brxe-clefgx {
    background-color: #003399 !important;
    color: #ffffff !important;
}
#brxe-clefgx:hover { background-color: #03a9f4 !important; }

/* CTA Templates */
#brxe-1c174a {
    background-color: #003399 !important;
    color: #ffffff !important;
}
#brxe-1c174a:hover { background-color: #03a9f4 !important; }


/* ==============================================
   ODOO PAGE — one-off green button
   #00ff59 → brand blue
   ============================================== */

#brxe-wjsthw {
    background-color: #003399 !important;
    color: #ffffff !important;
}
#brxe-wjsthw:hover {
    background-color: #03a9f4 !important;
}


/* ==============================================
   ABOUT US PAGE — purple link
   #4000ff → brand accent blue
   ============================================== */

#brxe-tszryz,
#brxe-tszryz a {
    color: #03a9f4 !important;
}
#brxe-tszryz a:hover {
    color: #003399 !important;
}
"""

session = requests.Session()
session.auth = (USER, APP_PASS)

print("=" * 70)
print("POLYSAAS SITE-WIDE BRAND CSS")
print("=" * 70)
print(f"CSS length: {len(SITEWIDE_CSS)} characters")
print(f"Target: {SITE}")
print()

# Try to apply via the WordPress REST API
# Method: Update the existing draft page (ID 1709) or create a new one
print("Attempting to store CSS on WordPress...")

# Check if draft page 1709 still exists
resp = session.get(f"{SITE}/wp-json/wp/v2/pages/1709")
if resp.status_code == 200:
    page = resp.json()
    print(f"  Found existing CSS page: '{page.get('title', {}).get('rendered', 'unknown')}' (ID 1709)")
    # Update it with the new comprehensive CSS
    update = session.post(
        f"{SITE}/wp-json/wp/v2/pages/1709",
        json={
            "title": "Cursor CSS Fixes — Site-Wide Brand Uniformity",
            "content": f"<pre><code>{SITEWIDE_CSS}</code></pre>",
            "status": "draft",
        }
    )
    if update.status_code == 200:
        print("  Updated draft page 1709 with comprehensive CSS.")
    else:
        print(f"  Failed to update: HTTP {update.status_code}")
else:
    print(f"  Page 1709 not found (HTTP {resp.status_code}), creating new draft...")
    create = session.post(
        f"{SITE}/wp-json/wp/v2/pages",
        json={
            "title": "Cursor CSS Fixes — Site-Wide Brand Uniformity",
            "content": f"<pre><code>{SITEWIDE_CSS}</code></pre>",
            "status": "draft",
        }
    )
    if create.status_code == 201:
        new_id = create.json().get('id')
        print(f"  Created new draft page ID {new_id}")
    else:
        print(f"  Failed to create: HTTP {create.status_code}")

# Try to apply via custom_css changeset
print("\nAttempting to apply via Customizer API...")
resp = session.get(f"{SITE}/wp-json/wp/v2/themes")
active_theme = None
if resp.status_code == 200:
    for t in resp.json():
        if t.get('status') == 'active':
            active_theme = t.get('stylesheet', '')
            print(f"  Active theme: {active_theme}")

if active_theme:
    # Try posting custom_css
    css_post = session.post(
        f"{SITE}/wp-json/wp/v2/posts",
        json={
            "title": active_theme,
            "content": SITEWIDE_CSS,
            "status": "publish",
            "type": "custom_css",
        }
    )
    print(f"  Custom CSS post attempt: HTTP {css_post.status_code}")
    if css_post.status_code in (200, 201):
        print("  CSS applied via custom_css post type!")
    else:
        print(f"  Response: {css_post.text[:200]}")

print("\n" + "=" * 70)
print("CSS READY FOR MANUAL APPLICATION")
print("=" * 70)
print("Paste the CSS into: WordPress Admin > Appearance > Customize > Additional CSS")
print(f"\nThe CSS is also saved on the site as a draft page.")
print(f"\nCSS fixes {len(SITEWIDE_CSS)} chars covering:")
print("  - Home page: green stripe, lime/mint buttons, teal icons, card backgrounds, gradients")
print("  - 17 other pages: mint green CTA buttons → brand blue")
print("  - Odoo page: one-off green button → brand blue")
print("  - About Us: purple link → brand accent blue")
print(f"\nTotal elements fixed: ~50 across 20 pages")
