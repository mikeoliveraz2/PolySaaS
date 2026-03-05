"""Fetch and audit all rendered pages from the live WordPress site."""
import requests
import re
from html import unescape

SITE = "https://azure-nightingale-589250.hostingersite.com"

SLUGS = [
    ('Home', '/'),
    ('Architecture', '/architecture/'),
    ('Portal', '/portal/'),
    ('Atomic Services', '/atomic-services/'),
    ('Dynamic Orchestration', '/dynamic-orchestration/'),
    ('PolySniffer', '/polysniffer/'),
    ('AI As Peers', '/ai-as-peers/'),
    ('Apps As Peers', '/apps-as-peers/'),
    ('Bundled Applications', '/bundled-applications/'),
    ('External Applications', '/external-applications/'),
    ('Odoo', '/odoo/'),
    ('NextCloud', '/nextcloud/'),
    ('MatterMost', '/mattermost/'),
    ('WordPress', '/wordpress/'),
    ('PolySysMon', '/polysysmon/'),
    ('Monitor Logger', '/monitor-logger/'),
    ('Sign Up', '/sign-up/'),
    ('Gallery Images', '/gallery-images/'),
    ('Gallery Videos', '/gallery-videos/'),
    ('Dolibarr', '/dolibarr/'),
    ('CTA Templates', '/cta-templates/'),
    ('Liferay', '/liferay/'),
    ('OpenAPI', '/openapi/'),
    ('Pricing', '/pricing/'),
    ('Blog', '/blog/'),
    ('About Us', '/about-us/'),
    ('Request Demo', '/request-demo/'),
    ('For Partners', '/for-parners-resellers-and-large-enterprises/'),
]

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
    'reselers': 'resellers', 'enterprize': 'enterprise', 'entreprise': 'enterprise',
    'bussiness': 'business', 'busness': 'business', 'buisness': 'business',
    'applicaton': 'application', 'applicaiton': 'application', 'aplication': 'application',
    'arhitecture': 'architecture', 'archtecture': 'architecture', 'architecure': 'architecture',
    'servces': 'services', 'serivces': 'services', 'servies': 'services',
    'dynmaic': 'dynamic', 'dynamc': 'dynamic',
    'orchstration': 'orchestration', 'orchetration': 'orchestration',
    'monitring': 'monitoring', 'montioring': 'monitoring',
    'endpont': 'endpoint', 'endpiont': 'endpoint',
    'autmation': 'automation', 'dashbord': 'dashboard', 'dashbaord': 'dashboard',
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
    'visiblity': 'visibility', 'visibilty': 'visibility',
    'accesible': 'accessible', 'accessble': 'accessible',
    'reponse': 'response', 'respone': 'response',
    'reqest': 'request', 'requets': 'request',
    'messge': 'message', 'mesage': 'message',
    'chanel': 'channel', 'chanell': 'channel',
    'colaboration': 'collaboration', 'colloboration': 'collaboration',
    'comunication': 'communication', 'communcation': 'communication',
    'notifcation': 'notification', 'notificaton': 'notification',
    'efficent': 'efficient', 'efficeint': 'efficient',
    'intellgent': 'intelligent', 'inteligent': 'intelligent',
    'platfrom': 'platform', 'plaform': 'platform',
    'featur': 'feature', 'featrue': 'feature',
    'accout': 'account', 'acount': 'account',
    'compnay': 'company', 'companny': 'company',
    'anlaysis': 'analysis', 'anlysis': 'analysis',
    'worklfow': 'workflow', 'worflow': 'workflow',
    'shedule': 'schedule', 'schdule': 'schedule',
    'availble': 'available', 'avialable': 'available',
    'diffrent': 'different', 'diferent': 'different',
    'specifc': 'specific', 'speicfic': 'specific',
    'technolgy': 'technology', 'techology': 'technology',
    'soluton': 'solution', 'soution': 'solution',
    'poweful': 'powerful', 'powreful': 'powerful',
    'manange': 'manage', 'mangae': 'manage',
    'authenicate': 'authenticate', 'authentcate': 'authenticate',
    'opitmize': 'optimize', 'optmize': 'optimize',
    'capabiity': 'capability', 'capabilty': 'capability',
    'orhcestration': 'orchestration',
}

TECH_TERMS = {
    'polysaas', 'polysniffer', 'polysysmon', 'nextcloud', 'mattermost', 'odoo',
    'dolibarr', 'liferay', 'wordpress', 'django', 'bigquery', 'grok', 'claude',
    'gemini', 'openapi', 'swagger', 'api', 'apis', 'saas', 'dxp', 'erp', 'crm',
    'ai', 'ml', 'llm', 'ui', 'ux', 'sso', 'oauth', 'jwt', 'https', 'http',
    'css', 'html', 'js', 'json', 'sdk', 'url', 'cdn', 'aws', 'gcp', 'ssl',
    'devops', 'npm', 'svg', 'png', 'jpg', 'btn', 'cta', 'img', 'px',
    'iframe', 'backend', 'frontend', 'signup', 'login', 'passthrough',
    'sniffable', 'webhook', 'webhooks', 'websocket', 'microservice', 'favicon',
    'portlet', 'portlets', 'navbar', 'dropdown', 'tooltip', 'popup', 'middleware',
    'multitenancy', 'roi', 'arr', 'mrr', 'kpi', 'gdpr', 'hipaa', 'nist',
}

def strip_html(html):
    # Extract only the main content area
    main_match = re.search(r'<main[^>]*>(.*?)</main>', html, re.DOTALL)
    if main_match:
        html = main_match.group(1)
    else:
        body_match = re.search(r'<body[^>]*>(.*?)</body>', html, re.DOTALL)
        if body_match:
            html = body_match.group(1)

    text = re.sub(r'<style[^>]*>.*?</style>', '', html, flags=re.DOTALL)
    text = re.sub(r'<script[^>]*>.*?</script>', '', text, flags=re.DOTALL)
    text = re.sub(r'<!--.*?-->', '', text, flags=re.DOTALL)
    text = re.sub(r'<[^>]+>', ' ', text)
    text = unescape(text)
    text = re.sub(r'\{[^}]+\}', ' ', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def audit_text(text):
    issues = []
    words = re.findall(r"[a-zA-Z']+", text)

    for i, word in enumerate(words):
        lower = word.lower()
        if lower in TECH_TERMS:
            continue
        if lower in COMMON_MISSPELLINGS:
            ctx_start = max(0, i - 5)
            ctx_end = min(len(words), i + 6)
            context = ' '.join(words[ctx_start:ctx_end])
            issues.append({
                'type': 'spelling',
                'word': word,
                'suggestion': COMMON_MISSPELLINGS[lower],
                'context': f"...{context}..."
            })

    for i in range(len(words) - 1):
        if words[i].lower() == words[i+1].lower() and len(words[i]) > 1:
            ctx_start = max(0, i - 3)
            ctx_end = min(len(words), i + 6)
            context = ' '.join(words[ctx_start:ctx_end])
            issues.append({
                'type': 'grammar',
                'word': f'{words[i]} {words[i+1]}',
                'suggestion': f'{words[i]} (remove duplicate)',
                'context': f"...{context}..."
            })

    return issues

if __name__ == '__main__':
    print("="*80)
    print("RENDERED PAGE AUDIT — Fetching live Bricks-rendered content")
    print(f"Site: {SITE}")
    print("="*80)

    session = requests.Session()
    session.headers.update({'User-Agent': 'PolySaaS-Audit/1.0'})
    
    all_issues = {}
    total_pages = 0
    total_words = 0

    for name, slug in SLUGS:
        url = f"{SITE}{slug}"
        try:
            resp = session.get(url, timeout=15)
            if resp.status_code != 200:
                print(f"  SKIP {name}: HTTP {resp.status_code}")
                continue
            
            text = strip_html(resp.text)
            words = re.findall(r"[a-zA-Z']+", text)
            total_words += len(words)
            total_pages += 1
            
            issues = audit_text(text)
            if issues:
                all_issues[name] = {'url': url, 'issues': issues}
                print(f"  {name:35s} {len(words):5d} words  {len(issues)} issues")
            else:
                print(f"  {name:35s} {len(words):5d} words  CLEAN")
        except Exception as e:
            print(f"  ERROR {name}: {e}")

    print(f"\n{'='*80}")
    print(f"AUDIT RESULTS")
    print(f"{'='*80}")
    print(f"Pages scanned: {total_pages}")
    print(f"Total words checked: {total_words:,}")
    total_issues = sum(len(v['issues']) for v in all_issues.values())
    print(f"Total issues found: {total_issues}")
    print(f"Pages with issues: {len(all_issues)}\n")

    for name, data in sorted(all_issues.items()):
        print(f"\n--- {name} ({data['url']}) ---")
        for issue in data['issues']:
            icon = "SPELL" if issue['type'] == 'spelling' else "GRAM "
            print(f"  [{icon}] '{issue['word']}' -> '{issue['suggestion']}'")
            print(f"          {issue['context']}")

    if not all_issues:
        print("\nNo issues found! All rendered pages look clean.")

    print(f"\n{'='*80}")
    print("Audit complete.")
