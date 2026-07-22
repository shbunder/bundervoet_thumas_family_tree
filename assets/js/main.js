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

    const ancestors = kin.directAncestorCount();
    $('subtitle').textContent =
      `${ancestors} direct ancestor${ancestors === 1 ? '' : 's'} recorded`;

    $('foot').textContent = meta.footer;
    $('legend').innerHTML = view.legend();
    $('cols').innerHTML = view.lineageColumns();
    $('branchgrid').innerHTML = view.indexCards();

    FT.initTooltip($('tt'), id => (people[id] ? view.tooltip(id) : null));
    if (!FT.canHover()) {
      $('tip').textContent = 'Tap any name to open it — full details appear below';
    }
    const showView = FT.initTabs();

    // ---- explorer state ----
    let focus = meta.root;
    let history = [];

    function draw() {
      $('ped').innerHTML = view.pedigree(focus);
      $('detail').innerHTML = view.detail(focus);
      $('backBtn').disabled = history.length === 0;
      $('lineBody').innerHTML = view.descent(focus);

      // On a narrow screen the pedigree is wider than the viewport and scrolls
      // inside itself. Line the scroll up on the person in focus, so a phone
      // opens on them rather than on the far-left grandparent.
      const ped = $('ped');
      const card = ped.querySelector('.node.focus');
      if (card && ped.scrollWidth > ped.clientWidth) {
        const box = ped.getBoundingClientRect();
        const it = card.getBoundingClientRect();
        ped.scrollLeft += it.left + it.width / 2 - (box.left + box.width / 2);
      }
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
      const n = e.target.closest('.lstep[data-id]');
      if (n) openInExplorer(n.dataset.id);
    });

    draw();
  });
})(window.FamilyTree);
