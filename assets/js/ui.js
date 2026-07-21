// Chrome that has nothing to do with genealogy: theme switch, hover card, tabs.

FamilyTree.initTheme = function (btn) {
  const mq = window.matchMedia('(prefers-color-scheme: dark)');
  const labels = { auto: '🖥 Auto', light: '☀ Light', dark: '🌙 Dark' };
  const order = { auto: 'light', light: 'dark', dark: 'auto' };
  let mode = 'auto';

  function apply() {
    const dark = mode === 'dark' || (mode === 'auto' && mq.matches);
    document.body.classList.toggle('dark', dark);
    btn.textContent = labels[mode];
    btn.title = 'Theme: ' + mode + (mode === 'auto' ? (mq.matches ? ' → dark' : ' → light') : '');
  }

  btn.onclick = () => {
    mode = order[mode];
    apply();
  };
  mq.addEventListener('change', () => mode === 'auto' && apply());
  apply();
};

FamilyTree.initTooltip = function (el, contentFor) {
  document.addEventListener('mouseover', e => {
    const target = e.target.closest('[data-id]');
    if (!target) return;
    const html = contentFor(target.getAttribute('data-id'));
    if (!html) return;
    el.innerHTML = html;
    el.style.display = 'block';
  });

  document.addEventListener('mousemove', e => {
    if (el.style.display !== 'block') return;
    const r = el.getBoundingClientRect();
    let x = e.clientX + 16;
    let y = e.clientY + 16;
    if (x + r.width > window.innerWidth - 8) x = e.clientX - r.width - 16;
    if (y + r.height > window.innerHeight - 8) y = window.innerHeight - r.height - 8;
    el.style.left = Math.max(6, x) + 'px';
    el.style.top = Math.max(6, y) + 'px';
  });

  document.addEventListener('mouseout', e => {
    if (e.target.closest('[data-id]')) el.style.display = 'none';
  });
};

FamilyTree.initTabs = function () {
  const show = view => {
    document.querySelectorAll('.tab').forEach(t => t.classList.toggle('active', t.dataset.view === view));
    document.querySelectorAll('.view').forEach(v => v.classList.remove('active'));
    document.getElementById('view-' + view).classList.add('active');
  };
  document.querySelectorAll('.tab').forEach(t => (t.onclick = () => show(t.dataset.view)));
  return show;
};
