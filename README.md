# MTeC website
Static site, no dependencies. `python3 build.py` writes `dist/`. Deploy `dist/` to Cloudflare Pages or Netlify
(build command `python3 build.py`, output directory `dist`). Serve from the domain root (assets use /paths).

Edit content in `data/`:
- `programmes.json`: add summary, level, duration, fee, requirements per programme once confirmed (empty = hidden).
- `news.json`: array of {slug,title,date:"YYYY-MM-DD",category,excerpt,image,body:["paragraph",...]}.
- `site.json`: mission, vision, history, hours, documents (empty = section hidden). contact_form_endpoint is unused.
Add photos: `assets/hero.jpg`, `assets/campus.jpg` (optional; hidden when missing).

## Performance
- Photos: put originals in `assets-src/hero.jpg` and `assets-src/campus.jpg`. `build.py` creates 480/800/1280px WebP plus a JPEG fallback, adds width/height (no layout shift), preloads the hero and lazy-loads the rest. Without these files the sections simply omit the image.
- CSS is bundled and minified into one file; all CSS/JS/image outputs are fingerprinted under `/_a/` and cached for a year (`_headers`).
- `sw.js` caches only public same-origin pages and assets for offline use. It never touches the student system and stores no personal data.
- Tests: `tools/lighthouse.sh <name> <path>` (needs `npm i lighthouse`) and `tools/browser_checks.py` (Playwright). Serve `dist/` on port 8123 first.

## SEO and sharing
- Canonical origin is configurable. Set `SITE_URL=https://your-site.pages.dev` as a build environment variable (Cloudflare Pages / Netlify), or put it in `data/site.json` as `"origin"`. When set, the build adds canonical URLs, absolute Open Graph image URLs, breadcrumb structured data, `sitemap.xml` and the `Sitemap:` line in `robots.txt`. When empty, those are skipped (a warning is printed).
- Change the origin again when a custom domain is bought, then rebuild and resubmit the sitemap.
- `tools/make_brand_assets.py` regenerates favicon, app icons and the 1200x630 sharing image from `assets-src/crest.png` (outputs are committed in `assets/`).
- Verify before deploying: `SITE_URL=https://your-site.pages.dev python3 build.py && python3 tools/verify_seo.py dist https://your-site.pages.dev`
- `noindex` is set on the 404 and offline pages. Structured data is limited to the organisation (name, address, phone, email, slogan) and breadcrumbs; no ratings, reviews, awards, accreditation or student numbers.

## Deploying
See `DEPLOY.md` (Cloudflare Pages steps, limits, test checklist, rollback, custom domain). CI: `.github/workflows/ci.yml`. Build: `pip install -r requirements.txt && python3 build.py` -> `dist/`.
