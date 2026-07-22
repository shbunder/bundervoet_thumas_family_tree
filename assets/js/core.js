// The FamilyTree namespace and the loader for the data files.
//
// Everything here is a plain script rather than an ES module, and the person files
// register themselves rather than being fetched. That is deliberate: it means the
// pages work both from a web server and when opened straight off disk, where
// browsers block fetch() and module scripts but still allow ordinary <script> tags.

window.FamilyTree = (function () {
  var FT = {
    people: {},
    roster_: [],
    meta_: null,
    branches_: {},
    lineages_: [],
    groups_: [],
  };

  // ---- called by the data files ----
  FT.person = function (p) {
    FT.people[p.id] = p;
  };
  FT.roster = function (ids) {
    FT.roster_ = ids;
  };
  FT.meta = function (m) {
    FT.meta_ = m;
  };
  FT.branches = function (b) {
    FT.branches_ = b;
  };
  FT.lineages = function (l) {
    FT.lineages_ = l;
  };
  FT.groups = function (g) {
    FT.groups_ = g;
  };

  // Where the data lives, worked out from this script's own URL so the pages keep
  // working if they are ever moved into a subfolder.
  var self = document.currentScript.src;
  var base = new URL('../../data/', self).href;

  // GitHub Pages serves these with a ten-minute cache, so an edit can take that
  // long to reach a phone that has already loaded the page. The page stamps every
  // reference with ?v=N; carry the same stamp onto the person files it injects,
  // so bumping it in the HTML refreshes the whole site at once.
  var version = (self.match(/[?&]v=([^&]*)/) || [])[1];
  var stamp = version ? '?v=' + version : '';

  // Loads every person named in the roster. Order does not matter — each file just
  // adds itself to FT.people — so they all go out at once.
  FT.loadPeople = function (done) {
    var ids = FT.roster_;
    var pending = ids.length;
    var missing = [];

    if (!pending) return done([]);

    ids.forEach(function (id) {
      var s = document.createElement('script');
      s.src = base + 'people/' + encodeURIComponent(id) + '.js' + stamp;
      s.onload = s.onerror = function (e) {
        if (e.type === 'error') missing.push(id);
        if (--pending === 0) done(missing);
      };
      document.head.appendChild(s);
    });
  };

  // The shape the rest of the app works with.
  FT.tree = function () {
    return {
      meta: FT.meta_,
      people: FT.people,
      branches: FT.branches_,
      lineages: FT.lineages_,
      groups: FT.groups_,
    };
  };

  return FT;
})();
