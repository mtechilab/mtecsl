#!/usr/bin/env python3
"""Structural checks on dist/: balanced HTML, every internal link/asset exists, no placeholder links.
Usage: python3 tools/check_links.py [dist]"""
import sys, re, pathlib, html.parser
root = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else 'dist'); bad = []
class P(html.parser.HTMLParser):
    def __init__(s): super().__init__(); s.st = []; s.err = 0
    def handle_starttag(s, t, a):
        if t not in ('meta', 'link', 'img', 'br', 'input', 'source', 'hr'): s.st.append(t)
    def handle_endtag(s, t):
        if not s.st or s.st.pop() != t: s.err += 1
pages = list(root.rglob('*.html'))
for f in pages:
    s = f.read_text(); p = P(); p.feed(s)
    if p.err or p.st: bad.append(f'{f}: unbalanced tags {p.err} {p.st}')
    if 'href="#"' in s: bad.append(f'{f}: placeholder href')
    ids = set(re.findall(r'id="([^"]+)"', s))
    for h in re.findall(r'(?:href|src)="(/[^"#?]*)', s):
        t = root / h.lstrip('/'); t = t / 'index.html' if h.endswith('/') else t
        if not t.exists(): bad.append(f'{f}: missing {h}')
    for h in re.findall(r'(?:srcset|imagesrcset)="([^"]+)"', s):
        for u in re.findall(r'(/\S+?)\s+\d+w', h):
            if not (root / u.lstrip('/')).exists(): bad.append(f'{f}: missing srcset {u}')
    for h in re.findall(r'href="#([^"]+)"', s):
        if h not in ids: bad.append(f'{f}: bad anchor #{h}')
print(len(pages), 'pages checked;', 'PROBLEMS:' if bad else 'no problems', *bad, sep='\n  ' if bad else ' ')
sys.exit(1 if bad else 0)
