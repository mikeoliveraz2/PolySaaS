"""WordPress site-wide spelling and grammar audit."""
import requests
import re
import json
from html import unescape

SITE = "https://azure-nightingale-589250.hostingersite.com"
USER = "mikeoliveraz@gmail.com"
APP_PASS = "vlop MpGU Os2V xDSI C6T7 2fAN"

def strip_html(html):
    text = re.sub(r'<style[^>]*>.*?</style>', '', html, flags=re.DOTALL)
    text = re.sub(r'<script[^>]*>.*?</script>', '', text, flags=re.DOTALL)
    text = re.sub(r'<[^>]+>', ' ', text)
    text = unescape(text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def get_all_content():
    session = requests.Session()
    session.auth = (USER, APP_PASS)

    content = {}

    for kind in ['posts', 'pages']:
        page = 1
        while True:
            resp = session.get(f"{SITE}/wp-json/wp/v2/{kind}", params={
                'per_page': 50, 'page': page, 'status': 'any'
            })
            if resp.status_code != 200:
                break
            items = resp.json()
            if not items:
                break
            for item in items:
                title = unescape(item['title']['rendered'])
                raw = item['content']['rendered']
                text = strip_html(raw)
                if text.strip():
                    content[f"{kind.upper()}: {title} [ID:{item['id']}]"] = {
                        'id': item['id'],
                        'type': kind,
                        'title': title,
                        'status': item['status'],
                        'text': text
                    }
            page += 1

    return content

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
    'orginization': 'organization', 'customise': 'customize', 'analyse': 'analyze',
    'utilise': 'utilize', 'optimise': 'optimize', 'visualise': 'visualize',
    'centralise': 'centralize', 'standardise': 'standardize',
    'saas': None,  # skip - proper acronym
    'youre': "you're", 'dont': "don't", 'cant': "can't", 'wont': "won't",
    'didnt': "didn't", 'doesnt': "doesn't", 'isnt': "isn't", 'arent': "aren't",
    'wasnt': "wasn't", 'werent': "weren't", 'havent': "haven't", 'hasnt': "hasn't",
    'wouldnt': "wouldn't", 'shouldnt': "shouldn't", 'couldnt': "couldn't",
    'its a': "it's a", 'its the': "it's the", 'its not': "it's not",
}

GRAMMAR_PATTERNS = [
    (r'\b(a)\s+(ai|api|app|atomic|auto|open)\b', 'an', 'article "a" before vowel sound'),
    (r'\b(an)\s+([bcdfghjklmnpqrstvwxyz](?!our))\w+\b', 'a', 'article "an" before consonant sound'),
    (r'(\w+)\s+\1\b', None, 'repeated word'),
    (r'\.\s*[a-z]', None, 'lowercase after period (possible missing cap)'),
    (r'\s,', None, 'space before comma'),
    (r'\s\.', None, 'space before period'),
    (r'  +', None, 'double/multiple spaces'),
]

def audit_text(label, text):
    issues = []
    words = re.findall(r"[a-zA-Z']+", text)

    for i, word in enumerate(words):
        lower = word.lower()
        if lower in COMMON_MISSPELLINGS and COMMON_MISSPELLINGS[lower] is not None:
            context_start = max(0, i-3)
            context_end = min(len(words), i+4)
            context = ' '.join(words[context_start:context_end])
            issues.append({
                'type': 'spelling',
                'word': word,
                'suggestion': COMMON_MISSPELLINGS[lower],
                'context': f"...{context}..."
            })

    for i in range(len(words) - 1):
        bigram = f"{words[i].lower()} {words[i+1].lower()}"
        if bigram in COMMON_MISSPELLINGS and COMMON_MISSPELLINGS[bigram] is not None:
            context_start = max(0, i-2)
            context_end = min(len(words), i+5)
            context = ' '.join(words[context_start:context_end])
            issues.append({
                'type': 'grammar',
                'word': bigram,
                'suggestion': COMMON_MISSPELLINGS[bigram],
                'context': f"...{context}..."
            })

    for pattern, suggestion, desc in GRAMMAR_PATTERNS:
        for match in re.finditer(pattern, text, re.IGNORECASE if 'repeated' in desc else 0):
            start = max(0, match.start() - 30)
            end = min(len(text), match.end() + 30)
            context = text[start:end].strip()
            if desc == 'repeated word' and match.group(1).lower() in ('the', 'that', 'had', 'has', 'is', 'a', 'an', 'and', 'or', 'to', 'in', 'on', 'at', 'of', 'for', 'with', 'as', 'by', 'be', 'we', 'our', 'your', 'it', 'all'):
                issues.append({
                    'type': 'grammar',
                    'word': f'"{match.group(1)} {match.group(1)}"',
                    'suggestion': match.group(1),
                    'context': f"...{context}..."
                })
            elif desc != 'repeated word':
                issues.append({
                    'type': 'grammar',
                    'word': match.group(0).strip(),
                    'suggestion': suggestion or '(review)',
                    'context': f"...{context}..."
                })

    return issues

if __name__ == '__main__':
    print("Pulling all content from WordPress...")
    content = get_all_content()
    print(f"Retrieved {len(content)} items\n")

    all_issues = {}
    total = 0

    for label, data in sorted(content.items()):
        issues = audit_text(label, data['text'])
        title_issues = audit_text(f"TITLE: {data['title']}", data['title'])
        combined = title_issues + issues
        if combined:
            all_issues[label] = {
                'status': data['status'],
                'issues': combined
            }
            total += len(combined)

    print(f"{'='*80}")
    print(f"WORDPRESS SITE-WIDE SPELLING & GRAMMAR AUDIT")
    print(f"Site: {SITE}")
    print(f"Items scanned: {len(content)}")
    print(f"Total issues found: {total}")
    print(f"{'='*80}\n")

    for label, data in sorted(all_issues.items()):
        print(f"\n--- {label} [{data['status']}] ---")
        for issue in data['issues']:
            icon = "SP" if issue['type'] == 'spelling' else "GR"
            suggestion = f" -> {issue['suggestion']}" if issue['suggestion'] != '(review)' else ' (review needed)'
            print(f"  [{icon}] '{issue['word']}'{suggestion}")
            print(f"       {issue['context']}")

    if not all_issues:
        print("\nNo issues found! Content looks clean.")
    
    print(f"\n{'='*80}")
    print(f"Audit complete. {total} issues across {len(all_issues)} items.")
