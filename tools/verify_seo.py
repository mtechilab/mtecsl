#!/usr/bin/env python3
"""Checks dist/ for SEO problems. Usage: python3 tools/verify_seo.py [dist] [origin]  (origin optional; must match the SITE_URL used for the build)"""
import sys, re, json, pathlib, html.parser
from urllib.parse import urlparse
root = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else 'dist'); origin = (sys.argv[2] if len(sys.argv) > 2 else '').rstrip('/')
errs, warns = [], []
def err(m): errs.append(m)
class P(html.parser.HTMLParser):
    def __init__(s): super().__init__(); s.t = ''; s.in_t = False; s.meta = {}; s.links = []; s.h = []; s.imgs = []; s.ld = []; s.in_ld = False; s.a = []
    def handle_starttag(s, t, a):
        a = dict(a)
        if t == 'title': s.in_t = True
        elif t == 'meta': s.meta[a.get('name') or a.get('property')] = a.get('content')
        elif t == 'link': s.links.append(a)
        elif t in ('h1', 'h2', 'h3', 'h4'): s.h.append(int(t[1]))
        elif t == 'img': s.imgs.append(a)
        elif t == 'a': s.a.append(a.get('href'))
        elif t == 'script' and a.get('type') == 'application/ld+json': s.in_ld = True; s.ld.append('')
    def handle_endtag(s, t):
        if t == 'title': s.in_t = False
        if t == 'script': s.in_ld = False
    def handle_data(s, d):
        if s.in_t: s.t += d
        if s.in_ld: s.ld[-1] += d
pages = {}
for f in sorted(root.rglob('*.html')):
    path = '/' + str(f.relative_to(root).parent) + '/' if f.name == 'index.html' else '/' + f.name
    path = path.replace('/./', '/') if path != '//' else '/'
    p = P(); p.feed(f.read_text()); pages[path] = (f, p)
titles = {}
for path, (f, p) in pages.items():
    noindex = 'noindex' in (p.meta.get('robots') or '')
    t = p.t.strip(); titles.setdefault(t, []).append(path)
    if not t or len(t) > 65: err(f'{path}: title length {len(t)}')
    d = p.meta.get('description') or ''
    if not noindex and not 50 <= len(d) <= 165: err(f'{path}: description length {len(d)}')
    if p.h.count(1) != 1: err(f'{path}: {p.h.count(1)} h1')
    for a, b in zip(p.h, p.h[1:]):
        if b > a + 1: err(f'{path}: heading jump h{a} -> h{b}')
    for im in p.imgs:
        if 'alt' not in im: err(f'{path}: img without alt {im.get("src")}')
    can = [l for l in p.links if l.get('rel') == 'canonical']
    if origin and not noindex:
        if len(can) != 1 or can[0]['href'] != origin + path: err(f'{path}: canonical {[c["href"] for c in can]}')
        if p.meta.get('og:url') != origin + path: err(f'{path}: og:url')
        img = p.meta.get('og:image') or ''
        if not img.startswith(origin + '/') or not (root / urlparse(img).path.lstrip('/')).exists(): err(f'{path}: og:image missing/relative {img}')
    if not origin and can: err(f'{path}: canonical present without origin')
    if not p.meta.get('og:title') or not p.meta.get('og:description'): err(f'{path}: og tags')
    if noindex and path not in ('/404.html', '/offline.html'): err(f'{path}: unexpected noindex')
    if not noindex and path in ('/404.html', '/offline.html'): err(f'{path}: should be noindex')
    for j in p.ld:
        try: o = json.loads(j)
        except Exception as e: err(f'{path}: invalid JSON-LD {e}'); continue
        flat = json.dumps(o)
        if re.search(r'"[^"]*(rating|review|award|accredit|numberOf|alumni)[^"]*"\s*:', flat, re.I) or re.search(r'accredit|recogni[sz]ed|award', flat, re.I): err(f'{path}: JSON-LD contains risky claim keys/values')
    for h in p.a:
        if h in ('#', '', None): err(f'{path}: empty/placeholder link')
for t, ps in titles.items():
    if len(ps) > 1: err(f'duplicate title "{t}": {ps}')
# sitemap / robots / manifest
rob = (root / 'robots.txt').read_text()
sm = root / 'sitemap.xml'
if origin:
    if not sm.exists(): err('sitemap.xml missing')
    else:
        locs = re.findall(r'<loc>(.*?)</loc>', sm.read_text())
        expect = {origin + p for p, (f, q) in pages.items() if 'noindex' not in (q.meta.get('robots') or '')}
        if set(locs) != expect: err(f'sitemap mismatch: missing {sorted(expect - set(locs))[:3]} extra {sorted(set(locs) - expect)[:3]}')
        if len(locs) != len(set(locs)): err('sitemap duplicates')
        if f'Sitemap: {origin}/sitemap.xml' not in rob: err('robots.txt lacks Sitemap line')
        print(f'sitemap: {len(locs)} URLs')
else:
    if sm.exists(): err('sitemap present without origin')
    warns.append('no origin: canonical, sitemap and absolute og:image not checked')
m = json.loads((root / 'manifest.webmanifest').read_text())
for i in m['icons']:
    if not (root / i['src'].lstrip('/')).exists(): err(f'manifest icon missing {i["src"]}')
for need in ('favicon.ico', 'assets/apple-touch-icon.png', 'assets/og-image.jpg', '404.html'):
    if not (root / need).exists(): err(f'missing {need}')
print(f'{len(pages)} pages checked;', 'ERRORS:' if errs else 'no errors', *errs, sep='\n  ' if errs else ' ')
for w in warns: print('note:', w)
sys.exit(1 if errs else 0)
