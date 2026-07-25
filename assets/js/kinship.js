// Everything derived from the raw records: how any two people are related, who
// their children are, and which source backs each person.
//
// The engine underneath is root-free — it works from the lowest common ancestor
// of a pair, so it can relate anyone to anyone. The tree's familiar labels
// ("Great-grandmother") are just that engine pointed at the root.

FamilyTree.createKinship = function ({ meta, people, branches }) {
  const ROOT = meta.root;
  // A forest has more than one starting family. `roots` is what the index and the
  // validator measure from; a tree with a single root is the one-element case.
  const ROOTS = (meta.roots && meta.roots.length ? meta.roots : [ROOT]).filter(id => people[id]);

  const ids = Object.keys(people);

  // ---------- indexes built once ----------
  // These were previously scans over every person, run per lookup. That is O(n²)
  // across a full render, which is invisible at 300 people and fatal at 10,000.

  // Sex comes from the record if it states one, and is otherwise inferred from the
  // role someone plays for their children — being recorded as a `father` is
  // evidence, not a guess. For anyone who is nobody's parent and says nothing, it
  // stays unknown, and the relation names below fall back to neutral wording
  // rather than picking one. Guessing from a forename would be inventing a fact.
  const gender = {};
  const children = {};
  for (const id of ids) {
    const p = people[id];
    if (p.sex === 'f' || p.sex === 'm') gender[id] = p.sex;
    if (p.father) {
      if (!people[p.father]?.sex) gender[p.father] = 'm';
      (children[p.father] = children[p.father] || []).push(id);
    }
    if (p.mother) {
      if (!people[p.mother]?.sex) gender[p.mother] = 'f';
      (children[p.mother] = children[p.mother] || []).push(id);
    }
  }
  const genderOf = id => gender[id] || null;
  const childrenOf = id => children[id] || [];

  // Everyone born of either of the same parents. Half-siblings are in, because they
  // are siblings; which kind they are is what `bloodRelation` is for, and the row
  // that shows them says so on each card.
  function siblingsOf(id) {
    const p = people[id];
    if (!p) return [];
    const seen = new Set([id]);
    const out = [];
    for (const parent of [p.father, p.mother]) {
      for (const kid of childrenOf(parent)) {
        if (!seen.has(kid)) {
          seen.add(kid);
          out.push(kid);
        }
      }
    }
    return out;
  }

  // ---------- ancestry ----------

  // Every ancestor of someone, mapped to how many generations up they sit. The
  // person themselves is in it at 0, which is what makes the relation cases below
  // fall out uniformly. Breadth-first, so the first time a person is reached is
  // by their shortest line — cousin marriages put the same ancestor on two paths.
  const ancestorCache = {};
  function ancestorsOf(id) {
    if (ancestorCache[id]) return ancestorCache[id];
    const out = new Map([[id, 0]]);
    const queue = [id];
    for (let i = 0; i < queue.length; i++) {
      const at = queue[i];
      const p = people[at];
      if (!p) continue;
      const d = out.get(at);
      for (const parent of [p.father, p.mother]) {
        if (parent && people[parent] && !out.has(parent)) {
          out.set(parent, d + 1);
          queue.push(parent);
        }
      }
    }
    return (ancestorCache[id] = out);
  }

  // The actual steps from someone up to one of their ancestors — [from, …, anc] —
  // by the same shortest route `ancestorsOf` counted, so the distance the relation
  // is named from and the chain the page draws can never disagree. Null if `anc` is
  // not above `from` at all.
  function ancestorLine(from, anc) {
    if (!people[from] || !people[anc]) return null;
    if (from === anc) return [from];
    const cameFrom = new Map([[from, null]]);
    const queue = [from];
    for (let i = 0; i < queue.length; i++) {
      const at = queue[i];
      const p = people[at];
      if (!p) continue;
      for (const parent of [p.father, p.mother]) {
        if (!parent || !people[parent] || cameFrom.has(parent)) continue;
        cameFrom.set(parent, at);
        if (parent === anc) {
          const path = [];
          for (let step = parent; step !== null; step = cameFrom.get(step)) path.push(step);
          return path.reverse();
        }
        queue.push(parent);
      }
    }
    return null;
  }

  // How many generations up from the root each ancestor sits. The index reads it to
  // order a heading's people by generation instead of alphabetically.
  const distance = {};
  (() => {
    const queue = [ROOT];
    distance[ROOT] = 0;
    for (let i = 0; i < queue.length; i++) {
      const p = people[queue[i]];
      if (!p) continue;
      for (const parent of [p.father, p.mother]) {
        if (parent && people[parent] && !(parent in distance)) {
          distance[parent] = distance[queue[i]] + 1;
          queue.push(parent);
        }
      }
    }
  })();

  const directAncestorCount = () => Object.keys(distance).filter(id => distance[id] > 0).length;

  // ---------- naming a relationship ----------

  const cap = s => (s ? s[0].toUpperCase() + s.slice(1) : s);
  const greatPrefix = n => (n <= 0 ? '' : n === 1 ? 'great-' : `${n}×-great-`);
  const greats = (n, word) => greatPrefix(n) + word;
  const ORDINALS = ['', 'first', 'second', 'third', 'fourth', 'fifth', 'sixth', 'seventh', 'eighth', 'ninth', 'tenth'];
  const ordinal = n => ORDINALS[n] || `${n}th`;
  const TIMES = ['', 'once', 'twice', 'three times', 'four times', 'five times'];
  const removedWord = n => TIMES[n] || `${n} times`;
  // Falls back to the neutral word when the record does not say, so an unknown
  // never silently reads as a man.
  const byGender = (id, female, male, neutral) => {
    const g = genderOf(id);
    return g === 'f' ? female : g === 'm' ? male : neutral !== undefined ? neutral : male;
  };

  // The closest ancestor the two share. Ties are broken toward the most balanced
  // pair of distances, so a couple's shared child reads as "sibling" rather than
  // picking whichever grandparent happened to be visited first.
  function commonAncestor(a, b) {
    const A = ancestorsOf(a);
    const B = ancestorsOf(b);
    // Iterate the smaller set.
    const [small, large, flip] = A.size <= B.size ? [A, B, false] : [B, A, true];
    let best = null;
    for (const [anc, d1] of small) {
      const d2 = large.get(anc);
      if (d2 === undefined) continue;
      const da = flip ? d2 : d1;
      const db = flip ? d1 : d2;
      const total = da + db;
      const skew = Math.abs(da - db);
      if (!best || total < best.total || (total === best.total && skew < best.skew)) {
        best = { id: anc, da, db, total, skew };
      }
    }
    return best;
  }

  // Names the blood relation of a to b — "a is b's ___" — or null if they share
  // no ancestor. `via` is the common ancestor, so callers can show the join.
  function bloodRelation(a, b) {
    if (a === b) return { label: 'the same person', via: a, kind: 'self' };
    if (!people[a] || !people[b]) return null;
    const lca = commonAncestor(a, b);
    if (!lca) return null;
    const { da, db } = lca;
    const out = label => ({ label, via: lca.id, da, db, kind: 'blood' });

    // One is an ancestor of the other: the common ancestor IS one of them.
    if (da === 0) {
      return out(db === 1
        ? byGender(a, 'mother', 'father', 'parent')
        : greats(db - 2, byGender(a, 'grandmother', 'grandfather', 'grandparent')));
    }
    if (db === 0) {
      return out(da === 1
        ? byGender(a, 'daughter', 'son', 'child')
        : greats(da - 2, byGender(a, 'granddaughter', 'grandson', 'grandchild')));
    }

    // Siblings. Sharing both parents is a full sibling; sharing one is a half.
    if (da === 1 && db === 1) {
      const pa = people[a];
      const pb = people[b];
      const shared = [pa.father, pa.mother].filter(x => x && (x === pb.father || x === pb.mother)).length;
      const word = byGender(a, 'sister', 'brother', 'sibling');
      return out(shared >= 2 ? word : `half-${word}`);
    }

    // One sits a generation or more above the other's line: aunt/uncle downward,
    // niece/nephew upward.
    if (da === 1) return out(greats(db - 2, byGender(a, 'aunt', 'uncle', 'aunt or uncle')));
    if (db === 1) return out(greats(da - 2, byGender(a, 'niece', 'nephew', 'niece or nephew')));

    // Otherwise cousins: the degree is the shorter leg, the removal is the gap.
    const degree = Math.min(da, db) - 1;
    const removed = Math.abs(da - db);
    return out(`${ordinal(degree)} cousin${removed ? ` ${removedWord(removed)} removed` : ''}`);
  }

  const spouseIdsOf = id => (people[id]?.spouses || []).map(s => s.id).filter(id2 => id2 && people[id2]);

  // Blood first; failing that, look one marriage step away. Beyond one step the
  // phrasing stops meaning anything useful, so it stops there rather than
  // inventing chains of in-laws.
  function relationBetween(a, b) {
    if (!people[a] || !people[b]) return null;
    const blood = bloodRelation(a, b);
    if (blood) return blood;

    if (spouseIdsOf(a).includes(b)) {
      return { label: byGender(a, 'wife', 'husband', 'spouse'), kind: 'marriage' };
    }
    // Related through exactly one marriage, from one end or the other. The blood
    // relation is returned as itself and the marriage step as `through`, rather than
    // folded into one string: only the caller knows whether it is writing a sentence
    // or drawing the join, and a label that has already committed to a sentence
    // cannot be drawn.
    for (const sp of spouseIdsOf(b)) {
      const r = bloodRelation(a, sp);
      if (r) return { label: r.label, kind: 'marriage', through: sp, married: 'b' };
    }
    for (const sp of spouseIdsOf(a)) {
      const r = bloodRelation(sp, b);
      if (r) return { label: r.label, kind: 'marriage', through: sp, married: 'a' };
    }
    return null;
  }

  // The same connection `relationBetween` names, but as the route rather than the
  // word for it: two arms that climb from each person to the ancestor they share.
  // Drawn, that is an arch — up one side, across, down the other — and it is the
  // only form that shows *where* two people meet rather than asserting that they do.
  //
  // `left` and `right` both run person-first, ancestor-last, so they are the two
  // sides of the arch read outwards-in. A marriage step, when one is needed, hangs
  // off the foot of its arm: the blood link is between `married.to` and the other
  // person, and `married.id` is attached to it by marriage, never inside it.
  function linkDiagram(a, b) {
    if (!people[a] || !people[b]) return null;
    if (a === b) return { kind: 'self' };

    const blood = commonAncestor(a, b);
    if (blood) {
      return { kind: 'blood', via: blood.id, left: ancestorLine(a, blood.id), right: ancestorLine(b, blood.id) };
    }
    // Checked before the loops below, which would otherwise pair someone with
    // themselves through their own spouse.
    if (spouseIdsOf(a).includes(b)) return { kind: 'spouse', left: [a], right: [b] };

    const step = (x, y, side) => {
      for (const sp of spouseIdsOf(y)) {
        const lca = commonAncestor(x, sp);
        if (!lca) continue;
        const arms = { left: ancestorLine(x, lca.id), right: ancestorLine(sp, lca.id) };
        return {
          kind: 'marriage',
          via: lca.id,
          left: side === 'right' ? arms.left : arms.right,
          right: side === 'right' ? arms.right : arms.left,
          married: { id: y, to: sp, side },
        };
      }
      return null;
    };
    // One marriage step, from either end. Beyond one the drawing would claim a
    // relationship that the wording already refuses to name.
    return step(a, b, 'right') || step(b, a, 'left');
  }

  // The label the tree shows on a node: their relation to the root. The roots are
  // the reference point, so they get no label of their own — saying a child is
  // their own sibling's sibling explains nothing.
  const rootSet = new Set(ROOTS);
  function relationship(id) {
    if (rootSet.has(id)) return '';
    const r = bloodRelation(id, ROOT);
    return r && r.kind === 'blood' ? cap(r.label) : '';
  }

  // ---------- who belongs where ----------

  // Three groups, all derived, so nobody can be added to the data and then be
  // missing from the index because a hand-kept list was not updated.
  //   ancestor — a direct ancestor of a root
  //   relative — blood, but not a direct ancestor: siblings, cousins, descendants
  //   other    — connected by marriage only, or not connected at all
  const category = (() => {
    const ancestors = new Set();
    for (const r of ROOTS) for (const [anc, d] of ancestorsOf(r)) if (d > 0) ancestors.add(anc);

    // Everyone descended from a root or from any of its ancestors is blood.
    const blood = new Set([...ROOTS, ...ancestors]);
    const queue = [...blood];
    for (let i = 0; i < queue.length; i++) {
      for (const kid of childrenOf(queue[i])) {
        if (!blood.has(kid)) {
          blood.add(kid);
          queue.push(kid);
        }
      }
    }

    const out = {};
    for (const id of ids) out[id] = ancestors.has(id) ? 'ancestor' : blood.has(id) ? 'relative' : 'other';
    return out;
  })();

  const categoryOf = id => category[id] || 'other';

  // ---------- sources ----------

  // Per-person source wins, then the branch default, then the catch-all.
  const sourceFor = id => {
    const p = people[id];
    return p.source || (p.branch && branches[p.branch]) || meta.defaultSource;
  };

  const confidenceOf = id => people[id]?.confidence || 'doc';
  const isResearchable = id => Boolean(people[id]) && confidenceOf(id) !== 'unk';

  return {
    ROOT, ROOTS, relationship, relationBetween, bloodRelation, ancestorsOf, commonAncestor,
    childrenOf, siblingsOf, genderOf, categoryOf, sourceFor, confidenceOf, isResearchable,
    distance, directAncestorCount, ancestorLine, linkDiagram,
  };
};
