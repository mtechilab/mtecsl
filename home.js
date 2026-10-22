/* Homepage behaviour: dynamic year + news loader with loading / empty / error states. */
document.getElementById('year').textContent = new Date().getFullYear();

const box = document.getElementById('news');
const fmt = new Intl.DateTimeFormat('en-GB', { day: 'numeric', month: 'short', year: 'numeric' });

function el(tag, attrs = {}, kids = []) {
  const n = document.createElement(tag);
  for (const [k, v] of Object.entries(attrs)) n.setAttribute(k, v);
  for (const c of [].concat(kids)) n.append(c);
  return n;
}
function card(a) {
  const when = new Date(a.date);
  const link = el('a', { href: a.url || '/news/' }, a.title);
  const body = el('div', { class: 'card__body' }, [
    el('div', { class: 'meta' }, el('time', { datetime: a.date }, isNaN(when) ? '' : fmt.format(when))),
    el('h3', { class: 'card__title' }, link),
    el('p', {}, a.excerpt || ''),
    el('span', { class: 'more', 'aria-hidden': 'true' }, 'Read more')
  ]);
  const kids = [];
  if (a.image) kids.push(el('img', { class: 'card__media', src: a.image, alt: '', loading: 'lazy', width: '640', height: '360' }));
  link.setAttribute('aria-label', 'Read more: ' + a.title);
  return el('article', { class: 'card' }, kids.concat(body));
}
function show(node) { box.replaceChildren(node); box.removeAttribute('aria-busy'); }

async function loadNews() {
  box.setAttribute('aria-busy', 'true');
  box.replaceChildren(el('div', { class: 'grid', role: 'status' }, [
    el('span', { class: 'visually-hidden' }, 'Loading news'),
    el('div', { class: 'skeleton', style: 'height:12rem' }), el('div', { class: 'skeleton', style: 'height:12rem' }), el('div', { class: 'skeleton', style: 'height:12rem' })
  ]));
  try {
    const res = await fetch('/data/news.json', { cache: 'no-cache' });
    if (!res.ok) throw new Error(res.status);
    const items = (await res.json()).sort((a, b) => new Date(b.date) - new Date(a.date)).slice(0, 3);
    if (!items.length) {
      show(el('div', { class: 'state' }, [
        el('h3', {}, 'No announcements yet'),
        el('p', {}, 'New notices will appear here. In the meantime, you can apply or ask us a question.'),
        el('a', { class: 'btn btn--ghost', href: '/contact/' }, 'Contact us')
      ]));
    } else show(el('div', { class: 'grid' }, items.map(card)));
  } catch {
    const retry = el('button', { class: 'btn btn--ghost', type: 'button' }, 'Try again');
    retry.addEventListener('click', loadNews);
    show(el('div', { class: 'notice notice--error', role: 'alert' }, [
      el('p', {}, [el('strong', {}, 'News could not be loaded. '), 'Check your connection and try again. ']), retry
    ]));
  }
}
loadNews();
