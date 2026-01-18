import os
import json
import urllib.request
import urllib.error
import urllib.parse

BASE = os.environ.get('BASE_URL', 'http://127.0.0.1:5000')
TIMEOUT = 10

headers = {'Content-Type': 'application/json'}

endpoints = [
    ('GET', '/health'),
    ('GET', '/health/config'),
    ('GET', '/health/services'),
    ('GET', '/api/trends'),
    ('GET', '/api/products'),
    ('POST', '/api/products/analyze'),
    ('POST', '/api/products/match-trends'),
    ('POST', '/api/products/match-and-generate'),
    ('POST', '/admin/graphql'),
]


def call(method, path, body=None):
    url = BASE.rstrip('/') + path
    data = None
    req_headers = headers.copy()
    if body is not None:
        data = json.dumps(body).encode('utf-8')
    req = urllib.request.Request(url, data=data, headers=req_headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
            text = resp.read().decode('utf-8', errors='replace')
            print(f"{method} {path} -> {resp.status} {resp.reason}")
            snippet = text[:1000]
            print(snippet)
            try:
                parsed = json.loads(text)
                return parsed
            except Exception:
                return text
    except urllib.error.HTTPError as e:
        print(f"{method} {path} -> HTTPError {e.code}")
        try:
            err = e.read().decode('utf-8', errors='replace')
            print(err[:1000])
        except Exception:
            pass
    except Exception as e:
        print(f"{method} {path} -> Exception: {e}")


if __name__ == '__main__':
    print('Base URL:', BASE)
    results = {}

    # Run initial endpoints
    for method, path in endpoints:
        body = None
        if path == '/admin/graphql':
            body = {"query": "{ shop { name myshopifyDomain } }"}
        if method == 'POST' and body is None:
            body = {}
        results[path] = call(method, path, body)
        print('\n' + '-' * 60 + '\n')

    # If products returned, pick first product id for product-specific tests
    products = results.get('/api/products')
    product_id = None
    if isinstance(products, dict) and products.get('products'):
        p0 = products['products'][0]
        product_id = p0.get('id') or p0.get('gid') or p0.get('handle') or p0.get('id')

    if product_id:
        print('Using product id:', product_id)
        # ensure proper path encoding
        pid = urllib.parse.quote(product_id, safe='')
        call('POST', f'/api/products/{pid}/analyze', {})
        print('\n' + '-' * 60 + '\n')
        call('POST', f'/api/products/{pid}/apply', {'dry_run': True})
        print('\n' + '-' * 60 + '\n')
        call('POST', f'/api/products/{pid}/generate-marketing', {'trend_id': ''})
        print('\n' + '-' * 60 + '\n')

    # Trends detail if available
    trends = results.get('/api/trends')
    if isinstance(trends, dict) and trends.get('trends'):
        t0 = trends['trends'][0]
        trend_id = t0.get('id')
        if trend_id:
            call('GET', f'/api/trends/{trend_id}')

    print('\nDone.')
