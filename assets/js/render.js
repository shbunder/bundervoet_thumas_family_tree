// Turns records into markup. Nothing here knows where the data came from.

(function () {

const esc = s =>
  String(s ?? '')
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');

const spouseText = sp => '❦ ' + (sp.detail ? `${sp.name} — ${sp.detail}` : sp.name);

FamilyTree.createRenderer = function ({ meta, people, lineages, groups }, kin) {
  const conf = id => kin.confidenceOf(id);

  // ---------- shared pieces ----------

  function node(id, { role, arrow = '↑', focus = false } = {}) {
    if (!id) return '<div class="node unk"><div class="nm">Unknown</div><div class="dt">to research</div></div>';
    const p = people[id];
    const c = conf(id);
    const label = focus ? kin.relationship(id) || 'in focus' : role || kin.relationship(id) || p.role || '';
    const climb = !focus && c !== 'unk' ? `<span class="climb">climb ${arrow}</span>` : '';
    return (
      `<div class="node ${focus ? 'focus ' : ''}${c}" data-id="${esc(id)}">` +
      climb +
      (label ? `<div class="rl">${esc(label)}</div>` : '') +
      `<div class="nm">${esc(p.name)}</div>` +
      (p.dates ? `<div class="dt">${esc(p.dates)}</div>` : '') +
      '</div>'
    );
  }

  const spouseNode = sp =>
    '<div class="node fam spouse"><div class="rl">spouse</div>' +
    `<div class="nm">${esc(sp.name)}</div>` +
    (sp.detail ? `<div class="dt">${esc(sp.detail)}</div>` : '') +
    '</div>';

  // A parent's own parents, shown as a couple with a drop line beneath them.
  // The caption only shows on narrow screens: there the two couples sit one
  // above the other, where the drop line would wrongly read as descent, so it
  // is hidden and this says whose parents each couple is instead.
  function grandparentCouple(parentId) {
    const p = parentId && people[parentId];
    if (!p || (!p.father && !p.mother)) return '';
    return (
      `<div class="gplab">${esc(p.name)}’s parents</div>` +
      `<div class="couple">${node(p.father)}<span class="xmark">×</span>${node(p.mother)}</div>` +
      '<div class="vline"></div>'
    );
  }

  const parentLine = (label, id) =>
    id && people[id]
      ? `<div class="kv"><b>${label}:</b> ${esc(people[id].name)}` +
        (people[id].dates ? ` (${esc(people[id].dates)})` : '') +
        '</div>'
      : '';

  function subtitleFor(id) {
    const p = people[id];
    const rel = kin.relationship(id);
    return [rel, p.dates, p.role && p.role !== rel ? p.role : ''].filter(Boolean).join(' · ');
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
      (p.spouse ? `<div class="kv"><b>Spouse:</b> ${esc(spouseText(p.spouse))}</div>` : '') +
      parentLine('Father', p.father) +
      parentLine('Mother', p.mother) +
      (kids.length ? `<div class="kv"><b>Children:</b> ${esc(kids.join(', '))}</div>` : '') +
      (p.note ? `<div class="nt">${esc(p.note)}</div>` : '') +
      `<div class="sr"><b>Source:</b> ${esc(kin.sourceFor(id))}</div>`
    );
  }

  // ---------- explorer ----------

  function pedigree(focus) {
    const p = people[focus];
    const fatherGP = grandparentCouple(p.father);
    const motherGP = grandparentCouple(p.mother);
    let html = '';

    // The two rows are tagged so a narrow screen can stack the four grandparents
    // into two couples while keeping the parents side by side.
    if (fatherGP || motherGP) {
      html += `<div class="pgrid gp"><div class="pcol">${fatherGP}</div><div class="pcol"></div><div class="pcol">${motherGP}</div></div>`;
    }
    if (p.father || p.mother) {
      html +=
        `<div class="gplab">${esc(p.name)}’s parents</div>` +
        `<div class="pgrid parents"><div class="pcol">${node(p.father)}</div>` +
        '<div class="pcol xcol"><span class="xmark">×</span></div>' +
        `<div class="pcol">${node(p.mother)}</div></div>` +
        '<div class="vline tall"></div>';
    }

    html +=
      '<div class="couple">' +
      node(focus, { focus: true }) +
      (p.spouse ? `<span class="xmark">×</span>${spouseNode(p.spouse)}` : '') +
      '</div>';

    const children = kin.childrenOf(focus);
    if (children.length) {
      html +=
        '<div class="vline tall"></div>' +
        '<div class="childlab">children · click to climb down ↓</div>' +
        `<div class="crow">${children.map(k => node(k, { arrow: '↓' })).join('')}</div>`;
    }
    return html;
  }

  function detail(focus) {
    const p = people[focus];
    return (
      `<h3>${esc(p.name)}</h3><div class="sub">${esc(subtitleFor(focus))}</div>` +
      (p.spouse ? `<div class="kv"><b>Spouse:</b> ${esc(spouseText(p.spouse))}</div>` : '') +
      parentLine('Father', p.father) +
      parentLine('Mother', p.mother) +
      (p.note ? `<div class="disc">${esc(p.note)}</div>` : '') +
      '<div class="kv" style="margin-top:8px;font-size:.82rem;color:var(--muted)">' +
      `<b style="color:var(--accent)">Source:</b> ${esc(kin.sourceFor(focus))}</div>`
    );
  }

  // ---------- lineages ----------

  function lineageColumns() {
    return lineages
      .map(line => {
        const known = line.chain.filter(id => kin.isResearchable(id)).length;
        const chain = line.chain
          .map((id, i) => {
            const p = people[id];
            return (
              `<div class="cnode ${conf(id)}" data-id="${esc(id)}">` +
              `<div class="nm">${esc(p.name)}</div>` +
              (p.dates ? `<div class="dt">${esc(p.dates)}</div>` : '') +
              '</div>' +
              (i < line.chain.length - 1 ? '<div class="cconn"></div>' : '')
            );
          })
          .join('');
        return (
          `<div class="col"><h3>${esc(line.key)}</h3>` +
          `<div class="cap">${esc(line.caption)}</div>` +
          `<div class="chain">${chain}</div>` +
          `<div class="depthlab">${known} generation${known > 1 ? 's' : ''} known</div></div>`
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

  // ---------- line of descent ----------

  // The single thread from whoever is in focus down to the children.
  function descent(id) {
    const line = kin.lineOfDescent(id);

    if (line.kind === 'none') {
      return (
        `<p class="lnote">${esc(people[id].name)} is not linked to Renée &amp; Léon by ` +
        'any recorded parent, so there is no line to walk yet.</p>'
      );
    }

    let head = '';
    if (line.kind === 'collateral') {
      const via = people[line.branchesFrom];
      head =
        `<p class="lnote">${esc(people[id].name)} is not a direct ancestor. ` +
        `The line below is ${esc(via.name)}’s — where ${esc(people[id].name)} branches off.</p>` +
        `<div class="lstep off"><div class="lname">${esc(people[id].name)}</div>` +
        `<div class="lrel">off the direct line</div></div>` +
        '<div class="lconn dashed"><span>child of</span></div>';
    }

    const steps = line.path
      .map((pid, i) => {
        const p = people[pid];
        const isFocus = pid === id;
        const generations = line.path.length - 1 - i;
        const label =
          pid === kin.ROOT
            ? 'the children'
            : generations === 1
              ? 'parent'
              : `${generations} generations up`;
        return (
          `<div class="lstep ${conf(pid)}${isFocus ? ' here' : ''}" data-id="${esc(pid)}">` +
          `<div class="lname">${esc(p.name)}</div>` +
          (p.dates ? `<div class="ldt">${esc(p.dates)}</div>` : '') +
          `<div class="lrel">${esc(label)}</div>` +
          '</div>' +
          (i < line.path.length - 1 ? '<div class="lconn"><span>↓</span></div>' : '')
        );
      })
      .join('');

    const depth = line.path.length - 1;
    const from = line.kind === 'collateral' ? ` from ${esc(people[line.branchesFrom].name)}` : '';
    const footer = depth
      ? `${depth} generation${depth === 1 ? '' : 's'}${from} down to Renée &amp; Léon`
      : 'Every line in the tree ends here.';
    return head + `<div class="lthread">${steps}</div>` + `<p class="ldepth">${footer}</p>`;
  }

  const legend = () =>
    Object.entries(meta.confidenceLabels)
      .map(([key, label]) => `<span><i class="swatch sw-${key}"></i>${esc(label)}</span>`)
      .join('');

  // ---------- index ----------

  function indexCards() {
    return groups
      .map(group => {
        const rows = group.people
          .map(id => {
            const p = people[id];
            const rel = kin.relationship(id);
            const extra = [rel, p.role && p.role !== rel ? p.role : ''].filter(Boolean).join(' · ');
            return (
              `<div class="p" data-id="${esc(id)}" style="cursor:pointer"><b>${esc(p.name)}</b>` +
              (p.dates ? ` <span class="d">— ${esc(p.dates)}</span>` : '') +
              (extra ? ` <span class="d">· ${esc(extra)}</span>` : '') +
              '</div>'
            );
          })
          .join('');
        return `<div class="bcard"><h4>${esc(group.title)}</h4>${rows}</div>`;
      })
      .join('');
  }

  return { tooltip, pedigree, detail, lineageColumns, indexCards, legend, searchResults, descent };
};

})();
