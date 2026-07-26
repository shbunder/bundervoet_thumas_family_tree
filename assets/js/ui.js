// Chrome that has nothing to do with genealogy: the two round switches, the hover
// card, the tabs, and the segmented controls over the index.

// The theme switch is a single round button that cycles system → light → dark. It
// carries a glyph rather than a word, because the word would need translating and
// the button would then change width in two languages for no gain; what it means is
// in the tooltip and the aria-label, which are translated.
FamilyTree.initTheme = function (btn, i18n) {
  const mq = window.matchMedia('(prefers-color-scheme: dark)');
  const glyph = { auto: '◐', light: '☀', dark: '☾' };
  const name = { auto: 'themeAuto', light: 'themeLight', dark: 'themeDark' };
  const order = { auto: 'light', light: 'dark', dark: 'auto' };
  let mode = 'auto';

  function apply() {
    const dark = mode === 'dark' || (mode === 'auto' && mq.matches);
    document.body.classList.toggle('dark', dark);
    btn.textContent = glyph[mode];
    // On auto, say which way it currently resolves — otherwise the button reads as
    // doing nothing on a machine whose system theme already matches.
    const resolved = mode === 'auto' ? ` → ${i18n.t(dark ? 'themeDark' : 'themeLight')}` : '';
    const title = `${i18n.t('theme')}: ${i18n.t(name[mode])}${resolved}`;
    btn.title = title;
    btn.setAttribute('aria-label', title);
  }

  btn.onclick = () => {
    mode = order[mode];
    apply();
  };
  mq.addEventListener('change', () => mode === 'auto' && apply());
  apply();
  // Handed back so the language switch can relabel it without knowing what mode
  // it is in.
  return apply;
};

// Flags, drawn rather than typed: the flag emoji do not render as flags on Windows,
// where they come out as the two letters of the country code. Which flag stands for
// which language is a choice, and it is made in site/labels.json — this only holds
// the drawings.
FamilyTree.FLAGS = {
  gb:
    '<svg class="flag" viewBox="0 0 60 30" preserveAspectRatio="xMidYMid slice" aria-hidden="true" focusable="false">' +
    '<clipPath id="ftflag-gb-a"><path d="M0,0 v30 h60 v-30 z"/></clipPath>' +
    '<clipPath id="ftflag-gb-b"><path d="M30,15 h30 v15 z v15 h-30 z h-30 v-15 z v-15 h30 z"/></clipPath>' +
    '<g clip-path="url(#ftflag-gb-a)">' +
    '<path d="M0,0 v30 h60 v-30 z" fill="#012169"/>' +
    '<path d="M0,0 L60,30 M60,0 L0,30" stroke="#fff" stroke-width="6"/>' +
    '<path d="M0,0 L60,30 M60,0 L0,30" clip-path="url(#ftflag-gb-b)" stroke="#c8102e" stroke-width="4"/>' +
    '<path d="M30,0 v30 M0,15 h60" stroke="#fff" stroke-width="10"/>' +
    '<path d="M30,0 v30 M0,15 h60" stroke="#c8102e" stroke-width="6"/>' +
    '</g></svg>',
  nl:
    '<svg class="flag" viewBox="0 0 9 6" preserveAspectRatio="xMidYMid slice" aria-hidden="true" focusable="false">' +
    '<rect width="9" height="6" fill="#21468b"/>' +
    '<rect width="9" height="4" fill="#fff"/>' +
    '<rect width="9" height="2" fill="#ae1c28"/></svg>',
};

// The same round button again, showing the flag of the language currently in use.
// With two languages a click is a toggle; with three it walks the list, which is
// why it asks the i18n layer for `next` rather than assuming there are two.
FamilyTree.initLanguage = function (btn, i18n) {
  function apply() {
    const now = i18n.info();
    const then = i18n.info(i18n.next());
    btn.innerHTML = FamilyTree.FLAGS[now.flag] || '';
    const title = `${i18n.t('language')}: ${now.name} — ${i18n.t('switchTo', { lang: then.name })}`;
    btn.title = title;
    btn.setAttribute('aria-label', title);
  }
  btn.onclick = () => i18n.set(i18n.next());
  i18n.onChange(apply);
  apply();
};

// True for a mouse, false for a touchscreen. On touch there is no hover, and a
// tap fires mouseover without a matching mouseout — which would leave the card
// stranded on screen — so the hover card is simply not wired up there.
FamilyTree.canHover = () => window.matchMedia('(hover: hover) and (pointer: fine)').matches;

FamilyTree.initTooltip = function (el, contentFor) {
  if (!FamilyTree.canHover()) return;

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

// A row of pills where exactly one is chosen — how the index is grouped, and how it
// is sorted inside each group. The options come from the renderer, so a control can
// never offer a grouping nothing implements; the labels come with them already
// translated, so this knows no words either.
FamilyTree.renderSegments = function (el, options, current) {
  el.innerHTML = options
    .map(o => {
      const on = o.key === current;
      // radio rather than tab: these reconfigure one view, they do not switch
      // between panels, and a tab that reveals nothing is a lie to a screen reader.
      return (
        `<button class="seg${on ? ' active' : ''}" data-key="${o.key}" role="radio" ` +
        `aria-checked="${on}">${o.label.replace(/&/g, '&amp;').replace(/</g, '&lt;')}</button>`
      );
    })
    .join('');
};

FamilyTree.onSegmentPick = function (el, handler) {
  el.addEventListener('click', e => {
    const b = e.target.closest('.seg[data-key]');
    if (b) handler(b.dataset.key);
  });
};
