"""
Build all 16 application and feature inner pages with proper content.
Each page follows a consistent template:
  - H2 page title
  - Hero description paragraph
  - Key capabilities section (3-4 points)
  - PolySaaS integration section
  - CTA
  - Shared footer + features section
"""
import requests, re, sys, json
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

from wp_snapshot import take_snapshot
take_snapshot("before building all inner pages")

AZURE = "https://azure-nightingale-589250.hostingersite.com"
s = requests.Session()
s.auth = ("mikeoliveraz@gmail.com", "vlop MpGU Os2V xDSI C6T7 2fAN")

HOME_URL = AZURE

# ============================================================
# PAGE CONTENT DEFINITIONS
# ============================================================

PAGES = {
    # ===== 8 BUNDLED APPLICATIONS =====
    "odoo": {
        "title": "Odoo",
        "subtitle": "Comprehensive ERP & CRM",
        "hero": "Odoo delivers a fully integrated suite of business applications — from CRM and sales to inventory, accounting, and project management. Within PolySaaS, Odoo becomes part of your unified platform, sharing data seamlessly with every other bundled application.",
        "capabilities": [
            ("End-to-End Business Operations", "Manage sales pipelines, purchase orders, manufacturing, HR, and accounting in a single integrated system. No more jumping between disconnected tools."),
            ("CRM & Sales Automation", "Track leads, automate follow-ups, and close deals faster with built-in CRM. Pipeline visibility from first contact to signed contract."),
            ("Inventory & Supply Chain", "Real-time stock tracking, automated reordering, and multi-warehouse management. Integrated with your sales and purchasing workflows."),
            ("Project & Timesheet Management", "Plan projects, assign tasks, track time, and bill clients — all connected to your accounting and invoicing modules."),
        ],
        "integration": "In PolySaaS, Odoo shares customer data with Mattermost for team notifications, syncs invoices with Dolibarr for dual-ledger validation, and publishes reports to your Liferay portal — all orchestrated automatically through Atomic Services.",
    },
    "nextcloud": {
        "title": "Nextcloud",
        "subtitle": "Secure File Storage & Collaboration",
        "hero": "Nextcloud provides enterprise-grade file storage, sharing, and real-time collaboration — all under your complete control. Within PolySaaS, your files are accessible from every bundled application, creating a unified document layer across your entire stack.",
        "capabilities": [
            ("Secure File Sync & Share", "Store, sync, and share files across devices with end-to-end encryption. Full control over who accesses what, with detailed audit logs."),
            ("Real-Time Collaboration", "Edit documents, spreadsheets, and presentations together in real time. Built-in Talk for video calls and chat directly from your file workspace."),
            ("Data Sovereignty", "Your files stay on your infrastructure. No third-party access, no data mining. Compliant with GDPR, HIPAA, and enterprise security requirements."),
            ("Extensible with Apps", "Hundreds of apps for calendars, contacts, mail, Kanban boards, and more. Extend Nextcloud to fit your exact workflow needs."),
        ],
        "integration": "Within PolySaaS, Nextcloud serves as the central file hub. Odoo attaches invoices directly to shared folders, Mattermost links to files in chat, and WordPress pulls media from Nextcloud — eliminating duplicate uploads and version confusion.",
    },
    "mattermost": {
        "title": "Mattermost",
        "subtitle": "Real-Time Team Messaging & AI Peers",
        "hero": "Mattermost delivers secure, enterprise-grade team messaging with channels, threads, and integrations. In PolySaaS, Mattermost is where your team collaborates — and where AI Peers join the conversation to automate decisions, surface insights, and accelerate workflows.",
        "capabilities": [
            ("Channels & Threads", "Organize conversations by team, project, or topic. Threaded discussions keep context together. Search across your entire message history instantly."),
            ("AI Peers Integration", "AI agents participate in your channels as peers — answering questions, triggering workflows, summarizing data, and suggesting actions based on real-time platform activity."),
            ("Security & Compliance", "Self-hosted messaging with full audit trails, data retention policies, and compliance exports. Your conversations never leave your infrastructure."),
            ("Webhooks & Bots", "Connect Mattermost to any system via incoming/outgoing webhooks. Build custom bots that respond to events across your PolySaaS stack."),
        ],
        "integration": "Mattermost is the collaboration hub of PolySaaS. Receive Odoo deal alerts, Nextcloud file notifications, PolySniffer traffic summaries, and PolySysMon health reports — all in dedicated channels. AI Peers turn these notifications into actionable workflows.",
    },
    "wordpress-3": {
        "title": "WordPress",
        "subtitle": "Flexible Content Management",
        "hero": "WordPress powers content creation, blogging, and dynamic website management within PolySaaS. Build landing pages, publish blog posts, manage media — all integrated with your enterprise applications and accessible through your unified portal.",
        "capabilities": [
            ("Content Management", "Create and manage pages, posts, and custom content types with the Gutenberg block editor. Full media library with image optimization."),
            ("Themes & Customization", "Thousands of themes and plugins. Customize layouts, styles, and functionality without touching code. Kadence theme included for professional design."),
            ("Multi-Site Capable", "Run multiple WordPress sites from a single installation. Perfect for multi-tenant scenarios where each customer gets their own branded content site."),
            ("REST API & Headless", "Full REST API for headless CMS use cases. Deliver WordPress content to mobile apps, SPAs, or other platforms in your PolySaaS stack."),
        ],
        "integration": "Within PolySaaS, WordPress content integrates with Liferay's portal for unified navigation, pulls media from Nextcloud for centralized asset management, and publishes updates to Mattermost channels for team awareness.",
    },
    "liferay-2": {
        "title": "Liferay",
        "subtitle": "Enterprise Portal & Personalization",
        "hero": "Liferay is the enterprise portal at the heart of PolySaaS — the unified interface where all your applications, content, and workflows come together. Personalized dashboards, role-based access, and seamless navigation across every bundled application.",
        "capabilities": [
            ("Unified Portal Experience", "One login, one dashboard. Access Odoo, Nextcloud, Mattermost, WordPress, and all other bundled applications through a single, consistent interface."),
            ("Personalization & Roles", "Deliver personalized content and application access based on user roles, departments, or tenant membership. Each user sees exactly what they need."),
            ("Widget & Fragment System", "Build custom portal pages using drag-and-drop widgets and page fragments. Embed application dashboards, charts, and data feeds without development."),
            ("Multi-Tenant Ready", "Full tenant isolation with customizable branding per organization. White-label the portal for your clients while maintaining centralized management."),
        ],
        "integration": "Liferay is the front door to PolySaaS. It aggregates content from WordPress, embeds Odoo dashboards, surfaces Mattermost conversations, and displays PolySysMon health metrics — all within personalized, role-based portal pages.",
    },
    "dolibarr-3": {
        "title": "Dolibarr",
        "subtitle": "Modular ERP & Invoicing",
        "hero": "Dolibarr provides lightweight, modular ERP and invoicing capabilities — perfect for organizations that need focused financial management without the complexity of a full ERP suite. Within PolySaaS, Dolibarr handles invoicing, proposals, and client management with seamless integration.",
        "capabilities": [
            ("Invoicing & Proposals", "Create professional invoices, quotes, and proposals. Track payment status, send reminders, and manage recurring billing with minimal setup."),
            ("Client & Contact Management", "Maintain a complete client database with contacts, addresses, and communication history. Link clients to invoices, proposals, and projects."),
            ("Inventory & Stock", "Track products, manage stock levels, and handle warehouse operations. Integrated with purchasing and sales for end-to-end supply chain visibility."),
            ("Modular Architecture", "Enable only the modules you need. Dolibarr's modular design means you start lean and add capabilities as your business grows."),
        ],
        "integration": "In PolySaaS, Dolibarr complements Odoo for organizations needing dual-ledger validation or simplified invoicing. Invoice data flows to Nextcloud for document storage, and payment notifications appear in Mattermost channels.",
    },
    "monitor-logger-4": {
        "title": "Monitor Logger",
        "subtitle": "Advanced System Logging & Monitoring",
        "hero": "Monitor Logger provides centralized logging and monitoring across your entire PolySaaS stack. Collect, aggregate, and analyze logs from every bundled application — enabling proactive issue detection, compliance auditing, and operational insights.",
        "capabilities": [
            ("Centralized Log Aggregation", "Collect logs from Odoo, Nextcloud, Mattermost, WordPress, Liferay, and all other components into a single searchable interface."),
            ("Real-Time Alerting", "Set thresholds and triggers for critical events. Receive alerts via Mattermost, email, or webhook when anomalies are detected."),
            ("Compliance & Audit Trail", "Maintain immutable audit logs for regulatory compliance. Track who did what, when, and where across your entire platform."),
            ("Dashboard & Visualization", "Visual dashboards showing log volumes, error rates, response times, and system health. Drill down from overview to individual log entries."),
        ],
        "integration": "Monitor Logger watches every application in your PolySaaS stack. Alerts route to Mattermost channels, summaries appear on Liferay portal dashboards, and PolySysMon correlates log events with performance metrics for root-cause analysis.",
    },
    "polysysmon": {
        "title": "PolySysMon",
        "subtitle": "Continuous Performance & Health Monitoring",
        "hero": "PolySysMon — built by the PolySaaS team — provides continuous performance tracking and health monitoring across your entire platform. Know the status of every application, every service, and every integration point in real time.",
        "capabilities": [
            ("Real-Time Health Dashboard", "Green/amber/red status for every bundled application and service. At-a-glance visibility into your entire platform's operational state."),
            ("Performance Metrics", "Track response times, throughput, CPU, memory, and disk usage across all components. Historical trends for capacity planning."),
            ("Automated Health Checks", "Scheduled probes verify that each application is responsive and functioning correctly. Detect failures before your users do."),
            ("Integration Monitoring", "Monitor the health of inter-application connections — API calls between Odoo and Liferay, file syncs with Nextcloud, message delivery in Mattermost."),
        ],
        "integration": "PolySysMon is purpose-built for PolySaaS. It monitors every bundled application and Atomic Service, correlates events with Monitor Logger, and surfaces health status on Liferay portal dashboards and Mattermost channels.",
    },

    # ===== 8 FEATURES =====
    "architecture": {
        "title": "Architecture",
        "subtitle": "Enterprise-Grade Cloud Infrastructure",
        "hero": "PolySaaS is built on Google Cloud Platform with Kubernetes orchestration, microservices architecture, and full multi-tenant isolation. Enterprise-grade infrastructure that scales automatically with your business — from startup to millions of users.",
        "capabilities": [
            ("Google Cloud Platform", "Hosted on GCP for global availability, automatic scaling, and enterprise security. Leveraging Cloud SQL, Cloud Storage, Cloud Run, and GKE for production workloads."),
            ("Kubernetes Orchestration", "Every bundled application runs in its own container, managed by Kubernetes. Automatic scaling, rolling updates, and self-healing ensure zero-downtime operations."),
            ("Multi-Tenant Isolation", "Each tenant gets isolated resources — separate databases, storage namespaces, and network policies. Your data never mixes with another organization's."),
            ("Microservices Architecture", "Atomic Services connect applications through well-defined APIs. Each service can be developed, deployed, and scaled independently."),
        ],
        "integration": "The architecture enables PolySaaS's core promise: multiple enterprise applications running as peers on a single platform, with data flowing securely between them through orchestrated Atomic Services — all managed by Kubernetes on GCP.",
    },
    "portal": {
        "title": "Portal",
        "subtitle": "Unified Application Interface",
        "hero": "The PolySaaS Portal — powered by Liferay — is where all your applications live behind a single interface. One login, one dashboard, fully customizable per tenant. Stop switching between tabs and logins; access everything from one place.",
        "capabilities": [
            ("Single Sign-On", "Authenticate once and access every bundled application. OAuth2/OIDC integration means one identity across Odoo, Nextcloud, Mattermost, WordPress, and more."),
            ("Customizable Dashboards", "Drag-and-drop widgets to build your perfect workspace. Embed application views, charts, reports, and data feeds on personalized portal pages."),
            ("Tenant Branding", "Each organization gets their own branded portal experience — custom logos, colors, domain, and layout. White-label ready for partners and resellers."),
            ("Role-Based Navigation", "Users see only what they need. Administrators get full control panels; team members get focused work views; clients get self-service portals."),
        ],
        "integration": "The Portal is the unified front end for PolySaaS. It embeds Odoo dashboards, Nextcloud file browsers, Mattermost conversations, WordPress content, and PolySysMon health displays — all within a single, navigable interface.",
    },
    "dynamic-orchestration": {
        "title": "Dynamic Orchestration",
        "subtitle": "No-Code Workflow Automation",
        "hero": "Dynamic Orchestration lets you customize workflows across your entire PolySaaS stack — without writing code. Connect applications, automate data flow, and trigger actions based on events. Your business rules, dynamically enforced across every application.",
        "capabilities": [
            ("Visual Workflow Builder", "Define workflows using a visual interface. Drag triggers, conditions, and actions to create automation chains that span multiple applications."),
            ("Event-Driven Triggers", "React to events from any application: new Odoo order, Nextcloud file upload, Mattermost message, or PolySniffer traffic pattern. Chain triggers for complex logic."),
            ("Atomic Services", "Each workflow step is an Atomic Service — a small, focused microservice that does one thing well. Compose them into powerful workflows without monolithic dependencies."),
            ("Dynamic Customization", "Modify workflows at runtime without redeployment. Add new rules, change thresholds, or reroute data flows — all through the portal's administration interface."),
        ],
        "integration": "Dynamic Orchestration is the automation layer of PolySaaS. It connects every bundled application through Atomic Services, enabling workflows like: 'When Odoo creates an invoice, store it in Nextcloud, notify the team in Mattermost, and update the Liferay portal dashboard.'",
    },
    "polysniffer": {
        "title": "PolySniffer",
        "subtitle": "Intelligent Traffic Analysis",
        "hero": "PolySniffer passively monitors all traffic to your configured applications — collecting protocols, cookies, headers, URLs, and everything you need for seamless integration. It sees what others miss, enabling automatic discovery of integration points.",
        "capabilities": [
            ("Passive Traffic Monitoring", "PolySniffer watches HTTP/HTTPS traffic without injecting proxies or modifying requests. Zero impact on application performance."),
            ("Protocol & Header Analysis", "Capture and analyze request/response headers, cookies, authentication tokens, and content types. Understand exactly how each application communicates."),
            ("Integration Discovery", "Automatically identify API endpoints, authentication flows, and data formats. PolySniffer maps the integration landscape so you don't have to reverse-engineer it."),
            ("Real-Time Dashboard", "Live traffic dashboard showing all captured requests, color-coded by status. Filter by application, method, status code, or content type."),
        ],
        "integration": "PolySniffer feeds its discoveries into Dynamic Orchestration — detected API endpoints become candidates for Atomic Services. Traffic patterns inform Monitor Logger alerts, and integration maps display on the Liferay portal.",
    },
    "apps-as-peers": {
        "title": "Apps As Peers",
        "subtitle": "First-Class Application Ecosystem",
        "hero": "In PolySaaS, every bundled application is a first-class peer — not a bolted-on add-on. Odoo, Nextcloud, Mattermost, WordPress, Liferay, Dolibarr, Monitor Logger, and PolySysMon operate side by side, sharing data and triggering workflows through standardized interfaces.",
        "capabilities": [
            ("Equal Standing", "No application is 'primary' or 'secondary.' Each peer has full access to shared services: authentication, storage, messaging, and orchestration."),
            ("Standardized Communication", "Applications communicate through OpenAPI-documented Atomic Services. No proprietary protocols or vendor lock-in. Any app can talk to any other app."),
            ("Shared Data Layer", "Common data entities — customers, files, messages, events — are accessible to every peer through the orchestration layer. No data silos."),
            ("Independent Scaling", "Each application scales independently based on its own load. A spike in Odoo usage doesn't slow down Mattermost or Nextcloud."),
        ],
        "integration": "Apps As Peers is the philosophy that makes PolySaaS work. By treating every application as an equal participant in a shared ecosystem, we eliminate the integration tax that normally makes multi-app environments fragile and expensive.",
    },
    "openapi-2": {
        "title": "OpenAPI / Swagger",
        "subtitle": "Standard API Documentation & Testing",
        "hero": "Every Atomic Service and integration endpoint in PolySaaS is documented with OpenAPI (Swagger) specifications. Explore, test, and integrate with any external system using standard interfaces — making PolySaaS fully extensible and developer-friendly.",
        "capabilities": [
            ("Complete API Documentation", "Every endpoint is documented with parameters, response schemas, authentication requirements, and example payloads. No guessing how to integrate."),
            ("Interactive Testing", "Swagger UI lets you test API calls directly from the documentation. Send requests, inspect responses, and validate integrations without writing code."),
            ("Code Generation", "Generate client libraries in any language from the OpenAPI specs. Python, JavaScript, Java, Go — connect to PolySaaS from your existing tools."),
            ("Versioned & Stable", "APIs follow semantic versioning. Breaking changes are communicated in advance. Your integrations won't break on platform updates."),
        ],
        "integration": "OpenAPI specs are auto-generated from Atomic Services. External systems can discover and connect to any PolySaaS capability — from Odoo's CRM data to PolySysMon's health metrics — through standard, documented, testable endpoints.",
    },
    "ai-as-peers": {
        "title": "AI As Peers",
        "subtitle": "Intelligent Agents in Your Workflow",
        "hero": "AI As Peers brings intelligent agents into your daily workflows. AI joins your Mattermost chats, suggests improvements, automates decisions, and scales effortlessly. Atomic Services can be agents to any AI — included in your customized workflows as first-class participants.",
        "capabilities": [
            ("Conversational AI in Mattermost", "AI agents participate in team channels — answering questions, summarizing discussions, drafting responses, and executing commands. Natural language interface to your entire platform."),
            ("Decision Automation", "AI analyzes data from Odoo, Monitor Logger, and PolySysMon to recommend actions: reorder inventory, escalate support tickets, or adjust resource allocation."),
            ("Workflow Acceleration", "AI peers execute repetitive tasks: data entry, report generation, status updates, and notification routing. Your team focuses on decisions, not data shuffling."),
            ("Extensible AI Framework", "Connect any AI model — OpenAI, Anthropic, local models — through Atomic Services. Each AI capability is a composable service in your orchestration workflows."),
        ],
        "integration": "AI As Peers integrates with every layer of PolySaaS. AI agents read Odoo data, access Nextcloud files, post to Mattermost channels, update WordPress content, and trigger Dynamic Orchestration workflows — all through the same Atomic Services that connect human-facing applications.",
    },
    "bundled-applications": {
        "title": "Bundled Applications",
        "subtitle": "Eight Enterprise-Grade Applications, One Platform",
        "hero": "PolySaaS bundles eight enterprise-grade applications into a single orchestrated platform. Each application is a first-class peer — sharing data, triggering workflows, and collaborating through standardized Atomic Services. One subscription, one login, unlimited integration.",
        "capabilities": [
            ("Odoo — ERP & CRM", "Comprehensive business operations: sales, purchasing, inventory, accounting, HR, and project management at enterprise scale."),
            ("Nextcloud — Files & Collaboration", "Secure file storage, real-time document editing, and team collaboration with full data sovereignty."),
            ("Mattermost — Team Messaging", "Enterprise-grade team chat with AI Peers integration for secure, productive, AI-enhanced communications."),
            ("WordPress — Content Management", "Flexible content creation, blogging, and dynamic website management integrated with your business applications."),
            ("Liferay — Enterprise Portal", "Unified portal delivering personalized content, role-based dashboards, and seamless navigation across all applications."),
            ("Dolibarr — ERP & Invoicing", "Modular invoicing, proposals, and client management for cost-effective financial operations."),
            ("Monitor Logger — System Monitoring", "Centralized logging and alerting for proactive issue detection across your entire platform."),
            ("PolySysMon — Performance Tracking", "Continuous health monitoring ensuring reliability, uptime, and optimal performance across your stack."),
        ],
        "integration": "All eight applications share a common authentication layer, a unified data orchestration bus, and standardized OpenAPI interfaces. Add one application or use all eight — they work together seamlessly from day one.",
    },
}


# ============================================================
# PAGE TEMPLATE
# ============================================================

def build_page_content(slug, page_data, existing_css_and_toggle):
    """Build the full page content with the template."""
    title = page_data['title']
    subtitle = page_data['subtitle']
    hero = page_data['hero']
    capabilities = page_data['capabilities']
    integration = page_data['integration']
    
    # Build capabilities HTML
    caps_html = ""
    for cap_title, cap_desc in capabilities:
        caps_html += f'''
<div style="background:var(--ps-card-bg,#f8fafc);border:1px solid var(--ps-border,#e5e7eb);border-radius:12px;padding:24px;margin-bottom:16px;">
<h3 style="color:var(--ps-primary,#001F3F);margin:0 0 8px 0;font-size:1.2rem;">{cap_title}</h3>
<p style="color:var(--ps-text,#1F2937);margin:0;line-height:1.6;">{cap_desc}</p>
</div>'''
    
    content_block = f'''<!-- wp:html -->
<h2 style="text-align:center;padding:10px 0;margin:0;color:var(--ps-primary,#001F3F);font-size:2rem;font-weight:700;">{title}</h2>
<p style="text-align:center;color:var(--ps-accent,#2B6CB0);font-size:1.2rem;margin:0 0 20px 0;font-weight:500;">{subtitle}</p>

<div style="max-width:800px;margin:0 auto;padding:0 20px;">

<p style="color:var(--ps-text,#1F2937);font-size:1.05rem;line-height:1.8;margin-bottom:32px;">{hero}</p>

<h2 style="color:var(--ps-primary,#001F3F);font-size:1.5rem;margin-bottom:20px;">Key Capabilities</h2>
{caps_html}

<div style="background:var(--ps-card-bg,#f0f4f8);border-left:4px solid var(--ps-accent,#2B6CB0);border-radius:0 12px 12px 0;padding:24px;margin:32px 0;">
<h3 style="color:var(--ps-primary,#001F3F);margin:0 0 8px 0;">PolySaaS Integration</h3>
<p style="color:var(--ps-text,#1F2937);margin:0;line-height:1.6;">{integration}</p>
</div>

<div style="text-align:center;padding:32px 0;">
<a href="{HOME_URL}/schedule-demo/" style="display:inline-block;background:var(--ps-accent,#2B6CB0);color:#fff;padding:14px 32px;border-radius:8px;text-decoration:none;font-weight:600;font-size:1rem;">Sign Up for a Demo</a>
</div>

</div>
<!-- /wp:html -->'''
    
    return existing_css_and_toggle + '\n' + content_block


# ============================================================
# MAIN: Update all pages
# ============================================================

r = s.get(f"{AZURE}/wp-json/wp/v2/pages", params={
    "per_page": 100, "context": "edit", "_fields": "id,slug,content"
})
all_pages = r.json()
page_map = {p['slug']: p for p in all_pages}

print(f"Found {len(all_pages)} pages total")
print(f"Building {len(PAGES)} inner pages\n")

built = 0
for slug, page_data in PAGES.items():
    if slug not in page_map:
        print(f"  {slug}: NOT FOUND in WordPress, skipping")
        continue
    
    wp_page = page_map[slug]
    raw = wp_page['content']['raw']
    
    # Extract existing CSS and toggle blocks (preserve them)
    css_and_toggle = []
    for match in re.finditer(r'<!-- wp:html -->.*?<!-- /wp:html -->', raw, re.DOTALL):
        block = match.group(0)
        if '<style>' in block or 'ps-theme-toggle' in block:
            css_and_toggle.append(block)
    
    existing_blocks = '\n'.join(css_and_toggle)
    
    # Build new page content
    new_content = build_page_content(slug, page_data, existing_blocks)
    
    r2 = s.post(f"{AZURE}/wp-json/wp/v2/pages/{wp_page['id']}", json={"content": new_content})
    if r2.status_code == 200:
        built += 1
        print(f"  {slug}: built ({page_data['title']})")
    else:
        print(f"  {slug}: FAILED {r2.status_code}")

print(f"\nBuilt {built}/{len(PAGES)} pages")
