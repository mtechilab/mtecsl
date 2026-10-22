/* MTeC UI behaviour: native <dialog> drawers and modals. No dependencies. */
document.addEventListener('click', e => {
  const open = e.target.closest('[data-open]');
  if (open) { const d = document.getElementById(open.dataset.open); d.showModal(); open.setAttribute('aria-expanded','true'); d._opener = open; return; }
  if (e.target.closest('[data-close]')) { e.target.closest('dialog').close(); return; }
  if (e.target.matches('dialog')) e.target.close(); // click on backdrop
});
document.addEventListener('close', e => {
  const o = e.target._opener; if (o) { o.setAttribute('aria-expanded','false'); o.focus(); }
}, true);
