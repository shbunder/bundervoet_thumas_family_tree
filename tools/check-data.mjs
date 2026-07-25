#!/usr/bin/env node
// Checks the data files hang together. Run with: node tools/check-data.mjs
import fs from 'node:fs';
import path from 'node:path';
import vm from 'node:vm';
import { fileURLToPath } from 'node:url';

const DATA = path.join(path.dirname(fileURLToPath(import.meta.url)), '..', 'data');

const errors = [];
const warnings = [];
const fail = m => errors.push(m);

// The data files are scripts that call into a FamilyTree namespace. Running each
// against a stub both checks it parses and hands back the value it registered.
let captured;
const record = v => (captured = v);
const context = vm.createContext({
  FamilyTree: { person: record, roster: record, meta: record, branches: record, lineages: record, groups: record },
});

function read(file) {
  captured = undefined;
  const full = path.join(DATA, file);
  try {
    vm.runInContext(fs.readFileSync(full, 'utf8'), context, { filename: full });
  } catch (e) {
    fail(`${file}: ${e.message}`);
    return null;
  }
  if (captured === undefined) fail(`${file}: does not register anything`);
  return captured;
}

const ids = read('people.js') || [];
const meta = read('meta.js') || { confidenceLabels: {} };
const branches = read('branches.js') || {};
const lineages = read('lineages.js') || [];
const groups = read('groups.js') || [];

const FIELDS = new Set([
  'id', 'name', 'sex', 'dates', 'born', 'died', 'confidence', 'occupation', 'nickname', 'branch',
  'father', 'mother', 'spouses', 'source', 'note',
]);
const SPOUSE_FIELDS = new Set(['id', 'name', 'detail']);
const CONFIDENCE = new Set(Object.keys(meta.confidenceLabels));

// Every id in the manifest has a file, and no file is missing from the manifest.
const onDisk = fs
  .readdirSync(path.join(DATA, 'people'))
  .filter(f => f.endsWith('.js'))
  .map(f => f.slice(0, -3));
for (const id of ids) if (!onDisk.includes(id)) fail(`people.js lists "${id}" but data/people/${id}.js is missing`);
for (const f of onDisk) if (!ids.includes(f)) fail(`data/people/${f}.js exists but is not listed in people.js`);

const people = {};
for (const id of ids.filter(i => onDisk.includes(i))) {
  const p = read(`people/${id}.js`);
  people[id] = p;
  if (p.id !== id) fail(`${id}.js: "id" field says "${p.id}"`);
  if (!p.name) fail(`${id}.js: missing "name"`);
  if (!CONFIDENCE.has(p.confidence)) fail(`${id}.js: confidence "${p.confidence}" is not one of ${[...CONFIDENCE].join(', ')}`);
  if (p.branch && !(p.branch in branches)) fail(`${id}.js: branch "${p.branch}" is not in branches.js`);
  if ('sex' in p && p.sex !== 'f' && p.sex !== 'm') fail(`${id}.js: sex "${p.sex}" must be "f" or "m"`);
  if ('spouses' in p) {
    if (!Array.isArray(p.spouses)) fail(`${id}.js: "spouses" must be an array`);
    else for (const [i, s] of p.spouses.entries()) {
      if (!s || typeof s !== 'object') fail(`${id}.js: spouses[${i}] is not an object`);
      else {
        if (!s.name) fail(`${id}.js: spouses[${i}] has no "name"`);
        for (const k of Object.keys(s)) if (!SPOUSE_FIELDS.has(k)) warnings.push(`${id}.js: spouses[${i}] unknown field "${k}"`);
      }
    }
  }
  for (const k of Object.keys(p)) if (!FIELDS.has(k)) warnings.push(`${id}.js: unknown field "${k}"`);
}

// Parent links point at people who exist, and nobody is their own ancestor.
for (const [id, p] of Object.entries(people)) {
  for (const rel of ['father', 'mother']) {
    if (p[rel] && !people[p[rel]]) fail(`${id}.js: ${rel} "${p[rel]}" does not exist`);
  }
}

// Spouse links point at people who exist, and marriage is mutual: if A records B,
// B records A. Without that, building the tree downwards silently loses branches —
// a child hangs off the parent who happened to be written up first.
for (const [id, p] of Object.entries(people)) {
  for (const s of p.spouses || []) {
    if (!s.id) continue;
    if (!people[s.id]) { fail(`${id}.js: spouse id "${s.id}" does not exist`); continue; }
    if (s.id === id) fail(`${id}.js: is listed as their own spouse`);
    if (!(people[s.id].spouses || []).some(t => t.id === id)) {
      fail(`${id}.js: lists spouse "${s.id}", but ${s.id}.js does not list "${id}" back`);
    }
  }
}

// A shared child is proof of a couple, so both parents must record the marriage.
// This is what keeps the upward tree and the downward tree describing one family.
for (const [id, p] of Object.entries(people)) {
  if (!p.father || !p.mother || !people[p.father] || !people[p.mother]) continue;
  for (const [a, b] of [[p.father, p.mother], [p.mother, p.father]]) {
    if (!(people[a].spouses || []).some(s => s.id === b)) {
      fail(`${a}.js: has a child (${id}) with "${b}" but does not list them as a spouse`);
    }
  }
}
for (const start of Object.keys(people)) {
  const seen = new Set();
  const walk = id => {
    if (!id || seen.has(id) || !people[id]) return;
    if (id === start && seen.size) return fail(`${start}.js: parent chain loops back to itself`);
    seen.add(id);
    walk(people[id].father);
    walk(people[id].mother);
  };
  walk(people[start].father);
  walk(people[start].mother);
}

// Config files only reference people who exist.
if (!people[meta.root]) fail(`meta.js: root "${meta.root}" does not exist`);
function lineageChain(l) {
  if (l.chain) return l.chain;
  const out = [];
  const seen = new Set();
  let id = l.head;
  while (id && people[id] && !seen.has(id)) { seen.add(id); out.push(id); id = people[id].father; }
  return out.reverse();
}
for (const l of lineages) {
  if (l.head && !people[l.head]) fail(`lineages.js (${l.key}): head "${l.head}" does not exist`);
  for (const id of lineageChain(l)) if (!people[id]) fail(`lineages.js (${l.key}): "${id}" does not exist`);
}
for (const g of groups) {
  for (const id of g.people) if (!people[id]) fail(`groups.js (${g.title}): "${id}" does not exist`);
}

// Not fatal, but usually a mistake: a record connected to nothing. The index no
// longer depends on a hand-kept list, so "missing from a view" is not the concern
// any more — a person who touches no one else is. Marriage counts as a connection,
// which is how a spouse with no children still belongs.
//
// `meta.roots` is the forest case: several unconnected families, each with its own
// starting point. A tree with one root is just the one-element list.
const roots = (meta.roots && meta.roots.length ? meta.roots : [meta.root]).filter(id => people[id]);
if (meta.roots) {
  for (const r of meta.roots) if (!people[r]) fail(`meta.js: roots entry "${r}" does not exist`);
}

const neighbours = id => {
  const p = people[id];
  const out = [p.father, p.mother];
  for (const s of p.spouses || []) if (s.id) out.push(s.id);
  for (const [other, q] of Object.entries(people)) if (q.father === id || q.mother === id) out.push(other);
  return out.filter(x => x && people[x]);
};

const reachable = new Set(roots);
const queue = [...roots];
for (let i = 0; i < queue.length; i++) {
  for (const n of neighbours(queue[i])) {
    if (!reachable.has(n)) {
      reachable.add(n);
      queue.push(n);
    }
  }
}
for (const id of ids) {
  if (reachable.has(id)) continue;
  const isolated = neighbours(id).length === 0;
  warnings.push(
    isolated
      ? `${id}.js: connected to nobody — no parents, children or spouse`
      : `${id}.js: not connected to any root in meta.js (add a root, or link them in)`
  );
}

for (const w of warnings) console.warn('warn  ' + w);
for (const e of errors) console.error('error ' + e);
console.log(
  errors.length
    ? `\n${errors.length} error(s) in ${ids.length} people.`
    : `OK — ${ids.length} people, ${Object.keys(branches).length} branches, ${lineages.length} lineages, ${groups.length} index groups.`
);
process.exit(errors.length ? 1 : 0);
