import urllib.request, re
req = urllib.request.Request('http://localhost:8000/pt/admin/mattermost')
req.add_header('Cookie', 'sessionid=ufyi3bked1d0sj73nygeak9qrb1bnsi4; csrftoken=G4NUuPpvlNhD0Yum414pWbQcElo4wptc')
resp = urllib.request.urlopen(req)
html = resp.read().decode('utf-8')

# Check if MMAUTHTOKEN is in the shim
if 'MMAUTHTOKEN' in html:
    m = re.search(r'MMAUTHTOKEN\s*=\s*"([^"]*)"', html)
    if m:
        token = m.group(1)
        print(f'MMAUTHTOKEN found: {"set" if token else "EMPTY"} (len={len(token)})')
    else:
        m2 = re.search(r'MMAUTHTOKEN\s*=\s*([^;\n]+)', html)
        if m2:
            print(f'MMAUTHTOKEN raw: {m2.group(1)[:50]}')
        else:
            print('MMAUTHTOKEN mentioned but pattern not matched')
else:
    print('MMAUTHTOKEN not found in HTML')
