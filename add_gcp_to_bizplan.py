"""Add GCP Deployment Plan section to the business plan docx."""
import sys, copy
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
from docx import Document
from docx.shared import Pt, Inches, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH

SRC = r'D:\PolySaaS\dose\website\staging\wp-content\uploads\PolySaaS Online Business PlanF1.md.docx'
DST = r'D:\PolySaaS\dose\website\staging\wp-content\uploads\PolySaaS Online Business PlanF1.md.docx'

doc = Document(SRC)

# Find the insertion point: after "Application teaser" paragraph (85) 
# and before "Targets (18-24 months)" heading (86)
insert_after = None
for i, p in enumerate(doc.paragraphs):
    if 'Targets' in p.text and '18' in p.text and '24' in p.text:
        insert_after = i
        break

if insert_after is None:
    print("Could not find 'Targets (18-24 months)' heading")
    sys.exit(1)

print(f"Will insert GCP Deployment Plan before paragraph {insert_after}: '{doc.paragraphs[insert_after].text[:60]}'")

# We need to insert paragraphs before the "Targets" heading.
# python-docx doesn't have a simple insert method, so we use element manipulation.
from docx.oxml.ns import qn
from lxml import etree

target_element = doc.paragraphs[insert_after]._element

def add_paragraph_before(target, text, style=None, bold=False, font_size=None):
    """Insert a paragraph before the target element."""
    new_p = etree.SubElement(target.getparent(), qn('w:p'))
    target.getparent().remove(new_p)
    target.addprevious(new_p)
    
    # Add paragraph properties
    pPr = etree.SubElement(new_p, qn('w:pPr'))
    if style:
        pStyle = etree.SubElement(pPr, qn('w:pStyle'))
        pStyle.set(qn('w:val'), style)
    
    # Add run with text
    run = etree.SubElement(new_p, qn('w:r'))
    if bold or font_size:
        rPr = etree.SubElement(run, qn('w:rPr'))
        if bold:
            etree.SubElement(rPr, qn('w:b'))
        if font_size:
            sz = etree.SubElement(rPr, qn('w:sz'))
            sz.set(qn('w:val'), str(font_size * 2))  # half-points
    
    t = etree.SubElement(run, qn('w:t'))
    t.text = text
    t.set(qn('xml:space'), 'preserve')
    
    return new_p

# Build the GCP Deployment Plan section
# Insert in reverse order since each goes before the target

sections = []

# Section heading
sections.append(('Heading4', 'GCP Deployment Plan & Cost Estimate', True, 14))

# Intro
sections.append((None, 
    'PolySaaS deploys natively on Google Cloud Platform using a containerized microservices architecture. '
    'The platform comprises the DOSE core (Django) plus 8 bundled applications, each running as an independent '
    'Cloud Run service with shared database infrastructure. The following plan details the phased deployment, '
    'estimated costs, and timeline.', False, None))

sections.append((None, '', False, None))

# Phase overview
sections.append((None, 'Deployment Phases & Timeline (8\u201311 weeks total)', True, 11))
sections.append((None, '', False, None))

sections.append((None, 
    'Phase 1 \u2014 SSO Readiness (2\u20134 weeks, $0): Complete OAuth2/SSO integration across all bundled '
    'applications. Passthrough auth middleware (JWT/header injection) for WordPress, Dolibarr, and custom apps; '
    'native OIDC for Mattermost, Odoo, Nextcloud, and Liferay. End-to-end single-login verification.', False, None))

sections.append((None, 
    'Phase 2 \u2014 GCP Infrastructure Setup (1 week, ~$0 using free credits): Create GCP project and enable '
    'billing, APIs (Cloud Run, Artifact Registry, Cloud SQL, Secret Manager, Cloud Build). Provision Cloud SQL '
    'instances (PostgreSQL 15 + MySQL 8), GCS buckets (static, media, backups), and Secret Manager entries. '
    'Build production Dockerfile (Django/Gunicorn, multi-stage) and cloudbuild.yaml for CI/CD.', False, None))

sections.append((None, 
    'Phase 3 \u2014 Deploy DOSE Core (1 week): Build and push Docker image to Artifact Registry. Deploy to '
    'Cloud Run with environment variables, Secret Manager refs, and Cloud SQL connector. Configure static/media '
    'serving via GCS + Cloud CDN. Run migrations (public + tenant schemas). Map polysaas.online domain with '
    'managed SSL. Smoke test: login, admin dashboard, passthrough verification.', False, None))

sections.append((None, 
    'Phase 4 \u2014 Deploy Bundled Applications (3\u20134 weeks): Each application deploys as its own Cloud Run '
    'service. Priority order: Mattermost (2\u20133 days), Nextcloud (2\u20133 days), Odoo (2\u20133 days), '
    'WordPress (1\u20132 days), Liferay CE (2\u20133 days), Dolibarr (1\u20132 days), Monitor Logger (1 day), '
    'PolySysMon with its 6 microservices (3\u20134 days). Each includes SSO verification and passthrough URL '
    'configuration.', False, None))

sections.append((None, 
    'Phase 5 \u2014 Post-Deploy (1 week): Load balancer and routing configuration (subdomain or path-based). '
    'Monitoring and alerting via Cloud Logging and uptime checks. Backup/restore procedures for Cloud SQL. '
    'Google for Startups Cloud Program application submission. Documentation update.', False, None))

sections.append((None, '', False, None))

# Cost table
sections.append((None, 'Monthly Cost Estimate', True, 11))
sections.append((None, '', False, None))

cost_lines = [
    ('Cloud Run (DOSE core)', '$5\u201310/mo', 'Scales to zero when idle'),
    ('Cloud Run (8 bundled apps)', '$16\u201340/mo', '~$2\u20135/app, scales independently'),
    ('Cloud SQL (PostgreSQL 15)', '$7\u201350/mo', 'db-f1-micro ($7) to db-n1-standard-1 ($50)'),
    ('Cloud SQL (MySQL 8)', '$7\u201350/mo', 'WordPress + Liferay'),
    ('Memorystore Redis', '$0\u201330/mo', 'Optional; can use sidecar container'),
    ('Cloud Storage (GCS)', '$1\u20135/mo', 'Static files, media, backups'),
    ('Cloud Load Balancer', '$18\u201330/mo', 'Fixed base + per-GB data'),
    ('Artifact Registry', '$1\u20133/mo', 'Docker image storage'),
    ('Cloud Build', '$0\u20135/mo', '120 free build-minutes/day'),
    ('Secret Manager + SSL', '~$0', 'Negligible; free managed SSL'),
]

for svc, cost, note in cost_lines:
    sections.append((None, f'\u2022 {svc}: {cost} \u2014 {note}', False, None))

sections.append((None, '', False, None))

sections.append((None, 
    'Total (minimal configuration): ~$55\u201390/month. Total (recommended production): ~$100\u2013170/month. '
    'With Google for Startups credits ($200\u2013350K over 2 years): effectively $0/month for 18\u201324+ months, '
    'covering 100\u2013200%+ of projected GCP spend during the seed stage.', False, None))

sections.append((None, '', False, None))

# Architecture topology
sections.append((None, 'Architecture Topology', True, 11))
sections.append((None, '', False, None))

sections.append((None, 
    'Hybrid approach (recommended): DOSE core + lightweight apps served via path-based passthrough '
    '(e.g., polysaas.online/app/odoo/), while heavy-use applications get dedicated subdomains '
    '(e.g., mattermost.polysaas.online). Single Cloud SQL instance per database engine (PostgreSQL shared '
    'across DOSE, Mattermost, Odoo, PolySysMon; MySQL shared across WordPress and Liferay). '
    'Redis via Memorystore or Cloud Run sidecar. All secrets in Secret Manager. CI/CD via Cloud Build '
    'with auto-deploy on push to main branch.', False, None))

sections.append((None, '', False, None))

sections.append((None, 
    'This architecture aligns with the $4K/month GCP infrastructure budget in the Use of Funds table and is '
    'fully offset by the anticipated Google for Startups Cloud Program credits.', False, None))

sections.append((None, '', False, None))

# Insert all paragraphs (in order, each before the target)
for style, text, bold, font_size in sections:
    add_paragraph_before(target_element, text, style=style, bold=bold, font_size=font_size)

doc.save(DST)
print(f"SUCCESS - GCP Deployment Plan added to business plan ({len(sections)} paragraphs inserted)")
