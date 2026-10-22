# Integration with the MTeC application system

## Decision: Option A (link to the existing form)
The website sends applicants to `https://mtec-payment-backend.onrender.com/apply`. No application data passes through the public website.

## Verified (fetched 21 Oct 2026)
- `GET /apply` returns **HTML** (`text/html; charset=UTF-8`), a complete one-page flow: application form, success panel (application number + PIN), fee payment (Orange Money reference or cash + receipt photo, JPG/PNG/WEBP up to 5 MB), status check, acceptance letter download.
- Form fields: first/middle/last name, gender, date of birth, programme, level (Certificate/Diploma), academic year, intake, address, district, town, mobile, email (optional), up to 5 schools, enrollment category, guardian details, declaration + typed signature + date.
- `GET /` returns a client error (4xx): there is no public landing page on the backend root.

## Not verifiable from here (needs the backend owner)
Form `action`/method or any JSON endpoints behind the page, field names, validation rules, authentication on status/letter, error responses, CORS configuration, rate limiting, source code or API docs. I did not submit test data to the live system.
Run `python3 tools/check_backend.py` (read-only, no POST) from a machine with internet and share the output.

## Why not Option B yet
A website-hosted form would need a documented API and CORS permission. Guessing field names against a live admissions and payment system could create bad records or lock out applicants. Until the items below exist, the existing form stays the single source of truth.

## Backend changes needed for a website-hosted form (Option C)
1. Documented endpoint, e.g. `POST /api/applications` (JSON), plus OpenAPI/field list and error format (HTTP 400/422 with per-field messages).
2. CORS allowlist for the production website origin only (not `*`).
3. Server-side validation and duplicate protection (idempotency key or phone + DOB check); rate limiting.
4. Programme and intake list endpoint (`GET /api/programmes`) so the site and form stay in sync.
5. Success response returning the real application number and PIN; the site must display only that.
6. Payment status only from the backend or Orange Money confirmation, never from a frontend message.
7. Security headers (HSTS, X-Content-Type-Options, frame protection) and no secrets in the repo.
8. Optional: query parameters on `/apply` (e.g. `?programme=`) to preselect a programme from website pages.

## What the website does
- Buttons link to `/apply` (verified destination).
- `warmup.js` (admissions and student-portal pages only) sends one anonymous GET to `/apply` after load so a sleeping server starts earlier. It reads no response, sends no data or cookies, and is skipped when Save-Data is on.
- No browser storage, no secrets, no invented reference numbers or payment claims.

## Test plan (on the live system, by staff)
Successful submit; missing required fields; invalid phone/email; double-tap submit; offline/slow network; backend sleeping (first load); payment by Orange Money and by cash receipt; status check with wrong PIN.
