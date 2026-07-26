// Wires the pieces together once the person files have registered themselves.

(function (FT) {
  const $ = id => document.getElementById(id);

  FT.initTheme($('themeBtn'));

  FT.loadPeople(function (missing) {
    if (missing.length) {
      $('ped').innerHTML =
        '<p class="hint">Could not load ' +
        missing.length +
        ' of the person files (' +
        missing.slice(0, 5).join(', ') +
        (missing.length > 5 ? ', …' : '') +
        '). Check that each id in data/people.js has a matching file in data/people/.</p>';
      return;
    }

    const tree = FT.tree();
    const kin = FT.createKinship(tree);
    const view = FT.createRenderer(tree, kin);
    const search = FT.createSearch(tree);
    const { meta, people } = tree;

    // Every number the page states about itself comes from the census in the bundle,
    // so nothing here has to be kept in step by hand as people are added.
    const n = (count, one, many) => `${count} ${count === 1 ? one : many}`;
    const c = meta.census;
    // "Renée & Léon Bundervoet" rather than the surname twice. The names come from the
    // records, not from the markup, so a page cannot go on naming somebody the data no
    // longer calls the root.
    const rootIds = (meta.roots?.length ? meta.roots : [meta.root]).filter(id => people[id]);
    const surname = people[rootIds[0]].surname;
    const shared = surname && rootIds.every(id => people[id].surname === surname);
    const rootNames = shared
      ? `${rootIds.map(id => people[id].name.replace(surname, '').trim()).join(' & ')} ${surname}`
      : rootIds.map(id => people[id].name).join(' & ');

    $('subtitle').textContent =
      `${n(c.total, 'person', 'people')} · ${n(c.ancestors, 'direct ancestor', 'direct ancestors')} · ` +
      `${n(c.relatives, 'blood relative', 'blood relatives')} · ${c.others} married in`;
    $('linehint').textContent =
      `The surname lines that flow into ${rootNames}, each as deep as the records reach. ` +
      'Click any name to open it in the explorer.';
    $('homeBtn').textContent = `⌂ ${rootNames}`;
    // The side panel measures from the root, so it is the root that it names.
    const linkLabel = `Link to ${people[meta.root].name.replace(surname || '', '').trim() || people[meta.root].name}`;
    $('lineBtn').title = linkLabel;
    $('lineBtn').querySelector('.lbl').textContent = linkLabel;
    $('lineTitle').textContent = linkLabel;

    $('foot').textContent = meta.footer;
    $('legend').innerHTML = view.legend();
    $('cols').innerHTML = view.lineageColumns();
    $('branchgrid').innerHTML = view.indexCards();

    // ---- relation finder ----
    // Two pickers over everyone, sorted by name. A <select> is the right control
    // at this size; it is also the first thing that will need replacing when the
    // tree reaches thousands of people.
    (() => {
      const byName = Object.keys(people).sort((a, b) => people[a].name.localeCompare(people[b].name));
      const options = byName
        .map(id => {
          const p = people[id];
          const label = p.dates ? `${p.name} — ${p.dates}` : p.name;
          return `<option value="${id.replace(/"/g, '&quot;')}">${label
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')}</option>`;
        })
        .join('');
      const a = $('relA');
      const b = $('relB');
      a.innerHTML = options;
      b.innerHTML = options;
      a.value = meta.root;
      b.value = byName.find(id => id !== meta.root) || meta.root;
      const update = () => ($('relOut').innerHTML = view.relationPanel(a.value, b.value));
      a.addEventListener('change', update);
      b.addEventListener('change', update);
      update();
    })();

    FT.initTooltip($('tt'), id => (people[id] ? view.tooltip(id) : null));
    if (!FT.canHover()) {
      $('tip').textContent = 'Tap any name to open it — full details appear below';
    }
    const showView = FT.initTabs();

    // ---- explorer state ----
    let focus = meta.root;
    let history = [];

    // A row wider than the screen scrolls inside itself; this puts the card that
    // matters in the middle of it, so a phone opens on the person in focus rather
    // than on whichever sibling happens to be eldest.
    function centreOn(row, card) {
      if (!row || !card || row.scrollWidth <= row.clientWidth) return;
      const box = row.getBoundingClientRect();
      const it = card.getBoundingClientRect();
      row.scrollLeft += it.left + it.width / 2 - (box.left + box.width / 2);
    }

    function draw() {
      $('ped').innerHTML = view.pedigree(focus);
      $('detail').innerHTML = view.detail(focus);
      $('backBtn').disabled = history.length === 0;
      $('lineBody').innerHTML = view.descent(focus);

      // Only the row of brothers and sisters needs this. The row of children opens
      // at its left, which is the eldest, and the rows above hold two cards.
      const sibrow = $('ped').querySelector('.sibrow');
      centreOn(sibrow, sibrow && sibrow.querySelector('.fcell'));
    }

    function climbTo(id) {
      if (!kin.isResearchable(id) || id === focus) return;
      history.push(focus);
      focus = id;
      draw();
    }

    function openInExplorer(id) {
      if (!kin.isResearchable(id)) return;
      focus = id;
      history = [];
      showView('explore');
      draw();
    }

    $('ped').addEventListener('click', e => {
      const n = e.target.closest('.node[data-id]');
      if (n) climbTo(n.dataset.id);
    });
    // Every name in the detail card is a way into that person's own four rows.
    $('detail').addEventListener('click', e => {
      const n = e.target.closest('.ref[data-id]');
      if (n) climbTo(n.dataset.id);
    });
    $('detail').addEventListener('keydown', e => {
      if (e.key !== 'Enter' && e.key !== ' ') return;
      const n = e.target.closest('.ref[data-id]');
      if (!n) return;
      e.preventDefault();
      climbTo(n.dataset.id);
    });
    $('relOut').addEventListener('click', e => {
      const n = e.target.closest('.ucard[data-id]');
      if (n) openInExplorer(n.dataset.id);
    });
    $('cols').addEventListener('click', e => {
      const n = e.target.closest('.cnode[data-id]');
      if (n) openInExplorer(n.dataset.id);
    });
    $('branchgrid').addEventListener('click', e => {
      const n = e.target.closest('.p[data-id]');
      if (n) openInExplorer(n.dataset.id);
    });

    $('backBtn').onclick = () => {
      if (history.length) {
        focus = history.pop();
        draw();
      }
    };
    $('homeBtn').onclick = () => {
      history = [];
      focus = meta.root;
      draw();
    };

    // ---- search ----
    const q = $('q');
    let lastTab = 'explore';

    function runSearch() {
      const term = q.value;
      $('searchbox').classList.toggle('filled', term.length > 0);
      if (!term.trim()) {
        showView(lastTab);
        return;
      }
      $('results').innerHTML = view.searchResults(search.query(term), term);
      showView('search');
    }

    function clearSearch() {
      q.value = '';
      $('searchbox').classList.remove('filled');
      showView(lastTab);
    }

    q.addEventListener('input', runSearch);
    $('qClear').onclick = () => {
      clearSearch();
      q.focus();
    };

    q.addEventListener('keydown', e => {
      if (e.key === 'Escape') return clearSearch();
      if (e.key !== 'Enter') return;
      const first = $('results').querySelector('.hit[data-id]');
      if (first) {
        clearSearch();
        openInExplorer(first.dataset.id);
      }
    });

    $('results').addEventListener('click', e => {
      const n = e.target.closest('.hit[data-id]');
      if (!n) return;
      clearSearch();
      openInExplorer(n.dataset.id);
    });

    // Remember which tab to fall back to when the search is cleared.
    document.querySelectorAll('.tab').forEach(t =>
      t.addEventListener('click', () => {
        lastTab = t.dataset.view;
        if (q.value) clearSearch();
      })
    );

    // "/" focuses the search from anywhere except a text field.
    document.addEventListener('keydown', e => {
      if (e.key !== '/' || e.metaKey || e.ctrlKey || e.altKey) return;
      if (/^(INPUT|TEXTAREA|SELECT)$/.test(document.activeElement.tagName)) return;
      e.preventDefault();
      q.focus();
      q.select();
    });

    // ---- line of descent panel ----
    const panel = $('linepanel');
    const lineBtn = $('lineBtn');

    function setPanel(open) {
      panel.classList.toggle('collapsed', !open);
      panel.setAttribute('aria-hidden', String(!open));
      lineBtn.classList.toggle('open', open);
      lineBtn.setAttribute('aria-expanded', String(open));
    }

    lineBtn.onclick = () => setPanel(panel.classList.contains('collapsed'));
    $('lineClose').onclick = () => setPanel(false);

    $('lineBody').addEventListener('click', e => {
      const n = e.target.closest('.ucard[data-id]');
      if (!n) return;
      openInExplorer(n.dataset.id);
      // On a phone the panel covers the whole screen, so leaving it open would
      // hide the tree it just redrew. On a wide screen it sits beside the tree
      // and redraws for the new person, which is worth keeping in view.
      if (window.matchMedia('(max-width:720px)').matches) setPanel(false);
    });

    draw();
  });
})(window.FamilyTree);
