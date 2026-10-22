/* Helpers for links to the separately hosted application system.
   1) On the admissions and student-portal pages, send one anonymous GET to wake the server (no data, no cookies, response unread; skipped when Save-Data is on).
   2) If the phone is offline when someone taps an application link, explain it instead of showing a browser error page. */
(() => {
  const m = document.querySelector('meta[name="apply-url"]');
  if (!m) return;
  const APPLY = m.content, BASE = new URL(APPLY).origin + '/';
  let done = false;
  function warm() {
    if (done || (navigator.connection && navigator.connection.saveData) || navigator.onLine === false) return;
    done = true;
    fetch(APPLY, { mode: 'no-cors', cache: 'no-store', credentials: 'omit', referrerPolicy: 'no-referrer' }).catch(() => {});
  }
  if (/^\/(admissions|student-portal)\//.test(location.pathname)) addEventListener('load', () => setTimeout(warm, 1500));
  document.addEventListener('pointerdown', e => { if (e.target.closest('a[href^="' + BASE + '"]')) warm(); });
  document.addEventListener('click', e => {
    if (!e.target.closest('a[href^="' + BASE + '"]') || navigator.onLine !== false) return;
    e.preventDefault();
    let n = document.getElementById('offline-note');
    if (!n) {
      n = document.createElement('div'); n.id = 'offline-note'; n.className = 'wrap';
      n.innerHTML = '<div class="notice notice--error" role="alert" tabindex="-1"><p><strong>You appear to be offline.</strong> Connect to the internet, then tap the button again.</p></div>';
      document.getElementById('main').prepend(n);
    }
    n.firstChild.focus(); n.scrollIntoView({ block: 'center' });
  });
})();
