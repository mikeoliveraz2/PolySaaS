"""Fix investor page v2 — explicit light/dark colors, unmissable toggle."""
import requests, sys
sys.stdout.reconfigure(encoding='utf-8')

AZURE = "https://azure-nightingale-589250.hostingersite.com"
s = requests.Session()
s.auth = ("mikeoliveraz@gmail.com", "vlop MpGU Os2V xDSI C6T7 2fAN")

PAGE_ID = 2565
BUSINESS_PLAN = "https://docs.google.com/document/d/1-rWJ3GkgCWwbFOmfuOPkGUaleSmpzpAadXHZWqkwzGw/edit?usp=sharing"
SAFE_DOC = "https://docs.google.com/document/d/1ZlwiyUKPR4ezu_dowuQZe0h0IwDIZExt/edit?usp=sharing&ouid=117986726904510989322&rtpof=true&sd=true"
PITCH_DECK = "https://docs.google.com/presentation/d/10aJicMPNOGaJF8sRUtNpXuVbes0BrKwP/edit?usp=sharing&ouid=117986726904510989322&rtpof=true&sd=true"

content = f'''<!-- wp:html --><style>
/* === LIGHT MODE (default) — explicit dark text on white === */
.inv-section, .inv-hero, .inv-cta, .inv-disclaimer {{
    color: #1F2937 !important;
}}
.inv-hero h1 {{ font-size: 2rem; font-weight: 700; color: #2563EB !important; margin-bottom: 8px; }}
.inv-hero .inv-subtitle {{ font-size: 1.1rem; color: #4B5563 !important; font-style: italic; }}
.inv-tagline {{ font-size: 1.05rem; line-height: 1.7; color: #1F2937 !important; text-align: center; max-width: 780px; margin: 0 auto 24px; }}
.inv-tagline strong {{ color: #111827 !important; }}
.inv-h2 {{ font-size: 1.5rem; font-weight: 600; color: #2563EB !important; margin-bottom: 16px; padding-bottom: 8px; border-bottom: 2px solid rgba(37,99,235,0.2); }}
.inv-h3 {{ font-size: 1.15rem; font-weight: 600; color: #1F2937 !important; margin-bottom: 8px; }}
.inv-text {{ font-size: 0.95rem; line-height: 1.7; color: #374151 !important; margin-bottom: 16px; }}
.inv-text strong {{ color: #111827 !important; }}
.inv-feature-text strong {{ color: #1F2937 !important; font-size: 1rem; }}
.inv-feature-text span {{ font-size: 0.9rem; color: #4B5563 !important; }}
.inv-card {{ background: #FFFFFF; border: 1px solid #E5E7EB; border-radius: 10px; padding: 24px; box-shadow: 0 2px 8px rgba(0,0,0,0.04); }}
.inv-card h3 {{ font-size: 1.1rem; font-weight: 600; color: #2563EB !important; margin-bottom: 6px; }}
.inv-card p {{ font-size: 0.9rem; line-height: 1.6; color: #4B5563 !important; margin-bottom: 0; }}
.inv-pricing-card {{ background: #FFFFFF; border: 1px solid #E5E7EB; border-radius: 10px; padding: 24px; text-align: center; }}
.inv-pricing-card.featured {{ border-color: #2563EB; box-shadow: 0 0 20px rgba(37,99,235,0.1); }}
.inv-pricing-card h3 {{ color: #2563EB !important; font-size: 1.1rem; margin-bottom: 8px; }}
.inv-pricing-card .price {{ font-size: 1.8rem; font-weight: 700; color: #111827 !important; margin-bottom: 4px; }}
.inv-pricing-card .price span {{ font-size: 0.85rem; font-weight: 400; color: #6B7280 !important; }}
.inv-pricing-card ul {{ text-align: left; list-style: none; padding: 0; margin: 12px 0 0; }}
.inv-pricing-card ul li {{ font-size: 0.85rem; color: #4B5563 !important; padding: 4px 0 4px 20px; position: relative; }}
.inv-pricing-card ul li::before {{ content: "\\2713"; position: absolute; left: 0; color: #0F766E; font-weight: 700; }}
.inv-traction-text {{ font-size: 0.9rem; color: #1F2937 !important; line-height: 1.6; }}
.inv-traction-bullet {{ flex-shrink: 0; width: 8px; height: 8px; background: #0F766E; border-radius: 50%; margin-top: 7px; }}
.inv-safe-item {{ background: #FFFFFF; border: 1px solid #E5E7EB; border-radius: 8px; padding: 16px; text-align: center; }}
.inv-safe-item .val {{ font-size: 1.3rem; font-weight: 700; color: #111827 !important; }}
.inv-safe-item .lbl {{ font-size: 0.8rem; color: #4B5563 !important; margin-top: 4px; }}
.inv-fund-bar {{ background: #FFFFFF; border: 1px solid #E5E7EB; border-radius: 10px; padding: 20px; text-align: center; }}
.inv-fund-bar .pct {{ font-size: 2rem; font-weight: 700; color: #2563EB !important; }}
.inv-fund-bar .label {{ font-size: 0.85rem; color: #4B5563 !important; margin-top: 4px; }}
.inv-doc-card {{ background: #FFFFFF; border: 1px solid #E5E7EB; border-radius: 10px; padding: 20px; text-align: center; transition: border-color 0.2s, box-shadow 0.2s; }}
.inv-doc-card:hover {{ border-color: #2563EB; box-shadow: 0 4px 16px rgba(37,99,235,0.08); }}
.inv-doc-card .doc-icon {{ font-size: 2rem; margin-bottom: 8px; }}
.inv-doc-card h4 {{ font-size: 1rem; font-weight: 600; color: #1F2937 !important; margin-bottom: 6px; }}
.inv-doc-card p {{ font-size: 0.8rem; color: #4B5563 !important; margin-bottom: 12px; }}
.inv-doc-card a {{ display: inline-block; background: #2563EB; color: #fff !important; padding: 8px 20px; border-radius: 6px; text-decoration: none; font-size: 0.85rem; font-weight: 500; }}
.inv-doc-card a:hover {{ background: #1D4ED8; }}
.inv-cta h2 {{ font-size: 1.4rem; font-weight: 600; color: #2563EB !important; margin-bottom: 12px; }}
.inv-cta p {{ font-size: 0.95rem; color: #374151 !important; margin-bottom: 8px; }}
.inv-cta a {{ color: #2563EB !important; text-decoration: none; font-weight: 500; }}
.inv-cta strong {{ color: #111827 !important; }}
.inv-disclaimer {{ font-size: 0.75rem; color: #6B7280 !important; line-height: 1.6; max-width: 780px; margin: 0 auto; text-align: center; padding: 16px 24px 32px; }}
.inv-disclaimer strong {{ color: #374151 !important; }}
.inv-badge {{ display: inline-block; background: rgba(37,99,235,0.1); color: #2563EB !important; font-size: 0.75rem; font-weight: 600; padding: 4px 12px; border-radius: 20px; margin-bottom: 16px; letter-spacing: 0.5px; text-transform: uppercase; }}
.inv-divider {{ border: none; border-top: 1px solid #E5E7EB; margin: 32px 0; }}

/* === DARK MODE — override all to light text on dark bg === */
body.dark-mode .entry-content-wrap {{ background-color: #0F172A !important; }}
body.dark-mode .entry-hero-section,
body.dark-mode .entry-hero-container-inner {{ background-color: #0F172A !important; }}
body.dark-mode .inv-section, body.dark-mode .inv-hero, body.dark-mode .inv-cta {{ color: #F1F5F9 !important; }}
body.dark-mode .inv-hero h1 {{ color: #60A5FA !important; }}
body.dark-mode .inv-hero .inv-subtitle {{ color: #94A3B8 !important; }}
body.dark-mode .inv-tagline {{ color: #E2E8F0 !important; }}
body.dark-mode .inv-tagline strong {{ color: #F1F5F9 !important; }}
body.dark-mode .inv-h2 {{ color: #60A5FA !important; border-bottom-color: rgba(96,165,250,0.2); }}
body.dark-mode .inv-h3 {{ color: #E2E8F0 !important; }}
body.dark-mode .inv-text {{ color: #CBD5E1 !important; }}
body.dark-mode .inv-text strong {{ color: #F1F5F9 !important; }}
body.dark-mode .inv-feature-text strong {{ color: #E2E8F0 !important; }}
body.dark-mode .inv-feature-text span {{ color: #94A3B8 !important; }}
body.dark-mode .inv-feature-icon {{ background: #334155; }}
body.dark-mode .inv-card {{ background: #1E293B; border-color: #334155; box-shadow: 0 2px 8px rgba(0,0,0,0.3); }}
body.dark-mode .inv-card h3 {{ color: #60A5FA !important; }}
body.dark-mode .inv-card p {{ color: #94A3B8 !important; }}
body.dark-mode .inv-pricing-card {{ background: #1E293B; border-color: #334155; }}
body.dark-mode .inv-pricing-card.featured {{ border-color: #60A5FA; box-shadow: 0 0 20px rgba(96,165,250,0.15); }}
body.dark-mode .inv-pricing-card h3 {{ color: #60A5FA !important; }}
body.dark-mode .inv-pricing-card .price {{ color: #F1F5F9 !important; }}
body.dark-mode .inv-pricing-card .price span {{ color: #94A3B8 !important; }}
body.dark-mode .inv-pricing-card ul li {{ color: #CBD5E1 !important; }}
body.dark-mode .inv-pricing-card ul li::before {{ color: #5EEAD4; }}
body.dark-mode .inv-traction-text {{ color: #E2E8F0 !important; }}
body.dark-mode .inv-traction-bullet {{ background: #5EEAD4; }}
body.dark-mode .inv-safe-item {{ background: #1E293B; border-color: #334155; }}
body.dark-mode .inv-safe-item .val {{ color: #F1F5F9 !important; }}
body.dark-mode .inv-safe-item .lbl {{ color: #94A3B8 !important; }}
body.dark-mode .inv-fund-bar {{ background: #1E293B; border-color: #334155; }}
body.dark-mode .inv-fund-bar .pct {{ color: #60A5FA !important; }}
body.dark-mode .inv-fund-bar .label {{ color: #94A3B8 !important; }}
body.dark-mode .inv-doc-card {{ background: #1E293B; border-color: #334155; }}
body.dark-mode .inv-doc-card:hover {{ border-color: #60A5FA; }}
body.dark-mode .inv-doc-card h4 {{ color: #E2E8F0 !important; }}
body.dark-mode .inv-doc-card p {{ color: #94A3B8 !important; }}
body.dark-mode .inv-cta h2 {{ color: #60A5FA !important; }}
body.dark-mode .inv-cta p {{ color: #CBD5E1 !important; }}
body.dark-mode .inv-cta a {{ color: #60A5FA !important; }}
body.dark-mode .inv-cta strong {{ color: #F1F5F9 !important; }}
body.dark-mode .inv-disclaimer {{ color: #64748B !important; }}
body.dark-mode .inv-disclaimer strong {{ color: #94A3B8 !important; }}
body.dark-mode .inv-badge {{ background: rgba(96,165,250,0.15); color: #60A5FA !important; }}
body.dark-mode .inv-divider {{ border-top-color: #334155; }}

/* Dark mode site chrome */
body.dark-mode .header-navigation .menu > li > a,
body.dark-mode .header-navigation .menu > li > a:visited {{ color: #F1F5F9 !important; }}
body.dark-mode .header-navigation .menu > li.current-menu-item > a {{ color: #60A5FA !important; }}
body.dark-mode .site-branding .site-title,
body.dark-mode .site-branding .site-title a {{ color: #60A5FA !important; }}
body.dark-mode #masthead,
body.dark-mode .site-header,
body.dark-mode .site-header-inner-wrap {{ background-color: #1E293B !important; }}
body.dark-mode h1, body.dark-mode h2, body.dark-mode h3,
body.dark-mode h4, body.dark-mode h5, body.dark-mode h6 {{ color: #60A5FA !important; }}
body.dark-mode .wp-block-group[style*="background-color"],
body.dark-mode div[style*="background-color:#F3F4F6"],
body.dark-mode div[style*="background-color:#f3f4f6"] {{ background-color: #1E293B !important; }}

/* Layout */
.inv-section {{ max-width: 900px; margin: 0 auto; padding: 32px 24px; }}
.inv-hero {{ text-align: center; padding: 48px 24px 32px; }}
.inv-grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(260px, 1fr)); gap: 16px; margin-bottom: 24px; }}
.inv-feature {{ display: flex; gap: 12px; align-items: flex-start; margin-bottom: 14px; }}
.inv-feature-icon {{ flex-shrink: 0; width: 32px; height: 32px; background: #E5E7EB; border-radius: 8px; display: flex; align-items: center; justify-content: center; font-size: 1rem; }}
.inv-pricing-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(240px, 1fr)); gap: 20px; margin-bottom: 24px; }}
.inv-docs {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(240px, 1fr)); gap: 16px; margin-bottom: 24px; }}
.inv-use-funds {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 16px; margin-bottom: 24px; }}
@media (max-width: 700px) {{ .inv-use-funds {{ grid-template-columns: 1fr; }} }}
.inv-traction-item {{ display: flex; gap: 10px; align-items: flex-start; margin-bottom: 12px; }}
.inv-safe-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 16px; margin-bottom: 20px; }}
@media (max-width: 600px) {{ .inv-safe-grid {{ grid-template-columns: 1fr; }} }}
.inv-cta {{ text-align: center; padding: 32px 24px; }}

/* Header logo */
.site-branding a.brand img, .site-branding a.brand img.custom-logo,
#masthead .site-branding a.brand img {{ max-width: 60px !important; max-height: 60px !important; width: auto !important; height: auto !important; }}
.site-branding .brand {{ max-width: 80px !important; }}
.mobile-site-branding a.brand img {{ max-width: 50px !important; max-height: 50px !important; }}

/* Whitespace */
.content-area {{ margin-top: 0 !important; padding-top: 0 !important; }}
.entry-content-wrap {{ padding-top: 0 !important; margin-top: 0 !important; }}
.entry-hero-container-inner {{ padding: 0 !important; min-height: 0 !important; }}
.entry-hero .entry-header {{ min-height: 0 !important; padding: 5px 0 !important; margin: 0 !important; }}
.site-main {{ padding-top: 0 !important; margin-top: 0 !important; }}
.site-content {{ padding-top: 0 !important; }}
.entry-content {{ margin-top: 0 !important; padding-top: 0 !important; }}
.entry-title {{ margin-top: 0 !important; padding-top: 5px !important; margin-bottom: 5px !important; }}
header.entry-header {{ padding-top: 0 !important; padding-bottom: 0 !important; }}
.page .entry-header {{ padding: 5px 0 !important; margin: 0 !important; min-height: 0 !important; }}

/* Toggle button — high visibility */
#ps-dark-toggle {{
    position: fixed !important;
    top: 15px !important;
    right: 20px !important;
    z-index: 99999 !important;
    background: #FFFFFF !important;
    border: 2px solid #2563EB !important;
    border-radius: 50%;
    width: 44px;
    height: 44px;
    cursor: pointer;
    font-size: 20px;
    display: flex !important;
    align-items: center;
    justify-content: center;
    box-shadow: 0 2px 12px rgba(0,0,0,0.2) !important;
    transition: all 0.3s ease;
    color: #001F3F !important;
}}
body.dark-mode #ps-dark-toggle {{
    background: #1E293B !important;
    border-color: #60A5FA !important;
    color: #F1F5F9 !important;
    box-shadow: 0 2px 12px rgba(0,0,0,0.4) !important;
}}
</style><!-- /wp:html -->

<!-- wp:html -->
<button id="ps-dark-toggle" onclick="document.body.classList.toggle('dark-mode');localStorage.setItem('ps-dark-mode',document.body.classList.contains('dark-mode'));var i=document.getElementById('ps-toggle-icon');var dm=document.body.classList.contains('dark-mode');if(i)i.innerHTML=dm?'\\u2600':'\\u263E';this.title=dm?'Switch to light mode':'Switch to dark mode';" aria-label="Toggle dark mode" title="Switch to dark mode"><span id="ps-toggle-icon">&#9790;</span></button>
<script>
(function(){{var s=localStorage.getItem('ps-dark-mode');var b=document.getElementById('ps-dark-toggle');if(s==='true'){{document.body.classList.add('dark-mode');var i=document.getElementById('ps-toggle-icon');if(i)i.innerHTML='\\u2600';if(b)b.title='Switch to light mode';}}else{{if(b)b.title='Switch to dark mode';}}}})();
</script>
<!-- /wp:html -->

<!-- wp:html -->
<div class="inv-hero">
  <span class="inv-badge">Confidential &mdash; March 2026</span>
  <h1>PolySaaS Private Investor Overview</h1>
  <p class="inv-subtitle">Bridge Raise &mdash; SAFE (YC Post-Money Template)</p>
</div>
<!-- /wp:html -->

<!-- wp:html -->
<div class="inv-section">
  <p class="inv-tagline"><strong>Industrial Strength SaaS for Limitless Horizons.</strong><br>
  PolySaaS delivers a unified, no-code orchestration layer that turns enterprise open-source applications into collaborative peers &mdash; eliminating SaaS sprawl, manual syncs, and expensive custom development.</p>
</div>
<!-- /wp:html -->

<!-- wp:html -->
<div class="inv-section">
  <h2 class="inv-h2">&#127919; The Opportunity</h2>
  <p class="inv-text">Enterprises and mid-market teams run dozens of tools in silos. Traditional SaaS is rigid and costly to customize. PolySaaS solves this with:</p>

  <div class="inv-feature">
    <div class="inv-feature-icon">&#9889;</div>
    <div class="inv-feature-text">
      <strong>Dynamic Orchestration</strong><br>
      <span>No-code workflows via Atomic Services &mdash; connect apps, automate data flows, trigger real-time actions across the stack.</span>
    </div>
  </div>

  <div class="inv-feature">
    <div class="inv-feature-icon">&#129309;</div>
    <div class="inv-feature-text">
      <strong>Apps as Peers</strong><br>
      <span>No hierarchy; applications share data and collaborate dynamically.</span>
    </div>
  </div>

  <div class="inv-feature">
    <div class="inv-feature-icon">&#129302;</div>
    <div class="inv-feature-text">
      <strong>AI as Peers</strong><br>
      <span>Intelligent agents (Grok, Gemini, etc.) join Mattermost chats, suggest improvements, automate decisions, and integrate into custom workflows.</span>
    </div>
  </div>

  <div class="inv-feature">
    <div class="inv-feature-icon">&#128269;</div>
    <div class="inv-feature-text">
      <strong>PolySniffer</strong><br>
      <span>Passive traffic monitoring for zero-code integration discovery.</span>
    </div>
  </div>

  <div class="inv-feature">
    <div class="inv-feature-icon">&#9729;&#65039;</div>
    <div class="inv-feature-text">
      <strong>Scalable Architecture</strong><br>
      <span>Multi-tenant microservices on Google Cloud with Kubernetes auto-scaling, unified SSO, and billing.</span>
    </div>
  </div>
</div>
<!-- /wp:html -->

<!-- wp:html -->
<div class="inv-section">
  <h2 class="inv-h2">&#128230; Bundled Enterprise-Grade Applications</h2>
  <p class="inv-text">All apps run as peers in a single subscription &mdash; instant provisioning, unified dashboard, and full orchestration on the Unlimited tier.</p>

  <div class="inv-grid">
    <div class="inv-card"><h3>Odoo</h3><p>Comprehensive ERP &amp; CRM for streamlined operations, sales, and project management at enterprise scale.</p></div>
    <div class="inv-card"><h3>Nextcloud</h3><p>Secure file storage and collaboration with full control over sharing and data privacy.</p></div>
    <div class="inv-card"><h3>Mattermost</h3><p>Real-time team messaging enhanced with AI peers for secure, productive workflows.</p></div>
    <div class="inv-card"><h3>WordPress</h3><p>Flexible content management for blogs, websites, and dynamic publishing.</p></div>
    <div class="inv-card"><h3>Liferay</h3><p>Robust enterprise portal delivering personalized content and seamless user experiences.</p></div>
    <div class="inv-card"><h3>Dolibarr</h3><p>Modular ERP and invoicing system for efficient inventory and customer relationship handling.</p></div>
    <div class="inv-card"><h3>Monitor Logger</h3><p>Advanced logging and monitoring to detect issues and gain actionable system insights.</p></div>
    <div class="inv-card"><h3>PolySysMon</h3><p>Continuous performance and health tracking ensuring reliability across the entire stack.</p></div>
  </div>
</div>
<!-- /wp:html -->

<!-- wp:html -->
<div class="inv-section">
  <h2 class="inv-h2">&#128176; Pricing Tiers (Live on Platform)</h2>
  <div class="inv-pricing-grid">
    <div class="inv-pricing-card">
      <h3>Starter</h3>
      <div class="price">$29<span>/mo per user</span></div>
      <ul><li>Any one application</li><li>SSO &amp; unified billing</li><li>Standard support</li></ul>
    </div>
    <div class="inv-pricing-card">
      <h3>Team</h3>
      <div class="price">$49<span>/mo per user</span></div>
      <ul><li>Any three applications</li><li>Dashboard access</li><li>Priority support</li></ul>
    </div>
    <div class="inv-pricing-card featured">
      <h3>Unlimited</h3>
      <div class="price">$99<span>/mo per user</span></div>
      <ul><li>Full suite access</li><li>Orchestration &amp; AI Peers</li><li>Enterprise support</li></ul>
    </div>
  </div>
</div>
<!-- /wp:html -->

<!-- wp:html -->
<div class="inv-section">
  <h2 class="inv-h2">&#128200; Traction &amp; Momentum</h2>
  <div class="inv-traction-item"><div class="inv-traction-bullet"></div><div class="inv-traction-text">Growing waitlist of qualified SMBs and enterprises (50&ndash;500 seats).</div></div>
  <div class="inv-traction-item"><div class="inv-traction-bullet"></div><div class="inv-traction-text">Signed LOIs signaling strong path to ARR post-hard launch.</div></div>
  <div class="inv-traction-item"><div class="inv-traction-bullet"></div><div class="inv-traction-text">MVP live: Real-time event-driven flows, Atomic Services executing cross-app automations, OpenAPI docs available.</div></div>
  <div class="inv-traction-item"><div class="inv-traction-bullet"></div><div class="inv-traction-text">Advisors: John Shackleton (confirmed); additional advisors (Francis &amp; Bento) pending final confirmation.</div></div>
</div>
<!-- /wp:html -->

<!-- wp:html -->
<div class="inv-section">
  <h2 class="inv-h2">&#128188; The Ask &mdash; Bridge Raise</h2>
  <p class="inv-text">We are raising a small bridge round via <strong>SAFE (YC post-money template)</strong> to fund the final sprint to public MVP polish, GTM activation (Product Hunt, partnerships, Liferay/Django channels), and first engineer hire.</p>

  <div class="inv-safe-grid">
    <div class="inv-safe-item"><div class="val">$5M</div><div class="lbl">Valuation Cap (post-money, negotiable)</div></div>
    <div class="inv-safe-item"><div class="val">20%</div><div class="lbl">Discount to next priced round</div></div>
    <div class="inv-safe-item"><div class="val">$2K&ndash;$10K</div><div class="lbl">Minimum check (flexible)</div></div>
    <div class="inv-safe-item"><div class="val">SAFE</div><div class="lbl">YC post-money template</div></div>
  </div>

  <h3 class="inv-h3">Use of Funds</h3>
  <div class="inv-use-funds">
    <div class="inv-fund-bar"><div class="pct">40%</div><div class="label">Public MVP polish &amp; GCP/Kubernetes scaling</div></div>
    <div class="inv-fund-bar"><div class="pct">30%</div><div class="label">Go-to-market (Product Hunt, channel partnerships)</div></div>
    <div class="inv-fund-bar"><div class="pct">30%</div><div class="label">First engineer &mdash; Atomic Services &amp; AI Peers</div></div>
  </div>
</div>
<!-- /wp:html -->

<!-- wp:html -->
<div class="inv-section">
  <h2 class="inv-h2">&#128196; Documents (Confidential)</h2>
  <p class="inv-text" style="text-align:center;margin-bottom:20px;">For discussion purposes only. Additional data room items available on request.</p>

  <div class="inv-docs">
    <div class="inv-doc-card">
      <div class="doc-icon">&#128203;</div>
      <h4>Business Plan</h4>
      <p>Full strategy, financial projections, market analysis</p>
      <a href="{BUSINESS_PLAN}" target="_blank" rel="noopener">View Document</a>
    </div>
    <div class="inv-doc-card">
      <div class="doc-icon">&#127916;</div>
      <h4>Pitch Deck</h4>
      <p>12&ndash;15 slide overview: problem, solution, traction, market, team, ask</p>
      <a href="{PITCH_DECK}" target="_blank" rel="noopener">View Deck</a>
    </div>
    <div class="inv-doc-card">
      <div class="doc-icon">&#128221;</div>
      <h4>SAFE Agreement</h4>
      <p>Standard YC post-money SAFE (customized; DocuSign per investor)</p>
      <a href="{SAFE_DOC}" target="_blank" rel="noopener">View Document</a>
    </div>
  </div>
</div>
<!-- /wp:html -->

<!-- wp:html -->
<hr class="inv-divider">
<div class="inv-cta">
  <h2>Interested in a Quick 15-Minute Call?</h2>
  <p>This page is private and shared only with select contacts under Regulation D (no general solicitation).</p>
  <p style="margin-top:16px;">
    <strong>Michael Oliver</strong><br>
    Founder &amp; Lead Architect<br><br>
    &#9993; <a href="mailto:michael.oliver@polysaas.online">michael.oliver@polysaas.online</a><br>
    &#128222; +1-713-913-0434<br>
    <a href="https://www.linkedin.com/in/mikeolivero4bo/" target="_blank" rel="noopener">LinkedIn &rarr;</a>
  </p>
</div>
<!-- /wp:html -->

<!-- wp:html -->
<div class="inv-disclaimer">
  <strong>Disclaimer:</strong> Materials provided for discussion purposes only. This is not an offer to sell securities or a solicitation of an offer to buy securities. Any investment would be made pursuant to a separate SAFE agreement and subject to applicable securities laws. Past performance is not indicative of future results. Investing involves significant risk, including possible loss of principal.
</div>
<!-- /wp:html -->

<!-- wp:html -->
<div style="max-width:1200px;margin:20px auto 0;background:#111827;padding:28px 32px 22px;border-top:3px solid #0F766E;">
<div style="display:flex;flex-wrap:wrap;gap:40px;justify-content:space-between;align-items:flex-start;">
<div style="flex:1 1 280px;min-width:200px;">
<p style="font-weight:700;font-size:1rem;color:#E5E7EB;margin-bottom:6px;">PolySaaS Online</p>
<p style="color:#9CA3AF;font-size:0.82rem;line-height:1.6;margin:0;">
<strong style="color:#CBD5E1;">Stop Managing Tools. Start Orchestrating Them.</strong><br>
Join enterprises already running smarter with PolySaaS.<br><br>
5900 Balcones Drive Suite 100<br>Austin, TX 78731<br><br>
<a href="mailto:michael.oliver@polysaas.online" style="color:#2DD4BF;text-decoration:none;">michael.oliver@polysaas.online</a><br>
+1-713-913-0434 &nbsp;|&nbsp; +63-947-992-7462
</p>
</div>
<div style="flex:0 1 200px;min-width:140px;">
<p style="font-weight:600;font-size:0.85rem;color:#E5E7EB;margin-bottom:8px;">Quick Links</p>
<p style="margin:0;line-height:2;">
<a href="/about-us/" style="color:#9CA3AF;text-decoration:none;font-size:0.82rem;">About Us</a><br>
<a href="/pricing/" style="color:#9CA3AF;text-decoration:none;font-size:0.82rem;">Pricing</a><br>
<a href="/sign-up/" style="color:#9CA3AF;text-decoration:none;font-size:0.82rem;">Sign Up</a>
</p>
</div>
<div style="flex:0 1 260px;min-width:160px;">
<p style="font-weight:600;font-size:0.85rem;color:#E5E7EB;margin-bottom:8px;">Legal</p>
<p style="margin:0;line-height:2;">
<a href="/privacy-policy/" style="color:#9CA3AF;text-decoration:none;font-size:0.82rem;">Privacy Policy</a><br>
<a href="/terms-of-service/" style="color:#9CA3AF;text-decoration:none;font-size:0.82rem;">Terms of Service</a><br>
<a href="/disclaimer/" style="color:#9CA3AF;text-decoration:none;font-size:0.82rem;">Disclaimer</a>
</p>
</div>
</div>
</div>
<!-- /wp:html -->'''

print(f"Content length: {len(content)} chars")

r2 = s.post(f"{AZURE}/wp-json/wp/v2/pages/{PAGE_ID}", json={"content": content}, timeout=60)
print(f"Update status: {r2.status_code}")
if r2.status_code == 200:
    print("SUCCESS — Investor page fixed with explicit light/dark colors + visible toggle")
else:
    print(f"ERROR: {r2.text[:500]}")
