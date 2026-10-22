#!/usr/bin/env python3
"""Static site build: python3 build.py -> dist/. Clean URLs (/about/ = dist/about/index.html)."""
import json, re, shutil, html, pathlib, hashlib, io, os
E = html.escape
ROOT = pathlib.Path(__file__).parent; OUT = ROOT / 'dist'
shutil.rmtree(OUT, ignore_errors=True)
DEFAULT_APPLY = "https://mtec-payment-backend.onrender.com/apply"
EMAIL, PHONE, TEL = "mtec.sierraleone@gmail.com", "+232 76 866 665", "+23276866665"
ADDR = "53 Station Road, Makeni City, Bombali District"
MAP = "https://www.google.com/maps/search/?api=1&query=53+Station+Road+Makeni+Sierra+Leone"
DIR = "https://www.google.com/maps/dir/?api=1&destination=53+Station+Road+Makeni+Sierra+Leone"
site = json.load(open(ROOT/'data/site.json')); P = json.load(open(ROOT/'data/programmes.json'))
news = sorted(json.load(open(ROOT/'data/news.json')), key=lambda a: a['date'], reverse=True)
# Canonical origin: set env SITE_URL or data/site.json "origin" (e.g. https://mtec.pages.dev). Empty = no canonical/sitemap/absolute social URLs.
ORIGIN = (os.environ.get('SITE_URL') or site.get('origin') or '').strip().rstrip('/')
# Application system URL (separate backend). Override with env APPLY_URL or data/site.json "apply_url".
APPLY = (os.environ.get('APPLY_URL') or site.get('apply_url') or DEFAULT_APPLY).strip()
# Student app download (APK). Override with env APP_URL or data/site.json "app_url".
DEFAULT_APP = "https://sanad-sl.org/mtecapp/mtec-student-app.apk"
APP = (os.environ.get('APP_URL') or site.get('app_url') or DEFAULT_APP).strip()
LC = []
NOINDEX = ('/404', '/offline')
ORG_DESC = 'Practical technical, vocational, business and technology education in Makeni, Sierra Leone.'
CAT = {c['id']: c['name'] for c in P['categories']}
LINK = {'index.html':'/','about.html':'/about/','programmes.html':'/programmes/','admissions.html':'/admissions/',
        'news.html':'/news/','portal.html':'/student-portal/','contact.html':'/contact/'}
def fix(s):
    for k, v in LINK.items(): s = s.replace(f'href="{k}"', f'href="{v}"')
    s = re.sub(r'(src|srcset)="assets/', r'\1="/assets/', s).replace(', assets/', ', /assets/')
    return s.replace(' aria-current="page"', '').replace(DEFAULT_APPLY, APPLY)
home = fix((ROOT/'templates/home.html').read_text())
home = home.replace('<a class="btn btn--ghost" href="/student-portal/">Student portal</a>', '<a class="btn btn--ghost" href="/student-portal/">Student portal</a>\n      ' + f'<a class="btn btn--ghost mtec-download-button" href="{APP}" download rel="noopener">\U0001F4F1 Download MTeC Student App</a>', 1)
HEADER = home[home.index('<div class="contact-strip'):home.index('</dialog>')+9]
FOOTER = home[home.index('<footer'):home.index('</footer>')+9]
HOME_MAIN = home[home.index('<main id="main">')+16:home.index('</main>')]

# ---- fingerprinted assets (served from /_a/ with immutable caching) ----
FP = {}
def emit(name, data=None):
    b = data if data is not None else (ROOT/name).read_bytes()
    stem, ext = name.rsplit('.', 1); h = hashlib.sha1(b).hexdigest()[:8]
    (OUT/'_a').mkdir(parents=True, exist_ok=True); (OUT/'_a'/f'{stem}.{h}.{ext}').write_bytes(b)
    return f'/_a/{stem}.{h}.{ext}'
def mincss(c):
    c = re.sub(r'/\*.*?\*/', '', c, flags=re.S); c = re.sub(r'\s+', ' ', c)
    return re.sub(r'\s*([{};,])\s*', r'\1', c).replace(';}', '}')
FP['site.css'] = emit('site.css', mincss(''.join((ROOT/f).read_text() for f in ('mtec.css', 'home.css', 'pages.css'))).encode())
for j in ('mtec.js', 'home.js', 'programmes.js', 'warmup.js'): FP[j] = emit(j)
# ---- responsive images: put originals in assets-src/ (hero.jpg, campus.jpg); WebP + JPEG fallback are generated ----
def picture(src, alt, sizes, cls='', eager=False, widths=(480, 800, 1280)):
    f = ROOT/'assets-src'/src
    if not f.exists(): return '', ''
    from PIL import Image  # only needed when photos are present
    im = Image.open(f).convert('RGB'); W, H = im.size
    ws = [w for w in widths if w <= W] or [W]; urls = []
    for w in ws:
        r = im.resize((w, round(H*w/W)), Image.LANCZOS); b = io.BytesIO(); r.save(b, 'WEBP', quality=72, method=6)
        urls.append((emit(f'{f.stem}-{w}.webp', b.getvalue()), w))
    mid = min(ws, key=lambda w: abs(w-800)); b = io.BytesIO()
    im.resize((mid, round(H*mid/W)), Image.LANCZOS).save(b, 'JPEG', quality=72, optimize=True, progressive=True)
    jpg = emit(f'{f.stem}-{mid}.jpg', b.getvalue()); ss = ', '.join(f'{u} {w}w' for u, w in urls); hh = round(H*ws[-1]/W)
    tag = (f'<picture><source type="image/webp" srcset="{ss}" sizes="{sizes}"><img{" class=%s" % chr(34)+cls+chr(34) if cls else ""} src="{jpg}" alt="{E(alt)}" width="{ws[-1]}" height="{hh}" '
           + ('fetchpriority="high"' if eager else 'loading="lazy" decoding="async"') + '></picture>')
    pre = f'<link rel="preload" as="image" type="image/webp" imagesrcset="{ss}" imagesizes="{sizes}" fetchpriority="high">' if eager else ''
    return tag, pre
HERO, HERO_PRELOAD = picture('hero.jpg', '', '100vw', cls='hero__img', eager=True)
CAMPUS_IMG, _ = picture('campus.jpg', 'The MTeC campus in Makeni', '(min-width:62rem) 50vw, 100vw')
HOME_MAIN = re.sub(r'<img class="hero__img"[^>]*>', lambda m: HERO, HOME_MAIN)
HOME_MAIN = re.sub(r'<figure>.*?</figure>', lambda m: f'<figure>{CAMPUS_IMG}</figure>' if CAMPUS_IMG else '', HOME_MAIN, flags=re.S)
SWREG = '<script>"serviceWorker"in navigator&&addEventListener("load",function(){navigator.serviceWorker.register("/sw.js")})</script>'
written = []
def write(path, s):
    f = OUT / path.strip('/') / 'index.html' if path not in ('/404', '/offline') else OUT / (path.strip('/') + '.html')
    s = re.sub(r'<!--.*?-->', '', s, flags=re.S)
    for k, v in FP.items(): s = s.replace(f'"/{k}"', f'"{v}"')
    f.parent.mkdir(parents=True, exist_ok=True); f.write_text(s); written.append(path)
def page(path, title, desc, body, nav=None, extra=''):
    h = HEADER
    if nav: h = h.replace(f'<a href="{nav}">', f'<a aria-current="page" href="{nav}">')
    global LC
    crumbs, LC = LC, []
    full = title if path == '/' else f'{title} | MTeC Makeni'
    url = ORIGIN + path if ORIGIN and path not in NOINDEX else ''
    art = re.fullmatch(r'/news/([^/]+)/', path) and not path.startswith('/news/page/')
    meta = f'<meta name="description" content="{E(desc)}"><meta name="apply-url" content="{E(APPLY)}">'
    if path in NOINDEX: meta += '<meta name="robots" content="noindex,follow">'
    if url: meta += f'<link rel="canonical" href="{url}">'
    meta += f'<meta property="og:site_name" content="MTeC"><meta property="og:title" content="{E(full)}"><meta property="og:description" content="{E(desc)}"><meta property="og:type" content="{"article" if art else "website"}">'
    if url: meta += f'<meta property="og:url" content="{url}">'
    if ORIGIN:
        meta += (f'<meta property="og:image" content="{ORIGIN}/assets/og-image.jpg"><meta property="og:image:width" content="1200"><meta property="og:image:height" content="630">'
                 '<meta property="og:image:alt" content="MTeC crest with the name Makeni Technical College of Innovation &amp; Technology and the slogan Skills for Innovation"><meta name="twitter:card" content="summary_large_image">')
    ld = []
    if path == '/':
        org = {"@context": "https://schema.org", "@type": "EducationalOrganization", "name": "Makeni Technical College of Innovation & Technology", "alternateName": "MTeC",
               "slogan": "SKILLS FOR INNOVATION.", "description": ORG_DESC, "telephone": TEL, "email": EMAIL,
               "address": {"@type": "PostalAddress", "streetAddress": "53 Station Road", "addressLocality": "Makeni", "addressRegion": "Bombali District", "addressCountry": "SL"}}
        if ORIGIN: org.update({"url": ORIGIN + "/", "logo": ORIGIN + "/assets/icon-512.png"})
        ld.append(org)
    if ORIGIN and len(crumbs) > 1 and path not in NOINDEX:
        ld.append({"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [
            {"@type": "ListItem", "position": i + 1, "name": n, "item": ORIGIN + h} for i, (h, n) in enumerate(crumbs)]})
    ldhtml = ''.join('<script type="application/ld+json">' + json.dumps(o, ensure_ascii=False).replace('</', '<\\/') + '</script>' for o in ld)
    icons = '<link rel="icon" href="/favicon.ico" sizes="48x48"><link rel="icon" href="/assets/icon-192.png" type="image/png" sizes="192x192"><link rel="apple-touch-icon" href="/assets/apple-touch-icon.png"><link rel="manifest" href="/manifest.webmanifest">'
    write(path, f'''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>{E(full)}</title>{meta}
<meta name="theme-color" content="#062B5B">{icons}{ldhtml}
<link rel="stylesheet" href="/site.css">
<script src="/mtec.js" defer></script><script src="/warmup.js" defer></script>{extra}</head><body>
<a class="skip" href="#main">Skip to main content</a>
{h}
<main id="main">{body}</main>
{FOOTER}{SWREG}</body></html>''')
def head(title, lead, crumbs):
    global LC
    LC = [('/', 'Home')] + list(crumbs)
    c = ''.join(f'<li><a href="{h}">{E(t)}</a></li>' for h, t in crumbs[:-1]) + f'<li aria-current="page">{E(crumbs[-1][1])}</li>'
    return f'<div class="page-head"><div class="wrap"><nav class="crumbs" aria-label="Breadcrumb"><ol><li><a href="/">Home</a></li>{c}</ol></nav><h1>{E(title)}</h1>' + (f'<p>{E(lead)}</p>' if lead else '') + '</div></div>'
def sec(inner, tint=False, h=None):
    return f'<section class="section{" section--tint" if tint else ""}"><div class="wrap">' + (f'<div class="section-head"><h2>{h}</h2></div>' if h else '') + inner + '</section>'.replace('</section>', '</div></section>')
def btn(href, label, cls=''): return f'<a class="btn {cls}" href="{href}">{label}</a>'
def appbtn(cls='btn--gold'): return f'<a class="btn mtec-download-button {cls}" href="{E(APP)}" download rel="noopener">\U0001F4F1 Download MTeC Student App</a>'
def facts(p):
    rows = [(k, p[v]) for k, v in (('Level','level'),('Duration','duration'),('Fee','fee')) if p.get(v)]
    return '<dl class="facts">' + ''.join(f'<div><dt>{k}</dt><dd>{E(v)}</dd></div>' for k, v in rows) + '</dl>' if rows else ''
def pcard(p, h='h3'):
    return (f'<article class="card programme" data-name="{E(p["name"].lower())}" data-cat="{p["category"]}"><div class="card__body"><span class="tag">{CAT[p["category"]].replace("&","&amp;")}</span>'
            f'<{h} class="card__title"><a href="/programmes/{p["slug"]}/">{E(p["name"])}</a></{h}>' + (f'<p>{E(p["summary"])}</p>' if p.get('summary') else '') + facts(p) + '</div></article>')

# HOME
page('/', 'MTeC | Makeni Technical College of Innovation & Technology',
     'Practical technical and vocational training in Makeni, Sierra Leone. Skills for innovation. Apply for admission to MTeC.',
     HOME_MAIN, nav='/', extra=HERO_PRELOAD + '<script src="/home.js" defer></script>')

# ABOUT
cats_html = ''.join(f'<li><a href="/programmes/?category={c}">{E(n)}</a></li>' for c, n in CAT.items())
about = head('About MTeC', 'Practical technical, vocational, business and technology education in Makeni.', [('/about/', 'About MTeC')])
body = '<div class="prose stack"><h2>Who we are</h2><p>Makeni Technical College of Innovation &amp; Technology (MTeC) provides practical technical, vocational, business and technology education in Makeni, Sierra Leone. Our slogan is Skills for Innovation.</p><h2>How we teach</h2><p>Our focus is practical training. Students learn skills they can use for employment, for starting a business, and for innovation.</p><h2>What you can study</h2><ul class="linklist">' + cats_html + '</ul><p>Ready to join? Read <a href="/admissions/">how to apply</a> or <a href="/contact/">contact the college</a>.</p>'
for k, t in (('mission','Mission'),('vision','Vision'),('history','Our history')):
    if site.get(k): body += f'<h2>{t}</h2><p>{E(site[k])}</p>'
body += '</div>'
side = f'<aside class="card"><div class="card__body"><h2 style="font-size:1.125rem">Visit us</h2><p>{ADDR}</p><a href="{DIR}" rel="noopener">Get directions</a></div></aside>'
if CAMPUS_IMG: side = f'<figure style="margin:0 0 var(--s4)">{CAMPUS_IMG}</figure>' + side
page('/about/', 'About the college', 'About Makeni Technical College of Innovation & Technology: practical technical, vocational, business and technology education in Makeni.',
     about + sec(f'<div class="split"><div>{body}</div><div>{side}</div></div>'), nav='/about/')

# PROGRAMMES
opts = '<option value="">All categories</option>' + ''.join(f'<option value="{c}">{E(n)}</option>' for c, n in CAT.items())
flt = (f'<div class="filters"><div class="field"><label for="q">Search programmes</label><input class="input" id="q" type="search" autocomplete="off"></div>'
       f'<div class="field"><label for="cat">Category</label><select class="select" id="cat">{opts}</select></div></div>'
       f'<p id="count" role="status" class="meta">{len(P["programmes"])} programmes shown</p><div class="grid">{"".join(pcard(p, "h2") for p in P["programmes"])}</div>'
       f'<div class="state" id="none" hidden><h3>No programmes match</h3><p>Try a different word or choose all categories.</p></div>')
page('/programmes/', 'Academic Programmes', 'Browse MTeC programmes in computing, business, ICT and technical skills, and creative and vocational training.',
     head('Academic programmes', 'Search or filter by category. Duration, fees and entry requirements appear on each programme once confirmed.', [('/programmes/', 'Academic Programmes')]) + sec(flt),
     nav='/programmes/', extra='<script src="/programmes.js" defer></script>')
for p in P['programmes']:
    f = facts(p) or '<div class="notice"><p><strong>Duration, fees and entry requirements</strong> are not yet listed. Contact admissions for current details.</p></div>'
    rel = ''.join(f'<li><a href="/programmes/{r["slug"]}/">{E(r["name"])}</a></li>' for r in P['programmes'] if r['category'] == p['category'] and r is not p)
    req = f'<h2>Entry requirements</h2><p>{E(p["requirements"])}</p>' if p.get('requirements') else ''
    d = (head(p['name'], CAT[p['category']], [('/programmes/', 'Academic Programmes'), (f'/programmes/{p["slug"]}/', p['name'])]) +
         sec(f'<div class="split"><div class="prose stack">' + (f'<p>{E(p["summary"])}</p>' if p.get('summary') else '') + f + req +
             f'<p>{btn(APPLY, "Apply for admission", "btn--gold")} {btn("/contact/", "Ask admissions", "btn--ghost")}</p><p>Read <a href="/admissions/">how to apply</a> or <a href="/programmes/">browse all programmes</a>.</p></div>'
             f'<aside class="card"><div class="card__body"><h2 style="font-size:1.125rem">More in {E(CAT[p["category"]])}</h2><ul class="linklist">{rel}</ul></div></aside></div>'))
    page(f'/programmes/{p["slug"]}/', f'{p["name"]} programme', f'Study {p["name"]} at MTeC in Makeni, Sierra Leone. Read about the programme and apply online.', d, nav='/programmes/')

# ADMISSIONS
steps = ['Open the online application form and fill in your personal details, the programme and level (certificate or diploma), and your educational history (up to five schools).',
 'Add your parent or guardian details, type your name to sign the declaration, and submit.',
 'Save the application number and PIN shown after you submit. You need both to pay, check your status and download your letter.',
 f'Pay the application fee to {PHONE} by Orange Money (enter the transaction reference), or pay cash and upload a photo of the receipt (JPG, PNG or WEBP, up to 5 MB).',
 'Check your application status and download your acceptance letter from the same system.']
SLOW = '<div class="notice notice--warning"><p><strong>The application form opens on a separate system</strong> and can be slow to load the first time. Please wait, and do not submit twice.</p></div>'
docs = f'<h2>Required documents</h2><p>{E(site["documents"])}</p>' if site.get('documents') else ''
adm = (head('Admissions', 'Apply online, pay the application fee, and track your application.', [('/admissions/', 'Admissions')]) +
  sec('<div class="split"><div class="prose stack"><h2>How to apply</h2><ol class="steps">' + ''.join(f'<li><span>{E(s)}</span></li>' for s in steps) + '</ol>' + SLOW + docs +
      '<h2>Enrollment categories</h2><p>On the form you choose either self-funded student or scholarship / sponsored student. The application fee depends on the programme level you choose and is shown on the form.</p>'
      f'<p>{btn(APPLY, "Apply for admission", "btn--gold")}</p></div>'
      f'<aside class="card"><div class="card__body"><h2 style="font-size:1.125rem">Need help?</h2><p><a href="tel:{TEL}">{PHONE}</a><br><a href="mailto:{EMAIL}">{EMAIL}</a></p><a href="/contact/">Contact page</a></div></aside></div>') +
  sec('<ul class="grid" style="list-style:none;padding:0">' + ''.join(f'<li class="card"><div class="card__body"><h3 class="card__title"><a href="/programmes/?category={c}">{E(n)}</a></h3><p>{sum(1 for p in P["programmes"] if p["category"]==c)} programmes</p></div></li>' for c, n in CAT.items()) + '</ul>', tint=True, h='Available programmes'))
page('/admissions/', 'Admissions', 'How to apply to MTeC: online application, application fee payment, status check and acceptance letter.', adm, nav='/admissions/')

# NEWS
SIZE = 9; pages_n = max(1, -(-len(news)//SIZE))
def ncard(a):
    img = f'<img class="card__media" src="{E(a["image"])}" alt="" loading="lazy" width="640" height="360">' if a.get('image') else ''
    return (f'<article class="card">{img}<div class="card__body"><div class="meta"><time datetime="{a["date"]}">{a["date"]}</time>' + (f'<span class="tag">{E(a["category"])}</span>' if a.get('category') else '') +
            f'</div><h2 class="card__title"><a href="/news/{a["slug"]}/">{E(a["title"])}</a></h2><p>{E(a.get("excerpt",""))}</p></div></article>')
for n in range(1, pages_n+1):
    path = '/news/' if n == 1 else f'/news/page/{n}/'
    chunk = news[(n-1)*SIZE:n*SIZE]
    inner = ('<div class="grid">' + ''.join(map(ncard, chunk)) + '</div>') if chunk else '<div class="state"><h2>No announcements yet</h2><p>New notices will appear here. In the meantime, you can apply or ask us a question.</p><a class="btn btn--ghost" href="/contact/">Contact us</a></div>'
    prev = f'<a class="btn btn--ghost" href="{"/news/" if n==2 else f"/news/page/{n-1}/"}">Newer</a>' if n > 1 else '<span></span>'
    nxt = f'<a class="btn btn--ghost" href="/news/page/{n+1}/">Older</a>' if n < pages_n else '<span></span>'
    if pages_n > 1: inner += f'<nav class="pager" aria-label="News pages">{prev}<span>Page {n} of {pages_n}</span>{nxt}</nav>'
    page(path, 'News & Announcements' + (f' (page {n})' if n > 1 else ''), 'Latest news and announcements from Makeni Technical College of Innovation & Technology (MTeC) in Makeni, Sierra Leone.', head('News & announcements', 'Updates from Makeni Technical College of Innovation & Technology.', [('/news/', 'News & Announcements')]) + sec(inner), nav='/news/')
for a in news:
    img = f'<img src="{E(a["image"])}" alt="" width="960" height="540" style="width:100%;height:auto;border-radius:8px;margin-bottom:var(--s4)">' if a.get('image') else ''
    body = ''.join(f'<p>{E(t)}</p>' for t in a.get('body', [a.get('excerpt', '')]))
    page(f'/news/{a["slug"]}/', a['title'], a.get('excerpt') or a['title'],
         head(a['title'], '', [('/news/', 'News & Announcements'), (f'/news/{a["slug"]}/', a['title'])]) + sec(f'<article class="prose"><p class="meta"><time datetime="{a["date"]}">{a["date"]}</time></p>{img}{body}<p><a href="/news/">All announcements</a></p></article>'), nav='/news/')
for a in news: a['url'] = f'/news/{a["slug"]}/'

# STUDENT PORTAL
portal = (head('Student portal', 'Use the MTeC student system to apply, pay and follow your application.', [('/student-portal/', 'Student Portal')]) +
  sec('<div class="split"><div class="prose stack"><h2>What you can do</h2><ul><li>Submit a new application.</li><li>Pay your application fee with your application number and PIN.</li><li>Check your application status.</li><li>Download your acceptance letter.</li></ul>'
      '<div class="notice"><p><strong>Keep your application number and PIN.</strong> The system asks for both. MTeC cannot recover them from this website.</p></div>'
      f'<p>{btn(APPLY, "Open the student system", "btn--gold")}</p>'
      f'<h2>Student app (Android)</h2><p>Install the MTeC Student App on your Android phone.</p><p>{appbtn("btn--ghost")}</p>'
      '<div class="notice"><p>The app is an APK file. Your phone may ask you to allow installs from your browser. Only download it from this official MTeC page.</p></div>'
      f'<p>The student system opens on its own page and can be slow to open the first time. Please wait for it to load.</p></div>'
      f'<aside class="card"><div class="card__body"><h2 style="font-size:1.125rem">Problem with your PIN?</h2><p>Contact admissions.</p><p><a href="tel:{TEL}">{PHONE}</a><br><a href="mailto:{EMAIL}">{EMAIL}</a></p></div></aside></div>'))
page('/student-portal/', 'Student Portal', 'Open the MTeC student system to apply, pay the application fee, check status and download your acceptance letter.', portal, nav='/student-portal/')

# CONTACT
hours = f'<dt>Opening hours</dt><dd>{E(site["hours"])}</dd>' if site.get('hours') else ''
contact = (head('Contact us', 'Reach MTeC admissions and the college office.', [('/contact/', 'Contact Us')]) +
  sec(f'<div class="card contact-card" style="max-width:36rem"><div class="card__body"><dl><dt>Address</dt><dd>{ADDR}</dd><dt>Telephone</dt><dd><a href="tel:{TEL}">{PHONE}</a></dd><dt>Email</dt><dd><a href="mailto:{EMAIL}">{EMAIL}</a></dd>{hours}</dl>'
      f'<p>{btn(DIR, "Get directions", "btn--gold")} {btn(MAP, "View on map", "btn--ghost")}</p></div></div>'))
page('/contact/', 'Contact Us', 'Contact MTeC in Makeni: address, telephone, email and directions.', contact, nav='/contact/')

# 404
page('/404', 'Page not found', 'This page does not exist.', '<section class="section nf"><div class="wrap"><h1>Page not found</h1><p>The page you opened does not exist or has moved. Use the menu, or go to one of these pages.</p><div class="row">' +
     btn('/', 'Home', 'btn--ghost') + btn('/programmes/', 'Academic programmes', 'btn--ghost') + btn('/admissions/', 'Admissions', 'btn--ghost') + btn('/contact/', 'Contact us', 'btn--ghost') + '</div></div></section>')

# static files
shutil.copytree(ROOT/'assets', OUT/'assets', dirs_exist_ok=True)
(OUT/'data').mkdir(exist_ok=True); json.dump(news, open(OUT/'data/news.json', 'w'))
(OUT/'robots.txt').write_text('User-agent: *\nAllow: /\n' + (f'\nSitemap: {ORIGIN}/sitemap.xml\n' if ORIGIN else ''))
shutil.copy(ROOT/'assets/favicon.ico', OUT/'favicon.ico')
json.dump({"name": "Makeni Technical College of Innovation & Technology", "short_name": "MTeC", "description": ORG_DESC, "start_url": "/", "scope": "/", "display": "browser",
           "theme_color": "#062B5B", "background_color": "#ffffff",
           "icons": [{"src": "/assets/icon-192.png", "sizes": "192x192", "type": "image/png"}, {"src": "/assets/icon-512.png", "sizes": "512x512", "type": "image/png"}]},
          open(OUT/'manifest.webmanifest', 'w'), indent=1)
if ORIGIN:
    dates = {f'/news/{a["slug"]}/': a['date'] for a in news}
    urls = [p for p in written if p not in NOINDEX]
    (OUT/'sitemap.xml').write_text('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' +
        ''.join(f'<url><loc>{E(ORIGIN + p)}</loc>' + (f'<lastmod>{dates[p]}</lastmod>' if p in dates else '') + '</url>\n' for p in urls) + '</urlset>\n')
else:
    print('WARNING: no origin set (SITE_URL or data/site.json "origin"): canonical, sitemap and absolute social-image URLs are skipped.')
print(len(written), 'pages written')

# ---- offline page, service worker, headers ----
page('/offline', 'You are offline', 'You are offline.', '<section class="section nf"><div class="wrap"><h1>You are offline</h1><p>This page is not saved on your phone. Connect to the internet and try again. The application system needs a connection.</p><div class="row"><a class="btn" href="/">Try the home page</a></div></div></section>')
ver = hashlib.sha1(''.join(FP.values()).encode()).hexdigest()[:8]
pre = json.dumps(['/offline.html', FP['site.css'], FP['mtec.js'], FP['warmup.js'], '/assets/mtec-crest-128.webp'])
(OUT/'sw.js').write_text("""/* Public-site service worker. Same-origin GET only. Never touches the student system (other origin) and stores no personal data. */
const V='mtec-%s',PRE=%s;
self.addEventListener('install',e=>e.waitUntil(caches.open(V).then(c=>c.addAll(PRE)).then(()=>self.skipWaiting())));
self.addEventListener('activate',e=>e.waitUntil(caches.keys().then(k=>Promise.all(k.filter(x=>x!==V).map(x=>caches.delete(x)))).then(()=>self.clients.claim())));
const save=(r,res)=>{if(res.ok){const c=res.clone();caches.open(V).then(x=>x.put(r,c))}return res};
self.addEventListener('fetch',e=>{const r=e.request,u=new URL(r.url);
 if(r.method!=='GET'||u.origin!==location.origin)return;
 if(r.mode==='navigate'||u.pathname.startsWith('/data/')){
  e.respondWith(fetch(r).then(res=>save(r,res)).catch(()=>caches.match(r).then(m=>m||(r.mode==='navigate'?caches.match('/offline.html'):Response.error()))));return}
 if(/\\.(css|js|webp|jpg|png|svg)$/.test(u.pathname))e.respondWith(caches.match(r).then(m=>m||fetch(r).then(res=>save(r,res))))});
""" % (ver, pre))
(OUT/'_headers').write_text("""/*
  X-Content-Type-Options: nosniff
  Referrer-Policy: strict-origin-when-cross-origin
  X-Frame-Options: DENY
  Permissions-Policy: camera=(), microphone=(), geolocation=()
/_a/*
  Cache-Control: public, max-age=31536000, immutable
/assets/*
  Cache-Control: public, max-age=604800
/data/*
  X-Robots-Tag: noindex
""")
print('assets:', sorted(p.name for p in (OUT/'_a').iterdir()))
