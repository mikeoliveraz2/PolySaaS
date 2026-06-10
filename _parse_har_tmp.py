import json
import re

with open(r"C:\Users\PC\.cursor\projects\d-PolySaaS\agent-transcripts\fe2a9519-5576-4596-a730-bb1cbe27bfc7\fe2a9519-5576-4596-a730-bb1cbe27bfc7.jsonl", "r", encoding="utf-8", errors="replace") as f:
    lines = f.readlines()

def extract_har(text):
    """Extract HAR JSON object from text."""
    # Find where "log" appears in quotes
    idx = text.find('"log"')
    if idx < 0:
        return None
    
    # Go back to find the opening {
    start_idx = text.rfind('{', 0, idx)
    if start_idx < 0:
        return None
    
    # Now find the matching closing }
    depth = 0
    in_string = False
    escape = False
    
    for i in range(start_idx, len(text)):
        ch = text[i]
        
        if escape:
            escape = False
            continue
        
        if ch == '\\':
            escape = True
            continue
        
        if ch == '"':
            in_string = not in_string
            continue
        
        if not in_string:
            if ch == '{':
                depth += 1
            elif ch == '}':
                depth -= 1
                if depth == 0:
                    # Try to parse
                    try:
                        har_str = text[start_idx:i+1]
                        har = json.loads(har_str)
                        if 'log' in har:
                            return har
                    except:
                        pass
    
    return None

# Extract from line 0 (passthrough)
msg0 = json.loads(lines[0])
text0 = msg0.get("message", {}).get("content", [{}])[0].get("text", "")
pt_har = extract_har(text0)

# Extract from line 402 (direct)
msg402 = json.loads(lines[402])
text402 = msg402.get("message", {}).get("content", [{}])[0].get("text", "")
direct_har = extract_har(text402)

print("="*70)
print("PASSTHROUGH HAR (t150 via /pt/admin/)")
print("="*70)
if pt_har:
    entries = pt_har.get('log', {}).get('entries', [])
    print(f"Total Entries: {len(entries)}\n")
    print("First 10 requests:")
    for i, entry in enumerate(entries[:10]):
        req = entry.get('request', {})
        resp = entry.get('response', {})
        url = req.get('url', '')
        status = resp.get('status', '?')
        method = req.get('method', '?')
        
        # Truncate path
        if 'pt/admin' in url:
            path = '...' + url.split('pt/admin')[-1][-60:]
        else:
            parts = url.split('/')
            path = '/'.join(parts[-3:])
        
        print(f"  {i+1:2}. [{status:3}] {method:6} {path}")
else:
    print("Could not extract HAR")

print("\n" + "="*70)
print("DIRECT HAR (t142 direct to Mattermost)")
print("="*70)
if direct_har:
    entries = direct_har.get('log', {}).get('entries', [])
    print(f"Total Entries: {len(entries)}\n")
    print("First 10 requests:")
    for i, entry in enumerate(entries[:10]):
        req = entry.get('request', {})
        resp = entry.get('response', {})
        url = req.get('url', '')
        status = resp.get('status', '?')
        method = req.get('method', '?')
        
        # Truncate path
        parts = url.split('/')
        path = '/'.join(parts[-3:])
        
        print(f"  {i+1:2}. [{status:3}] {method:6} {path}")
else:
    print("Could not extract HAR")

# Compare failures
print("\n" + "="*70)
print("FAILURES COMPARISON")
print("="*70)
if pt_har:
    pt_failures = [e for e in pt_har.get('log', {}).get('entries', []) if e.get('response', {}).get('status', 200) >= 400]
    print(f"Passthrough failed requests: {len(pt_failures)}")
    for f in pt_failures[:5]:
        req = f.get('request', {})
        resp = f.get('response', {})
        print(f"  [{resp.get('status')}] {req.get('method')} {req.get('url')[-80:]}")

if direct_har:
    direct_failures = [e for e in direct_har.get('log', {}).get('entries', []) if e.get('response', {}).get('status', 200) >= 400]
    print(f"\nDirect failed requests: {len(direct_failures)}")
    for f in direct_failures[:5]:
        req = f.get('request', {})
        resp = f.get('response', {})
        print(f"  [{resp.get('status')}] {req.get('method')} {req.get('url')[-80:]}")
