// Wires the pieces together once the person files have registered themselves.

(function (FT) {
  const $ = id => document.getElementById(id);

  const i18n = FT.createI18n(FT.strings_);
  const applyTheme = FT.initTheme($('themeBtn'), i18n);
  FT.initLanguage($('langBtn'), i18n);

  FT.loadPeople(function (missing) {
    if (missing.length) {
      FT.applyStatic(i18n, document);
      $('ped').textContent = i18n.t('loadError', {
        n: missing.length,
        ids: missing.slice(0, 5).join(', ') + (missing.length > 5 ? ', …' : ''),
      });
      return;
    }

    const tree = FT.tree();
    const kin = FT.createKinship(tree, i18n);
    const view = FT.createRenderer(tree, kin, i18n);
    const search = FT.createSearch(tree);
    const { meta, people } = tree;

    // "Renée & Léon Bundervoet" rather than the surname twice. The names come from the
    // records, not from the markup, so a page cannot go on naming somebody the data no
    // longer calls the root.
    //
    // `named`, not `roots`. A root is an entry point into the forest, and objective 3
    // adds one every time a disconnected Bundervoet family gets a documented head —
    // none of which makes this any less Renée and Léon's tree. Reading `roots` here put
    // a Gent patriarch in the page title; `named` is the short, deliberate list of who
    // the tree is of, and `roots` only stands in for it if the key is missing.
    const namedIds = (meta.named?.length ? meta.named : meta.roots || [meta.root]).filter(
      id => people[id]
    );
    const surname = people[namedIds[0]].surname;
    const shared = surname && namedIds.every(id => people[id].surname === surname);
    const treeNames = shared
      ? `${namedIds.map(id => people[id].name.replace(surname, '').trim()).join(' & ')} ${surname}`
      : namedIds.map(id => people[id].name).join(' & ');
    const rootShort =
      people[meta.root].name.replace(surname || '', '').trim() || people[meta.root].name;

    // ---- how the index is cut up ----
    // Remembered, because a reader who prefers the index by century wants it by
    // century on the next visit too; both are validated by the renderer, so a stale
    // or hand-edited value falls back rather than breaking the page.
    const remember = (key, value) => {
      try {
        window.localStorage.setItem(key, value);
      } catch (e) {
        /* private mode just forgets the choice */
      }
    };
    const recall = key => {
      try {
        return window.localStorage.getItem(key);
      } catch (e) {
        return null;
      }
    };
    let groupBy = recall('familytree.groupBy') || 'line';
    let sortBy = recall('familytree.sortBy') || 'generation';

    function paintIndex() {
      const opts = view.indexOptions();
      FT.renderSegments($('groupBy'), opts.group, groupBy);
      FT.renderSegments($('sortBy'), opts.sort, sortBy);
      $('branchgrid').innerHTML = view.indexCards(groupBy, sortBy);
    }

    FT.onSegmentPick($('groupBy'), key => {
      groupBy = key;
      remember('familytree.groupBy', key);
      paintIndex();
    });
    FT.onSegmentPick($('sortBy'), key => {
      sortBy = key;
      remember('familytree.sortBy', key);
      paintIndex();
    });

    // ---- relation finder ----
    // Two pickers over everyone, sorted by name. A <select> is the right control
    // at this size; it is also the first thing that will need replacing when the
    // tree reaches thousands of people. The options are names and dates, so they
    // are built once — it is only the sentence below them that is translated.
    const relA = $('relA');
    const relB = $('relB');
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
      relA.innerHTML = options;
      relB.innerHTML = options;
      relA.value = meta.root;
      relB.value = byName.find(id => id !== meta.root) || meta.root;
    })();
    const updateRelation = () =>
      ($('relOut').innerHTML = view.relationPanel(relA.value, relB.value));
    relA.addEventListener('change', updateRelation);
    relB.addEventListener('change', updateRelation);

    FT.initTooltip($('tt'), id => (people[id] ? view.tooltip(id) : null));
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

    // Everything the page says, said again. Language is not a page reload here — the
    // reader keeps their focus, their history and their place in the index — so every
    // piece of wording has to be settable rather than set once at load, and this is
    // the one list of them. Anything not called from here would silently stay in the
    // language the page opened in.
    function paint() {
      FT.applyStatic(i18n, document);
      applyTheme();

      // Every number the page states about itself comes from the census in the
      // bundle, so nothing here has to be kept in step by hand as people are added.
      const c = meta.census;
      document.title = i18n.t('treeOf', { names: treeNames });
      $('pagetitle').textContent = document.title;
      $('subtitle').textContent = [
        i18n.t('countPeople', { n: c.total }),
        i18n.t('countAncestors', { n: c.ancestors }),
        i18n.t('countRelatives', { n: c.relatives }),
        i18n.t('countMarriedIn', { n: c.others }),
      ].join(' · ');

      $('homeBtn').textContent = `⌂ ${treeNames}`;
      $('linehint').textContent = i18n.t('lineHint', { names: treeNames });
      $('tip').textContent = i18n.t(FT.canHover() ? 'hoverTip' : 'tapTip');

      // The side panel measures from the root, so it is the root that it names.
      const linkLabel = i18n.t('linkTo', { name: rootShort });
      $('lineBtn').title = linkLabel;
      $('lineBtn').querySelector('.lbl').textContent = linkLabel;
      $('lineTitle').textContent = linkLabel;

      $('foot').textContent = i18n.footer();
      $('legend').innerHTML = view.legend();
      $('cols').innerHTML = view.lineageColumns();
      paintIndex();
      updateRelation();
      if (q.value) runSearch();
      draw();
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

    i18n.onChange(paint);
    paint();
  });
})(window.FamilyTree);
