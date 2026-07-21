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
  'id', 'name', 'dates', 'confidence', 'role', 'branch',
  'father', 'mother', 'spouse', 'source', 'note',
]);
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
  if (p.spouse && !p.spouse.name) fail(`${id}.js: spouse has no "name"`);
  for (const k of Object.keys(p)) if (!FIELDS.has(k)) warnings.push(`${id}.js: unknown field "${k}"`);
}

// Parent links point at people who exist, and nobody is their own ancestor.
for (const [id, p] of Object.entries(people)) {
  for (const rel of ['father', 'mother']) {
    if (p[rel] && !people[p[rel]]) fail(`${id}.js: ${rel} "${p[rel]}" does not exist`);
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
for (const l of lineages) {
  for (const id of l.chain) if (!people[id]) fail(`lineages.js (${l.key}): "${id}" does not exist`);
}
for (const g of groups) {
  for (const id of g.people) if (!people[id]) fail(`groups.js (${g.title}): "${id}" does not exist`);
}

// Not fatal, but usually a mistake: someone unreachable from every view.
const listed = new Set([...groups.flatMap(g => g.people), ...lineages.flatMap(l => l.chain)]);
const reachable = new Set([meta.root]);
const queue = [meta.root];
for (let i = 0; i < queue.length; i++) {
  for (const [id, p] of Object.entries(people)) {
    if ((p.father === queue[i] || p.mother === queue[i] || [p.father, p.mother].includes(queue[i])) && !reachable.has(id)) {
      reachable.add(id);
      queue.push(id);
    }
  }
  const p = people[queue[i]];
  for (const parent of [p.father, p.mother]) {
    if (parent && people[parent] && !reachable.has(parent)) {
      reachable.add(parent);
      queue.push(parent);
    }
  }
}
for (const id of ids) {
  if (!reachable.has(id) && !listed.has(id)) warnings.push(`${id}.js: not linked to anyone and not listed in any view`);
}

for (const w of warnings) console.warn('warn  ' + w);
for (const e of errors) console.error('error ' + e);
console.log(
  errors.length
    ? `\n${errors.length} error(s) in ${ids.length} people.`
    : `OK — ${ids.length} people, ${Object.keys(branches).length} branches, ${lineages.length} lineages, ${groups.length} index groups.`
);
process.exit(errors.length ? 1 : 0);
