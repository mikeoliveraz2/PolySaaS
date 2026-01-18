import requests

url = 'https://polysaas.supportsystem.com/scp/login.php/'
print(f'Testing URL: {url}')
try:
    resp = requests.get(url, timeout=10)
    print(f'Status: {resp.status_code}')
    print(f'Content-Type: {resp.headers.get("Content-Type")}')
    print(f'Content length: {len(resp.content)}')
    if resp.status_code == 200 and len(resp.content) > 0:
        print('First 200 chars:')
        print(resp.content[:200].decode('utf-8', errors='ignore'))
except Exception as e:
    print(f'Error: {e}')