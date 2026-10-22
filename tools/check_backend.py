#!/usr/bin/env python3
"""Read-only contract check for the MTeC application system. Never sends POST or personal data.
Usage: python3 tools/check_backend.py [base_url] [website_origin]
Run it from a machine with internet access and share the output with the backend owner."""
import sys, time, urllib.request, urllib.error
base = (sys.argv[1] if len(sys.argv) > 1 else 'https://mtec-payment-backend.onrender.com').rstrip('/')
origin = sys.argv[2] if len(sys.argv) > 2 else 'https://example-mtec-site.pages.dev'
def call(method, path, headers=None):
    req = urllib.request.Request(base + path, method=method, headers=headers or {})
    t = time.time()
    try:
        with urllib.request.urlopen(req, timeout=60) as r: return r.status, r.headers, time.time() - t, r.read(2000).decode('utf-8', 'replace')
    except urllib.error.HTTPError as e: return e.code, e.headers, time.time() - t, ''
    except Exception as e: return None, {}, time.time() - t, str(e)
s, h, dt, body = call('GET', '/apply')
print(f'GET /apply -> {s} in {dt:.1f}s, content-type: {h.get("Content-Type")}')
print('  looks like HTML form page:', '<form' in body.lower() or '<html' in body.lower(), '(first 2 KB only)')
for p in ('/', '/openapi.json', '/docs', '/health'):
    s2, h2, _, _ = call('GET', p); print(f'GET {p} -> {s2}')
s, h, _, _ = call('OPTIONS', '/apply', {'Origin': origin, 'Access-Control-Request-Method': 'POST', 'Access-Control-Request-Headers': 'content-type'})
print(f'OPTIONS /apply (preflight from {origin}) -> {s}')
for k in ('Access-Control-Allow-Origin', 'Access-Control-Allow-Methods', 'Access-Control-Allow-Headers', 'Allow'):
    print(f'  {k}: {h.get(k)}')
s, h, _, _ = call('GET', '/apply', {'Origin': origin})
print('GET with Origin -> Access-Control-Allow-Origin:', h.get('Access-Control-Allow-Origin'))
print('Security headers on /apply:', {k: h.get(k) for k in ('Strict-Transport-Security', 'X-Content-Type-Options', 'X-Frame-Options', 'Content-Security-Policy')})
