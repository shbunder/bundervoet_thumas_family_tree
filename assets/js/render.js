// Turns records into markup. Nothing here knows where the data came from.

(function () {

const esc = s =>
  String(s ?? '')
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');

const spouseText = sp => '❦ ' + (sp.detail ? `${sp.name} — ${sp.detail}` : sp.name);
// Someone can have married more than once; the list is chronological.
const spousesText = p => (p.spouses || []).map(spouseText).join('   ');

FamilyTree.createRenderer = function ({ people, lineages, groups }, kin, i18n) {
  const conf = id => kin.confidenceOf(id);
  // Every word this file prints comes through here. Nothing below writes English —
  // it writes a key, and site/labels.json decides what that reads as.
  const t = (key, params) => i18n.t(key, params);

  // ---------- shared pieces ----------

  // Birth order, which is the order a sibship is read in. `order` is the birth date
  // reduced to a sortable string by the build; anyone without one sorts last rather
  // than being given a position the records do not support.
  const byBirth = (a, b) =>
    (people[a].order || '9999').localeCompare(people[b].order || '9999') ||
    people[a].name.localeCompare(people[b].name);

  // What someone is *to the person in focus* — "father", "sister", "granddaughter".
  // Every card on the explorer is labelled this way, so the same layout reads
  // correctly from anybody's seat and not just from the root's.
  const relTo = (id, ref) => {
    if (!id || !ref || id === ref || !people[id] || !people[ref]) return '';
    const r = kin.bloodRelation(id, ref);
    return r && r.kind === 'blood' ? r.label : '';
  };

  // Whose children a group is. Named, because with more than one group an unlabelled
  // row of children is the half-sibling ambiguity itself: it shows four children and
  // says nothing about the two mothers they had.
  const withWhom = other =>
    other && people[other]
      ? t('withWhom', { name: esc(people[other].name) })
      : t('otherParentUnknown');

  function node(id, { role, arrow = '↑', focus = false, cls = '' } = {}) {
    if (!id) {
      return `<div class="node unk"><div class="nm">${esc(t('unknownCard'))}</div>` +
        `<div class="dt">${esc(t('toResearch'))}</div></div>`;
    }
    const p = people[id];
    const c = conf(id);
    // Every other card on the row says what it is to the person in focus, so the
    // focus card cannot also say what it is to the root without the two readings
    // being mistaken for each other. What they are to the root is stated once,
    // with room to name the root, in the detail card below.
    const label = focus ? t('inFocus') : role || kin.relationship(id) || p.occupation || '';
    const climb = !focus && c !== 'unk'
      ? `<span class="climb">${esc(arrow ? t('climb', { arrow }) : t('openCard'))}</span>`
      : '';
    return (
      `<div class="node ${focus ? 'focus ' : ''}${cls ? cls + ' ' : ''}${c}" data-id="${esc(id)}">` +
      climb +
      (label ? `<div class="rl">${esc(label)}</div>` : '') +
      `<div class="nm">${esc(p.name)}</div>` +
      (p.dates ? `<div class="dt">${esc(p.dates)}</div>` : '') +
      '</div>'
    );
  }

  // A spouse who is a record of their own is rendered as a real node, so you can
  // open them and go on into their family. One who is only a name stays flat.
  const spouseNode = (sp, of) =>
    sp.id && people[sp.id]
      ? node(sp.id, { role: kin.spouseLabel(sp, of), arrow: '' })
      : `<div class="node fam spouse"><div class="rl">${esc(kin.spouseLabel(sp))}</div>` +
        `<div class="nm">${esc(sp.name)}</div>` +
        (sp.detail ? `<div class="dt">${esc(sp.detail)}</div>` : '') +
        '</div>';

  // A parent's own parents, shown as a couple with a drop line beneath them.
  // The caption only shows on narrow screens: there the two couples sit one
  // above the other, where the drop line would wrongly read as descent, so it
  // is hidden and this says whose parents each couple is instead.
  function grandparentCouple(parentId, focus) {
    const p = parentId && people[parentId];
    if (!p || (!p.father && !p.mother)) return '';
    return (
      `<div class="gplab">${esc(t('parentsOf', { name: p.name }))}</div>` +
      `<div class="couple">${node(p.father, { role: relTo(p.father, focus) })}<span class="xmark">×</span>` +
      `${node(p.mother, { role: relTo(p.mother, focus) })}</div>` +
      '<div class="vline"></div>'
    );
  }

  // A name that opens that person. Everywhere one person is mentioned inside
  // another's card, it is one of these — the tree is a graph, so reading it should
  // never be a one-way trip.
  const refLink = id =>
    `<a class="ref ${conf(id)}" data-id="${esc(id)}" role="button" tabindex="0">${esc(people[id].name)}</a>` +
    (people[id].dates ? ` <span class="d">${esc(people[id].dates)}</span>` : '');

  const parentLine = (label, id) =>
    id && people[id]
      ? `<div class="kv"><b>${label}:</b> ${esc(people[id].name)}` +
        (people[id].dates ? ` (${esc(people[id].dates)})` : '') +
        '</div>'
      : '';

  // "Renée's great-grandmother", not "Great-grandmother" — a relation is a fact about
  // a pair, so the other half of the pair has to be in it. Everywhere else on the page
  // labels are read against the person in focus; this one is read against the root,
  // and the only way to tell them apart is to say so.
  const rootName = people[kin.ROOT] ? people[kin.ROOT].name : '';
  function subtitleFor(id) {
    const p = people[id];
    const rel = kin.relationship(id);
    return [
      rel && t('ofRoot', { root: rootName, rel: rel.toLowerCase() }),
      p.dates,
      p.occupation,
      p.nickname && `“${p.nickname}”`,
    ]
      .filter(Boolean)
      .join(' · ');
  }

  // ---------- hover card ----------

  function tooltip(id) {
    const p = people[id];
    const c = conf(id);
    const sub = subtitleFor(id);
    const groups = kin.childGroupsOf(id);
    const kidLines = groups
      .map(g => {
        const label = groups.length > 1
          ? `${esc(t('lblChildren'))} ${withWhom(g.other)}`
          : esc(t('lblChildren'));
        return `<div class="kv"><b>${label}:</b> ` +
          `${esc(g.children.map(k => people[k].name).join(', '))}</div>`;
      })
      .join('');
    return (
      `<span class="conf conf-${c}">${esc(i18n.conf(c))}</span>` +
      `<h5>${esc(p.name)}</h5>` +
      (sub ? `<div class="r">${esc(sub)}</div>` : '') +
      (p.spouses?.length
        ? `<div class="kv"><b>${esc(t('lblSpouse'))}:</b> ${esc(spousesText(p))}</div>`
        : '') +
      parentLine(esc(t('lblFather')), p.father) +
      parentLine(esc(t('lblMother')), p.mother) +
      kidLines +
      (p.note ? `<div class="nt">${esc(p.note)}</div>` : '') +
      `<div class="sr"><b>${esc(t('lblSource'))}:</b> ${esc(kin.sourceFor(id))}</div>`
    );
  }

  // ---------- explorer ----------

  // Four rows around whoever is in focus: grandparents, parents, their own
  // generation — themselves, whoever they married, and their brothers and sisters —
  // and their children. Every card is labelled by what it is *to them*, and clicking
  // one makes it the focus, so the same four rows redraw around anybody in the tree.
  function pedigree(focus) {
    const p = people[focus];
    const fatherGP = grandparentCouple(p.father, focus);
    const motherGP = grandparentCouple(p.mother, focus);
    let html = '';

    // The two rows are tagged so a narrow screen can stack the four grandparents
    // into two couples while keeping the parents side by side.
    if (fatherGP || motherGP) {
      html += `<div class="pgrid gp"><div class="pcol">${fatherGP}</div><div class="pcol"></div><div class="pcol">${motherGP}</div></div>`;
    }
    if (p.father || p.mother) {
      html +=
        `<div class="gplab">${esc(t('parentsOf', { name: p.name }))}</div>` +
        `<div class="pgrid parents"><div class="pcol">${node(p.father, { role: relTo(p.father, focus) })}</div>` +
        '<div class="pcol xcol"><span class="xmark">×</span></div>' +
        `<div class="pcol">${node(p.mother, { role: relTo(p.mother, focus) })}</div></div>` +
        '<div class="vline tall"></div>';
    }

    // The whole sibship on one line, in birth order, with the person in focus in
    // their own place in it rather than pulled out of it — the drop line above
    // belongs to all of them equally. Their spouses travel with them.
    const siblings = kin.siblingsOf(focus);
    const sibship = [focus, ...siblings].sort(byBirth);
    const married = (p.spouses || [])
      .map(sp => `<span class="xmark">×</span>${spouseNode(sp, focus)}`)
      .join('');
    const row = sibship
      .map(id =>
        id === focus
          ? `<div class="fcell">${node(focus, { focus: true })}${married}</div>`
          : node(id, { role: relTo(id, focus), arrow: '', cls: 'sib' })
      )
      .join('');

    if (siblings.length) {
      html += `<div class="rowlab">${esc(t('siblingRow'))}</div>`;
    }
    // The inner wrapper is what lets a row centre when it fits and scroll when it
    // does not: `margin:auto` gives back negative free space as zero, where
    // `justify-content:center` would put the first card out of reach off-screen.
    html += `<div class="srow sibrow"><div class="rowin">${row}</div></div>`;

    // One row per marriage, not one row for the lot. Where someone married twice the
    // rows are the two sibships, captioned by the other parent — which is the whole
    // of what "half-brother" means, shown rather than left to be worked out by
    // clicking into a child and reading the label there.
    const groups = kin.childGroupsOf(focus);
    if (groups.length) {
      html += `<div class="vline tall"></div><div class="childlab">${esc(t('childrenRow'))}</div>`;
      html += groups
        .map(g => {
          const row = g.children
            .slice()
            .sort(byBirth)
            .map(k => node(k, { role: relTo(k, focus), arrow: '↓' }))
            .join('');
          const cap = groups.length > 1 ? `<div class="bywhom">${withWhom(g.other)}</div>` : '';
          return cap + `<div class="srow crow"><div class="rowin">${row}</div></div>`;
        })
        .join('');
    }
    return html;
  }

  // Everything known about the person in focus, under the four rows. Every name in
  // it is a way into that person's own four rows, so the detail is a second way to
  // walk the tree and not just a place to read about a stop on it.
  function detail(focus) {
    const p = people[focus];
    const c = conf(focus);
    const rows = [];
    const push = (label, value) => value && rows.push(`<div class="kv"><b>${label}:</b> ${value}</div>`);
    const list = ids => ids.map(id => refLink(id)).join('<span class="sep">·</span>');

    push(esc(t('lblBorn')), esc(p.born));
    push(esc(t('lblDied')), esc(p.died));
    push(esc(t('lblOccupation')), esc(p.occupation));
    if (p.spouses?.length) {
      push(
        esc(t('lblMarried')),
        p.spouses
          .map(sp => (sp.id && people[sp.id] ? refLink(sp.id) : esc(sp.name)) + (sp.detail ? ` <span class="d">— ${esc(sp.detail)}</span>` : ''))
          .join('<span class="sep">·</span>')
      );
    }
    push(esc(t('lblFather')), p.father && people[p.father] ? refLink(p.father) : '');
    push(esc(t('lblMother')), p.mother && people[p.mother] ? refLink(p.mother) : '');

    const siblings = kin.siblingsOf(focus).slice().sort(byBirth);
    if (siblings.length) {
      push(esc(t(siblings.length === 1 ? 'lblSibling' : 'lblSiblings')), list(siblings));
    }
    // Same reason as the rows above: with two marriages, one "Children:" line reads as
    // one family. The label carries the other parent so it cannot.
    const groups = kin.childGroupsOf(focus);
    for (const g of groups) {
      const kids = g.children.slice().sort(byBirth);
      const word = esc(t(kids.length === 1 ? 'lblChild' : 'lblChildren'));
      push(groups.length > 1 ? `${word} ${withWhom(g.other)}` : word, list(kids));
    }

    return (
      `<h3>${esc(p.name)}</h3><div class="sub">${esc(subtitleFor(focus))}</div>` +
      `<div class="conf conf-${c}">${esc(i18n.conf(c))}</div>` +
      rows.join('') +
      (p.note ? `<div class="disc">${esc(p.note)}</div>` : '') +
      `<div class="src"><b>${esc(t('lblSource'))}:</b> ${esc(kin.sourceFor(focus))}</div>`
    );
  }

  // ---------- how two people connect ----------
  //
  // Drawn as an arch: up from each of them to the ancestor they share, across the
  // top, and down again. The shape is the argument — it shows *where* two people
  // meet instead of asserting that they do, and the height of each side is the
  // number of generations that side had to climb.
  //
  // When one of the two is the shared ancestor there is no fork to draw, so the arch
  // straightens into the single line that a direct descent actually is. Same code,
  // because it is the same fact with one leg of length zero.

  const BRIDGE =
    '<svg class="ubridge" viewBox="0 0 100 34" preserveAspectRatio="none" aria-hidden="true">' +
    '<path d="M50 0 V12 M25 12 H75 M25 12 V34 M75 12 V34" vector-effect="non-scaling-stroke"/></svg>';

  // A function, not a constant: the language can change without the renderer being
  // rebuilt, and a string captured at construction would stay in the old one.
  const MARRIED = () => `<div class="uconn marr"><span>${esc(t('marriedConn'))}</span></div>`;

  function ucard(id, label, cls = '') {
    const p = people[id];
    return (
      `<div class="ucard ${conf(id)}${cls}" data-id="${esc(id)}">` +
      (label ? `<div class="urel">${esc(label)}</div>` : '') +
      `<div class="uname">${esc(p.name)}</div>` +
      (p.dates ? `<div class="udt">${esc(p.dates)}</div>` : '') +
      '</div>'
    );
  }

  // One side of the arch, read top-down: the steps below the shared ancestor, each
  // labelled by what it is to the person at the foot, ending on that person.
  function arm(path, marriedIn) {
    const foot = path[path.length - 1];
    const steps = path
      .map((id, i) => {
        const last = i === path.length - 1;
        return (
          '<div class="uconn"></div>' +
          ucard(id, last ? '' : relTo(id, foot), last && !marriedIn ? ' here' : '')
        );
      })
      .join('');
    return steps + (marriedIn ? MARRIED() + ucard(marriedIn, '', ' here') : '');
  }

  function linkGraph(a, b) {
    const d = kin.linkDiagram(a, b);
    if (!d || d.kind === 'self') return '';
    if (d.kind === 'spouse') {
      return `<div class="ulink pair">${ucard(a, '', ' here')}${MARRIED()}${ucard(b, '', ' here')}</div>`;
    }

    // Each arm without the ancestor at its top — that card is drawn once, at the
    // apex, which is the whole point of the shape.
    const left = d.left.slice(0, -1).reverse();
    const right = d.right.slice(0, -1).reverse();
    const marriedOn = side => (d.married && d.married.side === side ? d.married.id : null);

    if (!left.length || !right.length) {
      const emptyLeft = !left.length;
      const atApex = marriedOn(emptyLeft ? 'left' : 'right');
      return (
        '<div class="ulink straight">' +
        (atApex ? ucard(atApex, '', ' here') + MARRIED() : '') +
        ucard(d.via, '', atApex ? '' : ' here') +
        arm(emptyLeft ? right : left, marriedOn(emptyLeft ? 'right' : 'left')) +
        '</div>'
      );
    }

    return (
      '<div class="ulink">' +
      `<div class="uapex">${ucard(d.via, t('meetHere'))}</div>` +
      BRIDGE +
      `<div class="ucols"><div class="uside">${arm(left, marriedOn('left'))}</div>` +
      `<div class="uside">${arm(right, marriedOn('right'))}</div></div>` +
      '</div>'
    );
  }

  // ---------- lineages ----------

  // Resolve a lineage's people: an explicit chain if given, otherwise walk
  // father-links up from `head` so the chain always tracks the data.
  function lineageChain(line) {
    if (line.chain) return line.chain;
    const out = [];
    const seen = new Set();
    let id = line.head;
    while (id && people[id] && !seen.has(id)) { seen.add(id); out.push(id); id = people[id].father; }
    return out.reverse();
  }

  function lineageColumns() {
    return lineages
      .map(line => {
        const ids = lineageChain(line);
        const known = ids.filter(id => kin.isResearchable(id)).length;
        const chain = ids
          .map((id, i) => {
            const p = people[id];
            return (
              `<div class="cnode ${conf(id)}" data-id="${esc(id)}">` +
              `<div class="nm">${esc(p.name)}</div>` +
              (p.dates ? `<div class="dt">${esc(p.dates)}</div>` : '') +
              '</div>' +
              (i < ids.length - 1 ? '<div class="cconn"></div>' : '')
            );
          })
          .join('');
        return (
          `<div class="col"><h3>${esc(line.key)}</h3>` +
          `<div class="cap">${esc(line.caption)}</div>` +
          `<div class="chain">${chain}</div>` +
          `<div class="depthlab">${esc(t('generationsKnown', { n: known }))}</div>` +
          (line.origin
            ? `<div class="origin"><span class="ol">${esc(t('nameOrigin'))}</span> ${esc(line.origin)}</div>`
            : '') +
          '</div>'
        );
      })
      .join('');
  }

  // ---------- search results ----------

  // Wraps the matched stretches of a string in <mark>, escaping around them.
  function mark(raw, ranges) {
    if (!ranges || !ranges.length) return esc(raw);
    const merged = [];
    for (const [s, e] of [...ranges].sort((a, b) => a[0] - b[0])) {
      const last = merged[merged.length - 1];
      if (last && s <= last[1]) last[1] = Math.max(last[1], e);
      else merged.push([s, e]);
    }
    let out = '';
    let at = 0;
    for (const [s, e] of merged) {
      out += esc(raw.slice(at, s)) + '<mark>' + esc(raw.slice(s, e)) + '</mark>';
      at = e;
    }
    return out + esc(raw.slice(at));
  }

  // Long notes get windowed around the first match rather than shown whole.
  function excerpt(raw, ranges, limit = 150) {
    if (raw.length <= limit || !ranges || !ranges.length) return mark(raw, ranges);
    const first = [...ranges].sort((a, b) => a[0] - b[0])[0];
    let from = Math.max(0, first[0] - 50);
    let to = Math.min(raw.length, from + limit);
    if (from > 0) from = raw.lastIndexOf(' ', from) + 1 || from;
    const shifted = ranges
      .filter(r => r[0] >= from && r[1] <= to)
      .map(r => [r[0] - from, r[1] - from]);
    return (from > 0 ? '… ' : '') + mark(raw.slice(from, to), shifted) + (to < raw.length ? ' …' : '');
  }

  // Which field a hit was found in. The search index carries the field's key, not a
  // word for it — the word is wording, and belongs with the rest of it.
  const FIELD_LABEL = {
    name: 'lblName', born: 'lblBorn', died: 'lblDied', dates: 'lblDates',
    spouse: 'lblSpouse', occupation: 'lblOccupation', nickname: 'lblNickname',
    branch: 'lblBranch', note: 'lblNote', source: 'lblSource',
  };

  function searchResults(results, term) {
    if (!term.trim()) {
      return `<p class="hint">${esc(t('searchEmpty'))}</p>`;
    }
    if (!results.length) {
      return `<p class="hint">${esc(t('noMatches', { term: term.trim() }))}</p>`;
    }
    const rows = results
      .map(r => {
        const p = people[r.id];
        const meta = [kin.relationship(r.id), p.dates].filter(Boolean).join(' · ');
        const ctx = r.context
          ? `<div class="hc"><span class="hk">${esc(t(FIELD_LABEL[r.context.key] || r.context.key))}</span>` +
            `${excerpt(r.context.raw, r.ranges[r.context.key])}</div>`
          : '';
        return (
          `<div class="hit ${conf(r.id)}" data-id="${esc(r.id)}">` +
          `<div class="hn">${mark(p.name, r.ranges.name)}</div>` +
          (meta ? `<div class="hm">${esc(meta)}</div>` : '') +
          ctx +
          '</div>'
        );
      })
      .join('');
    return (
      `<p class="rescount">${esc(t('resultCount', { n: results.length, total: Object.keys(people).length }))}</p>` +
      `<div class="results">${rows}</div>`
    );
  }

  // ---------- the side panel: this person's link to the root ----------

  // The same arch, with one end pinned to the root. For a direct ancestor it is the
  // straight line of descent it always was; for an aunt or a cousin it is the fork
  // that the old single thread had to apologise for in prose.
  function descent(id) {
    if (id === kin.ROOT) {
      return `<p class="lnote">${esc(t('rootNote', { name: people[id].name }))}</p>`;
    }
    return `<div class="lhead">${relationText(id, kin.ROOT)}</div>` + linkGraph(id, kin.ROOT);
  }

  const legend = () =>
    i18n.confCodes
      .map(key => `<span><i class="swatch sw-${key}"></i>${esc(i18n.conf(key))}</span>`)
      .join('');

  // ---------- index ----------

  // Everyone, cut into groups by whichever question the reader asked and sorted
  // inside each group by whichever order they asked for. Both are *derived* — from
  // the person's own `line`, their surname, their birth date, their position in the
  // links — so someone added to data/ appears under the right heading in all four
  // groupings without a single list being edited anywhere.
  //
  // Which is the whole reason the controls can exist at all: a hand-kept index can
  // be regrouped only by rewriting it.

  const INDEX_GROUPINGS = ['line', 'letter', 'century', 'relation'];
  const INDEX_SORTS = ['generation', 'name', 'birth'];
  const GROUP_LABEL = {
    line: 'groupLine', letter: 'groupLetter', century: 'groupCentury', relation: 'groupRelation',
  };
  const SORT_LABEL = { generation: 'sortGeneration', name: 'sortName', birth: 'sortBirth' };

  // What the two controls above the index offer. Built here, beside the code that
  // honours them, so a grouping cannot be offered that nothing implements.
  const indexOptions = () => ({
    group: INDEX_GROUPINGS.map(key => ({ key, label: t(GROUP_LABEL[key]) })),
    sort: INDEX_SORTS.map(key => ({ key, label: t(SORT_LABEL[key]) })),
  });

  // `order` is the birth date reduced to a sortable string by the build, so its
  // first four characters are the year whatever precision the rest of it has.
  const birthYear = id => {
    const o = people[id].order;
    const y = o ? Number(String(o).slice(0, 4)) : NaN;
    return Number.isFinite(y) ? y : null;
  };

  // 1801–1900 is the 19th century, and 1900 is still in it. English wants the
  // ordinal and Dutch the bare number, so both go to the label and it takes one.
  const ordSuffix = n =>
    n % 100 >= 11 && n % 100 <= 13 ? 'th' : ['th', 'st', 'nd', 'rd'][n % 10] || 'th';

  // Each person names their own line; site/labels.json only says what the lines are
  // called and in what order. Nobody is listed twice, and nobody can be left out of
  // a list, because there is no list.
  const lineTitles = {};
  const orderOfLine = {};
  groups.forEach((g, i) => {
    lineTitles[g.key] = g.title;
    orderOfLine[g.key] = i;
  });
  // Resolved per call, not once: these headings are translated too, and the language
  // can change without the renderer being rebuilt.
  const titleOfLine = key => (key in lineTitles ? i18n.pick(lineTitles[key]) : null);

  const CATEGORY = {
    ancestor: { title: 'catAncestors', blurb: 'catAncestorsBlurb', rank: 0 },
    relative: { title: 'catRelatives', blurb: 'catRelativesBlurb', rank: 1 },
    other: { title: 'catOthers', blurb: 'catOthersBlurb', rank: 2 },
  };

  // Which card a person lands on. `rank` orders the cards themselves; within one
  // grouping every rank is the same type, so comparing them is well defined.
  function grouper(mode) {
    if (mode === 'letter') {
      return id => {
        const p = people[id];
        // The folded family key, not the name as written: it has already had the
        // particle spacing and the accents taken out, so "De Keyser", "Dekeyser"
        // and "'t Jonck" land where a reader would look for them.
        const ch = (p.family || p.surname || '').replace(/[^a-z]/gi, '').charAt(0).toUpperCase();
        return ch
          ? { key: ch, title: ch, rank: ch }
          : { key: '~none', title: t('letterUnknown'), rank: '￿' };
      };
    }
    if (mode === 'century') {
      return id => {
        const y = birthYear(id);
        if (!y) return { key: '~none', title: t('centuryUnknown'), rank: Infinity };
        const c = Math.floor((y - 1) / 100) + 1;
        return {
          key: String(c),
          title: t('century', { n: c, ord: c + ordSuffix(c) }),
          // Stated, because "19th century" meaning 1801–1900 is a convention half
          // the readers of a family tree do not hold.
          blurb: `${(c - 1) * 100 + 1}–${c * 100}`,
          rank: c,
        };
      };
    }
    if (mode === 'relation') {
      return id => {
        const c = kin.categoryOf(id);
        const cat = CATEGORY[c] || CATEGORY.other;
        return {
          key: c,
          title: t(cat.title),
          blurb: t(cat.blurb, { root: rootName }),
          rank: cat.rank,
        };
      };
    }
    // The curated headings, in the order site/labels.json gives them. Anyone it
    // does not mention falls back to their branch, which is why nobody goes missing.
    return id => {
      const p = people[id];
      const title = (p.line && titleOfLine(p.line)) || p.branch || t('unplaced');
      return {
        key: title,
        title,
        rank: p.line && p.line in orderOfLine ? orderOfLine[p.line] : Infinity,
      };
    };
  }

  // Within a card. "Generation" reads down the descent, closest to the root first —
  // all three are derived, but only that one tells a story, so it stays the default.
  function sorter(mode) {
    if (mode === 'name') {
      return (a, b) =>
        (people[a].family || '￿').localeCompare(people[b].family || '￿') ||
        people[a].name.localeCompare(people[b].name);
    }
    if (mode === 'birth') return byBirth;
    return (a, b) => {
      const da = a in kin.distance ? kin.distance[a] : Infinity;
      const db = b in kin.distance ? kin.distance[b] : Infinity;
      return da - db || people[a].name.localeCompare(people[b].name);
    };
  }

  const personRow = id => {
    const p = people[id];
    const rel = kin.relationship(id);
    const extra = [rel, p.occupation, p.nickname && `“${p.nickname}”`].filter(Boolean).join(' · ');
    return (
      `<div class="p" data-id="${esc(id)}"><b>${esc(p.name)}</b>` +
      (p.dates ? ` <span class="d">— ${esc(p.dates)}</span>` : '') +
      (extra ? ` <span class="d">· ${esc(extra)}</span>` : '') +
      '</div>'
    );
  };

  function indexCards(groupBy, sortBy) {
    const key = grouper(INDEX_GROUPINGS.indexOf(groupBy) >= 0 ? groupBy : INDEX_GROUPINGS[0]);
    const cmp = sorter(INDEX_SORTS.indexOf(sortBy) >= 0 ? sortBy : INDEX_SORTS[0]);

    const buckets = new Map();
    for (const id of Object.keys(people)) {
      const g = key(id);
      if (!buckets.has(g.key)) buckets.set(g.key, { title: g.title, blurb: g.blurb, rank: g.rank, ids: [] });
      buckets.get(g.key).ids.push(id);
    }

    const cards = [...buckets.values()]
      .sort((a, b) =>
        (a.rank < b.rank ? -1 : a.rank > b.rank ? 1 : 0) || a.title.localeCompare(b.title))
      .map(g =>
        `<div class="bcard"><h4>${esc(g.title)}<span class="n">${g.ids.length}</span></h4>` +
        (g.blurb ? `<div class="bblurb">${esc(g.blurb)}</div>` : '') +
        g.ids.sort(cmp).map(personRow).join('') +
        '</div>')
      .join('');

    return `<div class="branchgrid">${cards}</div>`;
  }

  // Objective (c): name the relation between any two people in the index.
  // These sentences carry their own markup — the <em> around the relation, the <b>
  // around each name — so what goes into them is escaped here, before it does.
  function relationText(a, b) {
    if (!a || !b || !people[a] || !people[b]) {
      return `<span class="muted">${esc(t('pickTwo'))}</span>`;
    }
    const A = `<b>${esc(people[a].name)}</b>`;
    const B = `<b>${esc(people[b].name)}</b>`;
    const r = kin.relationBetween(a, b);
    if (!r) return t('noConnection', { a: A, b: B });
    if (r.kind === 'self') return t('samePersonLine', { a: A });

    const line = t('isRelOf', { a: A, b: B, rel: esc(r.label) });
    // An in-law is two facts, not one — a blood relation and a marriage — and saying
    // it as one produces "X is Y's aunt of Y's husband". Two clauses, one per step.
    if (r.kind === 'marriage' && r.through) {
      const through = `<b>${esc(people[r.through].name)}</b>`;
      return t(r.married === 'b' ? 'inLawB' : 'inLawA', { a: A, b: B, through, rel: esc(r.label) });
    }
    if (r.kind !== 'blood' || !r.via) return line;
    // When one of them is the common ancestor, saying so again explains nothing —
    // the relation already is the line between them.
    if (r.da === 0 || r.db === 0) {
      const steps = Math.max(r.da, r.db);
      return line + `<div class="via">${esc(t('directLine', { n: steps }))}</div>`;
    }
    return (
      line +
      '<div class="via">' +
      t('commonAncestorLine', {
        via: `<b>${esc(people[r.via].name)}</b>`,
        ga: esc(t('genUp', { n: r.da })),
        gb: esc(t('genUp', { n: r.db })),
        a: esc(people[a].name),
        b: esc(people[b].name),
      }) +
      '</div>'
    );
  }

  // What the index's relation finder shows: the sentence, and then the route that
  // sentence came from. Neither is worth much alone — a label with no visible join
  // is a claim, and a drawing with no label makes the reader name the shape.
  const relationPanel = (a, b) => relationText(a, b) + linkGraph(a, b);

  return {
    tooltip, pedigree, detail, lineageColumns, indexCards, indexOptions, relationPanel,
    legend, searchResults, descent,
  };
};

})();
