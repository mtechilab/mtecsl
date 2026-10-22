/* Filters the programme list in place. The full list is in the HTML, so it works without JS too. */
const q = document.getElementById('q'), cat = document.getElementById('cat');
const items = [...document.querySelectorAll('[data-name]')];
const count = document.getElementById('count'), none = document.getElementById('none');
function run() {
  const t = q.value.trim().toLowerCase(), c = cat.value; let n = 0;
  for (const el of items) {
    const ok = (!c || el.dataset.cat === c) && (!t || el.dataset.name.includes(t));
    el.hidden = !ok; if (ok) n++;
  }
  count.textContent = n + (n === 1 ? ' programme' : ' programmes') + ' shown';
  none.hidden = n > 0;
}
q.addEventListener('input', run); cat.addEventListener('change', run);
const p = new URLSearchParams(location.search).get('category');
if (p) cat.value = p; run();
