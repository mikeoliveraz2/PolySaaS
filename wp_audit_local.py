"""Audit local staging HTML files for spelling and grammar issues."""
import os
import re
from html import unescape
from pathlib import Path

STAGING_DIR = Path(r"d:\PolySaaS\dose\website\staging\wp-content\temp")
SANDBOX_DIR = Path(r"d:\PolySaaS\dose\website\sandbox\wp-content")

TECH_TERMS = {
    'polysaas', 'polysniffer', 'polysysmon', 'nextcloud', 'mattermost', 'odoo',
    'dolibarr', 'liferay', 'wordpress', 'django', 'bigquery', 'pubsub', 'grok',
    'claude', 'gemini', 'openapi', 'swagger', 'kubernetes', 'nginx', 'redis',
    'postgresql', 'mongodb', 'graphql', 'restful', 'webhooks', 'websocket',
    'localhost', 'favicon', 'onclick', 'svg', 'png', 'jpg', 'css', 'html', 'js',
    'json', 'api', 'apis', 'sdk', 'url', 'urls', 'ui', 'ux', 'ai', 'ml', 'llm',
    'saas', 'dxp', 'erp', 'crm', 'hr', 'iot', 'sso', 'oauth', 'jwt', 'smtp',
    'https', 'http', 'tcp', 'dns', 'cdn', 'aws', 'gcp', 'ssl', 'tls', 'vpc',
    'cicd', 'devops', 'yaml', 'toml', 'env', 'dockerfile', 'npm', 'pip',
    'href', 'src', 'div', 'btn', 'cta', 'img', 'rgba', 'px', 'vh', 'vw',
    'flexbox', 'inline', 'dropdown', 'navbar', 'sidebar', 'tooltip', 'popup',
    'async', 'middleware', 'microservice', 'microservices', 'monorepo',
    'portlet', 'portlets', 'iframe', 'backend', 'frontend', 'fullstack',
    'signup', 'login', 'logout', 'username', 'favicon', 'passthrough',
    'sniffable', 'sniffing', 'sniffer', 'orchestrable', 'orchestrator',
    'pre', 'config', 'configs', 'blog', 'podcast', 'webinar', 'whitepaper',
    'scalable', 'scalability', 'multitenancy', 'multitenant',
    'roi', 'arr', 'mrr', 'cagr', 'tam', 'sam', 'som', 'kpi', 'okr',
    'itil', 'iso', 'soc', 'gdpr', 'hipaa', 'pci', 'nist', 'fedramp',
    'onprem', 'hybridcloud', 'serverless', 'containerized',
    'bricks', 'elementor', 'hostinger', 'jazzmin', 'gunicorn', 'uvicorn',
}

COMMON_MISSPELLINGS = {
    'teh': 'the', 'thier': 'their', 'recieve': 'receive', 'occured': 'occurred',
    'seperate': 'separate', 'definately': 'definitely', 'accomodate': 'accommodate',
    'occurence': 'occurrence', 'independant': 'independent', 'neccessary': 'necessary',
    'priviledge': 'privilege', 'succesful': 'successful', 'concious': 'conscious',
    'enviroment': 'environment', 'goverment': 'government', 'managment': 'management',
    'developement': 'development', 'performace': 'performance', 'infrastucture': 'infrastructure',
    'orchestartion': 'orchestration', 'authentification': 'authentication',
    'configuraton': 'configuration', 'implmentation': 'implementation',
    'subsription': 'subscription', 'intergration': 'integration', 'integation': 'integration',
    'orginization': 'organization', 'organzation': 'organization',
    'parners': 'partners', 'partnrs': 'partners', 'patners': 'partners',
    'reselers': 'resellers', 'resellerss': 'resellers',
    'enterprize': 'enterprise', 'entreprise': 'enterprise',
    'bussiness': 'business', 'busness': 'business', 'buisness': 'business',
    'applicaton': 'application', 'applicaiton': 'application', 'aplication': 'application',
    'arhitecture': 'architecture', 'archtecture': 'architecture', 'architecure': 'architecture',
    'servces': 'services', 'serivces': 'services', 'servies': 'services',
    'dynmaic': 'dynamic', 'dynamc': 'dynamic',
    'orchstration': 'orchestration', 'orchetration': 'orchestration',
    'monitring': 'monitoring', 'montioring': 'monitoring',
    'endpont': 'endpoint', 'endpiont': 'endpoint',
    'autmation': 'automation', 'automaton': 'automation',
    'dashbord': 'dashboard', 'dashbaord': 'dashboard',
    'analtics': 'analytics', 'anaytics': 'analytics',
    'securty': 'security', 'secuirty': 'security',
    'complance': 'compliance', 'compiance': 'compliance',
    'custmize': 'customize', 'cutomize': 'customize',
    'connctor': 'connector', 'conector': 'connector',
    'bundeld': 'bundled', 'bundlled': 'bundled',
    'exteranl': 'external', 'extrnal': 'external',
    'pricng': 'pricing', 'pricinng': 'pricing',
    'templete': 'template', 'tempalte': 'template',
    'galery': 'gallery', 'gallrey': 'gallery',
    'stremaing': 'streaming', 'streamng': 'streaming',
    'deployement': 'deployment', 'deploymnet': 'deployment',
    'realtime': 'real-time', 'real time': 'real-time',
}

def strip_html(html):
    text = re.sub(r'<style[^>]*>.*?</style>', '', html, flags=re.DOTALL)
    text = re.sub(r'<script[^>]*>.*?</script>', '', text, flags=re.DOTALL)
    text = re.sub(r'<!--.*?-->', '', text, flags=re.DOTALL)
    text = re.sub(r'<[^>]+>', ' ', text)
    text = unescape(text)
    text = re.sub(r'\{[^}]+\}', ' ', text)  # remove CSS-like content
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def audit_text(text):
    issues = []
    words = re.findall(r"[a-zA-Z']+", text)

    for i, word in enumerate(words):
        lower = word.lower()
        if lower in COMMON_MISSPELLINGS:
            ctx_start = max(0, i - 4)
            ctx_end = min(len(words), i + 5)
            context = ' '.join(words[ctx_start:ctx_end])
            issues.append({
                'type': 'spelling',
                'word': word,
                'suggestion': COMMON_MISSPELLINGS[lower],
                'context': f"...{context}..."
            })

    # Repeated words
    for i in range(len(words) - 1):
        if words[i].lower() == words[i+1].lower() and words[i].lower() in (
            'the', 'a', 'an', 'and', 'or', 'to', 'in', 'on', 'is', 'are', 'was',
            'for', 'with', 'of', 'your', 'our', 'that', 'this', 'it', 'we', 'you'
        ):
            ctx_start = max(0, i - 3)
            ctx_end = min(len(words), i + 6)
            context = ' '.join(words[ctx_start:ctx_end])
            issues.append({
                'type': 'grammar',
                'word': f'{words[i]} {words[i+1]}',
                'suggestion': words[i],
                'context': f"...{context}..."
            })

    return issues

def scan_directory(directory, label):
    results = {}
    if not directory.exists():
        return results
    for f in sorted(directory.rglob('*.html')):
        try:
            content = f.read_text(encoding='utf-8', errors='ignore')
            text = strip_html(content)
            if len(text) < 20:
                continue
            issues = audit_text(text)
            rel = str(f.relative_to(directory))
            if issues:
                results[f"{label}/{rel}"] = issues
        except Exception as e:
            print(f"  Error reading {f}: {e}")
    return results

if __name__ == '__main__':
    print("="*80)
    print("SITE-WIDE SPELLING & GRAMMAR AUDIT (Local Staging + API)")
    print("="*80)

    # 1. API content (posts that have content)
    print("\n[1/3] Checking WordPress API content (posts)...")
    import requests
    SITE = "https://azure-nightingale-589250.hostingersite.com"
    s = requests.Session()
    s.auth = ("mikeoliveraz@gmail.com", "vlop MpGU Os2V xDSI C6T7 2fAN")
    
    api_issues = {}
    for kind in ['posts', 'pages']:
        resp = s.get(f"{SITE}/wp-json/wp/v2/{kind}", params={"per_page": 50, "status": "any"})
        items = resp.json()
        for item in items:
            title = unescape(item['title']['rendered'])
            # Check title
            title_issues = audit_text(title)
            # Check content
            text = strip_html(item['content']['rendered'])
            content_issues = audit_text(text) if text.strip() else []
            combined = title_issues + content_issues
            if combined:
                key = f"WP-{kind.upper()}: {title} [ID:{item['id']}]"
                api_issues[key] = combined
    
    print(f"   Found {sum(len(v) for v in api_issues.values())} issues in API content")

    # 2. Local staging files
    print("\n[2/3] Scanning staging HTML files...")
    staging_issues = scan_directory(STAGING_DIR, "staging")
    print(f"   Found {sum(len(v) for v in staging_issues.values())} issues in staging files")

    # 3. Local sandbox files
    print("\n[3/3] Scanning sandbox HTML files...")
    sandbox_temo = Path(r"d:\PolySaaS\dose\website\sandbox\wp-content\temo")
    sandbox_issues = scan_directory(sandbox_temo, "sandbox")
    print(f"   Found {sum(len(v) for v in sandbox_issues.values())} issues in sandbox files")

    # Combine and report
    all_issues = {}
    all_issues.update(api_issues)
    all_issues.update(staging_issues)
    all_issues.update(sandbox_issues)

    total = sum(len(v) for v in all_issues.values())

    print(f"\n{'='*80}")
    print(f"AUDIT RESULTS")
    print(f"{'='*80}")
    print(f"Total issues found: {total}")
    print(f"Across {len(all_issues)} items\n")

    for label, issues in sorted(all_issues.items()):
        print(f"\n--- {label} ---")
        for issue in issues:
            icon = "SPELL" if issue['type'] == 'spelling' else "GRAM "
            print(f"  [{icon}] '{issue['word']}' -> '{issue['suggestion']}'")
            print(f"          {issue['context']}")

    if not all_issues:
        print("\nNo issues found! Content looks clean.")

    print(f"\n{'='*80}")
    print(f"Audit complete.")
