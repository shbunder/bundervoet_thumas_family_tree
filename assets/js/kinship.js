// Everything derived from the raw records: how people relate to the root of the
// tree, who their children are, and which source backs each person.

FamilyTree.createKinship = function ({ meta, people, branches }) {
  const ROOT = meta.root;

  // Distance in generations from the root, walking up through father/mother.
  const distance = (() => {
    const d = { [ROOT]: 0 };
    const queue = [ROOT];
    for (let i = 0; i < queue.length; i++) {
      const p = people[queue[i]];
      if (!p) continue;
      for (const parent of [p.father, p.mother]) {
        if (parent && people[parent] && !(parent in d)) {
          d[parent] = d[queue[i]] + 1;
          queue.push(parent);
        }
      }
    }
    return d;
  })();

  // Inferred from the role a person plays for their children, since the records
  // carry no gender field of their own.
  const genderOf = id => {
    for (const p of Object.values(people)) {
      if (p.father === id) return 'm';
      if (p.mother === id) return 'f';
    }
    return null;
  };

  const cap = s => (s ? s[0].toUpperCase() + s.slice(1) : s);
  const greatPrefix = n => (n <= 0 ? '' : n === 1 ? 'Great-' : `${n}×-great-`);

  function relationship(id) {
    if (id === ROOT) return 'The children';
    const g = genderOf(id);
    const d = distance[id];
    if (d !== undefined) {
      if (d === 1) return g === 'f' ? 'Mother' : 'Father';
      return cap(greatPrefix(d - 2) + 'grand' + (g === 'f' ? 'mother' : 'father'));
    }
    // Not a direct ancestor: describe them by their parents' distance instead.
    const p = people[id];
    if (!p) return '';
    const parentDepths = [p.father, p.mother]
      .filter(x => x && x in distance)
      .map(x => distance[x]);
    if (parentDepths.length && g) {
      const step = Math.min(...parentDepths) - 1;
      if (step >= 1) return cap(greatPrefix(step - 1) + (g === 'f' ? 'aunt' : 'uncle'));
    }
    return p.role || '';
  }

  const childrenOf = id =>
    Object.keys(people).filter(k => people[k].father === id || people[k].mother === id);

  // Per-person source wins, then the branch default, then the catch-all.
  const sourceFor = id => {
    const p = people[id];
    return p.source || (p.branch && branches[p.branch]) || meta.defaultSource;
  };

  const confidenceOf = id => people[id]?.confidence || 'doc';
  const isResearchable = id => Boolean(people[id]) && confidenceOf(id) !== 'unk';

  return { ROOT, relationship, childrenOf, sourceFor, confidenceOf, isResearchable, distance };
};
