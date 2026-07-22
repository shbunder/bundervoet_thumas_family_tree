// Searching the tree.
//
// Places are not a field of their own — they live inside the free-text dates,
// born and died strings ("1879 Evergem – 1943 Oostende"), so a search for a town
// has to look across everything rather than at one column.

(function () {

// Lowercases and strips accents, keeping a map from each folded character back to
// the character it came from, so a match can be highlighted in the original text.
// Also builds a whitespace-free variant, so "dekeyser" finds "De Keyser".
function fold(text) {
  const loose = [];
  const looseMap = [];
  const tight = [];
  const tightMap = [];

  for (let i = 0; i < text.length; i++) {
    const folded = text[i].normalize('NFD').replace(/\p{Diacritic}/gu, '').toLowerCase();
    for (const ch of folded) {
      loose.push(ch);
      looseMap.push(i);
      if (!/\s/.test(ch)) {
        tight.push(ch);
        tightMap.push(i);
      }
    }
  }
  return { loose: loose.join(''), looseMap, tight: tight.join(''), tightMap };
}

// Where a term sits in a folded field, expressed as a range in the original string.
function locate(folded, term) {
  let at = folded.loose.indexOf(term);
  if (at >= 0) {
    return {
      range: [folded.looseMap[at], folded.looseMap[at + term.length - 1] + 1],
      wordStart: at === 0 || /[\s·—–\-(,.]/.test(folded.loose[at - 1]),
    };
  }
  const squeezed = term.replace(/\s+/g, '');
  if (!squeezed) return null;
  at = folded.tight.indexOf(squeezed);
  if (at < 0) return null;
  return {
    range: [folded.tightMap[at], folded.tightMap[at + squeezed.length - 1] + 1],
    wordStart: at === 0,
  };
}

FamilyTree.createSearch = function ({ people }) {
  // Ordered by how much a match in each field says about relevance.
  const FIELDS = [
    { key: 'name', label: 'Name', weight: 100 },
    { key: 'born', label: 'Born', weight: 60 },
    { key: 'died', label: 'Died', weight: 60 },
    { key: 'dates', label: 'Dates', weight: 55 },
    { key: 'spouse', label: 'Spouse', weight: 35 },
    { key: 'role', label: 'Role', weight: 30 },
    { key: 'branch', label: 'Branch', weight: 20 },
    { key: 'note', label: 'Note', weight: 10 },
    { key: 'source', label: 'Source', weight: 5 },
  ];

  const textOf = (p, key) => {
    if (key === 'spouse') {
      return p.spouse ? [p.spouse.name, p.spouse.detail].filter(Boolean).join(' — ') : '';
    }
    return p[key] || '';
  };

  const index = Object.keys(people).map(id => ({
    id,
    fields: FIELDS.map(f => {
      const raw = textOf(people[id], f.key);
      return raw ? { key: f.key, label: f.label, weight: f.weight, raw, folded: fold(raw) } : null;
    }).filter(Boolean),
  }));

  // Every term must match somewhere (AND), so "oostende 1943" narrows rather than widens.
  function query(input) {
    const terms = fold(input).loose.split(/\s+/).filter(Boolean);
    if (!terms.length) return [];

    const results = [];

    for (const entry of index) {
      const ranges = {};
      let score = 0;
      let matchedAll = true;

      for (const term of terms) {
        let best = null;

        for (const field of entry.fields) {
          const hit = locate(field.folded, term);
          if (!hit) continue;
          (ranges[field.key] ||= []).push(hit.range);
          const value = field.weight + (hit.wordStart ? 25 : 0);
          if (!best || value > best.value) best = { value, field };
        }

        if (!best) {
          matchedAll = false;
          break;
        }
        score += best.value;
      }

      if (!matchedAll) continue;

      // The most telling field that matched, for the context line under the name.
      const context = entry.fields
        .filter(f => f.key !== 'name' && ranges[f.key])
        .sort((a, b) => b.weight - a.weight)[0];

      results.push({
        id: entry.id,
        score,
        ranges,
        context: context ? { label: context.label, key: context.key, raw: context.raw } : null,
      });
    }

    return results.sort(
      (a, b) => b.score - a.score || people[a.id].name.localeCompare(people[b.id].name)
    );
  }

  return { query, size: index.length };
};

})();
