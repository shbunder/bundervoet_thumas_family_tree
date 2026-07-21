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
    const { meta, people } = tree;

    $('foot').textContent = meta.footer;
    $('legend').innerHTML = view.legend();
    $('cols').innerHTML = view.lineageColumns();
    $('branchgrid').innerHTML = view.indexCards();

    FT.initTooltip($('tt'), id => (people[id] ? view.tooltip(id) : null));
    const showView = FT.initTabs();

    // ---- explorer state ----
    let focus = meta.root;
    let history = [];

    function draw() {
      $('ped').innerHTML = view.pedigree(focus);
      $('detail').innerHTML = view.detail(focus);
      $('backBtn').disabled = history.length === 0;
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

    draw();
  });
})(window.FamilyTree);
