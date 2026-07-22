// Everything derived from the raw records: how people relate to the root of the
// tree, who their children are, and which source backs each person.

FamilyTree.createKinship = function ({ meta, people, branches }) {
  const ROOT = meta.root;

  // Walk up from the root through father/mother, recording both how many
  // generations away each ancestor is and which child they were reached through.
  // That second map is what lets us replay a single line back down again.
  const distance = { [ROOT]: 0 };
  const descendant = {};
  (() => {
    const queue = [ROOT];
    for (let i = 0; i < queue.length; i++) {
      const p = people[queue[i]];
      if (!p) continue;
      for (const parent of [p.father, p.mother]) {
        if (parent && people[parent] && !(parent in distance)) {
          distance[parent] = distance[queue[i]] + 1;
          descendant[parent] = queue[i];
          queue.push(parent);
        }
      }
    }
  })();

  // Everyone the walk above reached is, by construction, a direct ancestor:
  // it only ever steps through father/mother, so siblings, aunts, uncles and
  // spouses who are nobody's parent are not in it. Distance 0 is the root pair
  // themselves, who are not their own ancestors. Someone appearing in two lines
  // is counted once.
  const directAncestorCount = () => Object.keys(distance).filter(id => distance[id] > 0).length;

  // The single thread from an ancestor down to the root, oldest first.
  const descentFrom = id => {
    if (!(id in distance)) return null;
    const path = [id];
    let at = id;
    while (at !== ROOT) {
      at = descendant[at];
      path.push(at);
    }
    return path;
  };

  // How anyone connects to the root — directly, or as the child of someone who does.
  // Aunts, uncles and siblings have no descent of their own, but the line they
  // branch off is still the interesting thing to show.
  function lineOfDescent(id) {
    const direct = descentFrom(id);
    if (direct) return { kind: 'direct', path: direct };

    const p = people[id];
    if (p) {
      const parents = [p.father, p.mother].filter(x => x && x in distance);
      if (parents.length) {
        // Prefer whichever parent sits closest to the root.
        const via = parents.sort((a, b) => distance[a] - distance[b])[0];
        return { kind: 'collateral', path: descentFrom(via), branchesFrom: via, person: id };
      }
    }
    return { kind: 'none', path: null };
  }

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

  return {
    ROOT, relationship, childrenOf, sourceFor, confidenceOf, isResearchable,
    distance, descentFrom, lineOfDescent, directAncestorCount,
  };
};
