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

FamilyTree.createRenderer = function ({ meta, people, lineages, groups }, kin) {
  const conf = id => kin.confidenceOf(id);

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

  const spouseWord = id => ({ f: 'wife', m: 'husband' })[kin.genderOf(id)] || 'spouse';

  function node(id, { role, arrow = '↑', focus = false, cls = '' } = {}) {
    if (!id) return '<div class="node unk"><div class="nm">Unknown</div><div class="dt">to research</div></div>';
    const p = people[id];
    const c = conf(id);
    // Every other card on the row says what it is to the person in focus, so the
    // focus card cannot also say what it is to the root without the two readings
    // being mistaken for each other. What they are to the root is stated once,
    // with room to name the root, in the detail card below.
    const label = focus ? 'in focus' : role || kin.relationship(id) || p.occupation || '';
    const climb = !focus && c !== 'unk' ? `<span class="climb">${arrow ? `climb ${arrow}` : 'open'}</span>` : '';
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
  const spouseNode = sp =>
    sp.id && people[sp.id]
      ? node(sp.id, { role: spouseWord(sp.id), arrow: '' })
      : '<div class="node fam spouse"><div class="rl">spouse</div>' +
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
      `<div class="gplab">${esc(p.name)}’s parents</div>` +
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
      rel && `${rootName}’s ${rel.toLowerCase()}`,
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
    const kids = kin.childrenOf(id).map(k => people[k].name);
    return (
      `<span class="conf conf-${c}">${esc(meta.confidenceLabels[c])}</span>` +
      `<h5>${esc(p.name)}</h5>` +
      (sub ? `<div class="r">${esc(sub)}</div>` : '') +
      (p.spouses?.length ? `<div class="kv"><b>Spouse:</b> ${esc(spousesText(p))}</div>` : '') +
      parentLine('Father', p.father) +
      parentLine('Mother', p.mother) +
      (kids.length ? `<div class="kv"><b>Children:</b> ${esc(kids.join(', '))}</div>` : '') +
      (p.note ? `<div class="nt">${esc(p.note)}</div>` : '') +
      `<div class="sr"><b>Source:</b> ${esc(kin.sourceFor(id))}</div>`
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
        `<div class="gplab">${esc(p.name)}’s parents</div>` +
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
    const married = (p.spouses || []).map(sp => `<span class="xmark">×</span>${spouseNode(sp)}`).join('');
    const row = sibship
      .map(id =>
        id === focus
          ? `<div class="fcell">${node(focus, { focus: true })}${married}</div>`
          : node(id, { role: relTo(id, focus), arrow: '', cls: 'sib' })
      )
      .join('');

    if (siblings.length) {
      html += '<div class="rowlab">brothers &amp; sisters, in birth order · click to open one</div>';
    }
    // The inner wrapper is what lets a row centre when it fits and scroll when it
    // does not: `margin:auto` gives back negative free space as zero, where
    // `justify-content:center` would put the first card out of reach off-screen.
    html += `<div class="srow sibrow"><div class="rowin">${row}</div></div>`;

    const children = kin.childrenOf(focus).slice().sort(byBirth);
    if (children.length) {
      html +=
        '<div class="vline tall"></div>' +
        '<div class="childlab">children · click to climb down ↓</div>' +
        '<div class="srow crow"><div class="rowin">' +
        children.map(k => node(k, { role: relTo(k, focus), arrow: '↓' })).join('') +
        '</div></div>';
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

    push('Born', esc(p.born));
    push('Died', esc(p.died));
    push('Occupation', esc(p.occupation));
    if (p.spouses?.length) {
      push(
        'Married',
        p.spouses
          .map(sp => (sp.id && people[sp.id] ? refLink(sp.id) : esc(sp.name)) + (sp.detail ? ` <span class="d">— ${esc(sp.detail)}</span>` : ''))
          .join('<span class="sep">·</span>')
      );
    }
    push('Father', p.father && people[p.father] ? refLink(p.father) : '');
    push('Mother', p.mother && people[p.mother] ? refLink(p.mother) : '');

    const siblings = kin.siblingsOf(focus).slice().sort(byBirth);
    const children = kin.childrenOf(focus).slice().sort(byBirth);
    if (siblings.length) push(siblings.length === 1 ? 'Sibling' : 'Siblings', list(siblings));
    if (children.length) push(children.length === 1 ? 'Child' : 'Children', list(children));

    return (
      `<h3>${esc(p.name)}</h3><div class="sub">${esc(subtitleFor(focus))}</div>` +
      `<div class="conf conf-${c}">${esc(meta.confidenceLabels[c])}</div>` +
      rows.join('') +
      (p.note ? `<div class="disc">${esc(p.note)}</div>` : '') +
      `<div class="src"><b>Source:</b> ${esc(kin.sourceFor(focus))}</div>`
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

  const MARRIED = '<div class="uconn marr"><span>married</span></div>';

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
    return steps + (marriedIn ? MARRIED + ucard(marriedIn, '', ' here') : '');
  }

  function linkGraph(a, b) {
    const d = kin.linkDiagram(a, b);
    if (!d || d.kind === 'self') return '';
    if (d.kind === 'spouse') {
      return `<div class="ulink pair">${ucard(a, '', ' here')}${MARRIED}${ucard(b, '', ' here')}</div>`;
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
        (atApex ? ucard(atApex, '', ' here') + MARRIED : '') +
        ucard(d.via, '', atApex ? '' : ' here') +
        arm(emptyLeft ? right : left, marriedOn(emptyLeft ? 'right' : 'left')) +
        '</div>'
      );
    }

    return (
      '<div class="ulink">' +
      `<div class="uapex">${ucard(d.via, 'they meet here')}</div>` +
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
          `<div class="depthlab">${known} generation${known > 1 ? 's' : ''} known</div>` +
          (line.origin ? `<div class="origin"><span class="ol">Name origin.</span> ${esc(line.origin)}</div>` : '') +
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

  function searchResults(results, term) {
    if (!term.trim()) {
      return '<p class="hint">Search for a name, a year, or a place — “Oostende”, “1943”, “Evergem 1879”.</p>';
    }
    if (!results.length) {
      return `<p class="hint">Nobody matches “${esc(term.trim())}”.</p>`;
    }
    const rows = results
      .map(r => {
        const p = people[r.id];
        const meta = [kin.relationship(r.id), p.dates].filter(Boolean).join(' · ');
        const ctx = r.context
          ? `<div class="hc"><span class="hk">${esc(r.context.label)}</span>` +
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
    const n = results.length;
    return (
      `<p class="rescount">${n} ${n === 1 ? 'person' : 'people'} of ` +
      `${Object.keys(people).length} · click to open in the tree</p>` +
      `<div class="results">${rows}</div>`
    );
  }

  // ---------- the side panel: this person's link to the root ----------

  // The same arch, with one end pinned to the root. For a direct ancestor it is the
  // straight line of descent it always was; for an aunt or a cousin it is the fork
  // that the old single thread had to apologise for in prose.
  function descent(id) {
    if (id === kin.ROOT) {
      return (
        `<p class="lnote">${esc(people[id].name)} is where this tree is measured from — ` +
        'every line in it ends here.</p>'
      );
    }
    return `<div class="lhead">${relationText(id, kin.ROOT)}</div>` + linkGraph(id, kin.ROOT);
  }

  const legend = () =>
    Object.entries(meta.confidenceLabels)
      .map(([key, label]) => `<span><i class="swatch sw-${key}"></i>${esc(label)}</span>`)
      .join('');

  // ---------- index ----------

  // The index is grouped by how each person relates to the root family, and
  // membership is derived rather than listed — someone added to the data shows up
  // here without anyone having to remember to add them to a second file.
  //
  // `groups.js` is still used, but only for its headings: where it has a curated
  // title for someone ("Bostyn & Cappaert (Marcel's mother)") that reads better
  // than the bare branch name, so it wins. Anyone it does not mention falls back
  // to their branch, which is why nobody can go missing.
  function indexCards() {
    const rootName = people[kin.ROOT] ? people[kin.ROOT].name : '';
    const CATEGORIES = [
      { key: 'ancestor', title: 'Ancestors', blurb: `The direct line above ${rootName} — parents, grandparents, and up.` },
      { key: 'relative', title: 'Blood relatives', blurb: 'Blood, but off the direct line: siblings, aunts and uncles, cousins, and their descendants.' },
      { key: 'other', title: 'Others', blurb: 'Married into the family, or not yet connected to it.' },
    ];

    // Each person names their own line; groups.js only says what the lines are
    // called and in what order. Nobody is listed twice, and nobody can be left
    // out of a list, because there is no list.
    const titleOfLine = {};
    const orderOfTitle = {};
    groups.forEach((g, i) => {
      titleOfLine[g.key] = g.title;
      orderOfTitle[g.title] = i;
    });

    const personRow = id => {
      const p = people[id];
      const rel = kin.relationship(id);
      const extra = [rel, p.occupation, p.nickname && `“${p.nickname}”`].filter(Boolean).join(' · ');
      return (
        `<div class="p" data-id="${esc(id)}" style="cursor:pointer"><b>${esc(p.name)}</b>` +
        (p.dates ? ` <span class="d">— ${esc(p.dates)}</span>` : '') +
        (extra ? ` <span class="d">· ${esc(extra)}</span>` : '') +
        '</div>'
      );
    };

    return CATEGORIES.map(catg => {
      const members = Object.keys(people).filter(id => kin.categoryOf(id) === catg.key);
      if (!members.length) return '';

      const buckets = new Map();
      for (const id of members) {
        const key = titleOfLine[people[id].line] || people[id].branch || 'Unplaced';
        if (!buckets.has(key)) buckets.set(key, []);
        buckets.get(key).push(id);
      }

      // Curated headings keep the order they have in groups.js; anything derived
      // from a branch name follows, alphabetically.
      const titles = [...buckets.keys()].sort((a, b) => {
        const ia = a in orderOfTitle ? orderOfTitle[a] : Infinity;
        const ib = b in orderOfTitle ? orderOfTitle[b] : Infinity;
        return ia !== ib ? ia - ib : a.localeCompare(b);
      });

      // Within a heading, read down the generations rather than alphabetically —
      // closest to the root first. Both are derived, but only one tells a story.
      const byGeneration = (a, b) => {
        const da = a in kin.distance ? kin.distance[a] : Infinity;
        const db = b in kin.distance ? kin.distance[b] : Infinity;
        return da - db || people[a].name.localeCompare(people[b].name);
      };
      const cards = titles
        .map(t => `<div class="bcard"><h4>${esc(t)}</h4>${buckets.get(t).sort(byGeneration).map(personRow).join('')}</div>`)
        .join('');

      return (
        `<h3 class="catsec">${esc(catg.title)}<span class="n">${members.length}</span></h3>` +
        `<p class="catblurb">${esc(catg.blurb)}</p>` +
        `<div class="branchgrid">${cards}</div>`
      );
    }).join('');
  }

  // Objective (c): name the relation between any two people in the index.
  function relationText(a, b) {
    if (!a || !b || !people[a] || !people[b]) return '<span class="muted">Pick two people.</span>';
    const r = kin.relationBetween(a, b);
    if (!r) {
      return (
        `<b>${esc(people[a].name)}</b> and <b>${esc(people[b].name)}</b> have no connection recorded in the tree — ` +
        'no shared ancestor, and no marriage linking them.'
      );
    }
    if (r.kind === 'self') return `<b>${esc(people[a].name)}</b> — that is the same person.`;

    const A = `<b>${esc(people[a].name)}</b>`;
    const B = `<b>${esc(people[b].name)}</b>`;
    const line = `${A} is ${B}’s <em>${esc(r.label)}</em>.`;
    // An in-law is two facts, not one — a blood relation and a marriage — and saying
    // it as one produces "X is Y's aunt of Y's husband". Two clauses, one per step.
    if (r.kind === 'marriage' && r.through) {
      const T = `<b>${esc(people[r.through].name)}</b>`;
      return r.married === 'b'
        ? `${A} is the <em>${esc(r.label)}</em> of ${T}, who married ${B}.`
        : `${A} married ${T}, who is ${B}’s <em>${esc(r.label)}</em>.`;
    }
    if (r.kind !== 'blood' || !r.via) return line;
    // When one of them is the common ancestor, saying so again explains nothing —
    // the relation already is the line between them.
    if (r.da === 0 || r.db === 0) {
      const steps = Math.max(r.da, r.db);
      return line + `<div class="via">${steps} generation${steps === 1 ? '' : 's'} apart, in a direct line.</div>`;
    }
    const gen = n => `${n} generation${n === 1 ? '' : 's'} up`;
    return (
      line +
      `<div class="via">Common ancestor: <b>${esc(people[r.via].name)}</b> — ` +
      `${gen(r.da)} from ${esc(people[a].name)}, ${gen(r.db)} from ${esc(people[b].name)}.</div>`
    );
  }

  // What the index's relation finder shows: the sentence, and then the route that
  // sentence came from. Neither is worth much alone — a label with no visible join
  // is a claim, and a drawing with no label makes the reader name the shape.
  const relationPanel = (a, b) => relationText(a, b) + linkGraph(a, b);

  return {
    tooltip, pedigree, detail, lineageColumns, indexCards, relationPanel,
    legend, searchResults, descent,
  };
};

})();
