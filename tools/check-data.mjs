#!/usr/bin/env node
// Checks the data files hang together. Run with: node tools/check-data.mjs
import fs from 'node:fs';
import path from 'node:path';
import { buildBundle } from './build.mjs';
import { loadSources } from './research.mjs';
import { createHash } from 'node:crypto';
import {
  DATA, ARTIFACTS_DIR, ARTIFACT_FIELDS, FIELDS, EVENT_FIELDS, SPOUSE_FIELDS,
  isValidDate, loadArtifacts, loadConfig, loadPerson, onDisk,
} from './lib/people.mjs';

// The build runs this validator first, so it passes --skip-generated to avoid
// being told the files it is about to write are out of date.
const SKIP_GENERATED = process.argv.includes('--skip-generated');

const errors = [];
const warnings = [];
const fail = m => errors.push(m);

const { roster: ids, meta, root, branches, lineages, groups } = loadConfig();
const GROUP_KEYS = new Set(groups.map(g => g.key));
const { sites, pages } = loadSources();
const SOURCE_IDS = new Set([...sites, ...pages].map(s => s.id));
const CONFIDENCE = new Set(meta.confidence);

// The roster IS the directory now, so there is no manifest to disagree with it.
const files = ids;

const people = {};
for (const id of ids.filter(i => files.includes(i))) {
  let p;
  try {
    p = loadPerson(id);
  } catch (e) {
    fail(e.message);
    continue;
  }
  people[id] = p;

  if (p.id !== id) fail(`${id}.md: "id" field says "${p.id}"`);
  if (!p.name) fail(`${id}.md: missing "name"`);
  // The surname is stated because it cannot be computed, so the one thing worth
  // checking is that it is really part of the name — a typo here would split a
  // family in two without anything else noticing.
  if (p.surname && !p.name.includes(p.surname)) {
    fail(`${id}.md: surname "${p.surname}" does not appear in name "${p.name}"`);
  }
  if (!CONFIDENCE.has(p.confidence)) fail(`${id}.md: confidence "${p.confidence}" is not one of ${[...CONFIDENCE].join(', ')}`);
  if (p.branch && !(p.branch in branches)) fail(`${id}.md: branch "${p.branch}" is not in data/branches.json`);
  if (p.line && !GROUP_KEYS.has(p.line)) fail(`${id}.md: line "${p.line}" is not a group key in site/labels.json`);
  if ('sex' in p && p.sex !== 'f' && p.sex !== 'm') fail(`${id}.md: sex "${p.sex}" must be "f" or "m"`);

  // A date is either in the grammar or explicitly marked raw. There is no third
  // option, because a half-parsed date is one that later gets read as a fact.
  for (const ev of ['birth', 'death']) {
    const e = p[ev];
    if (!e) continue;
    if (typeof e !== 'object' || Array.isArray(e)) { fail(`${id}.md: "${ev}" must be a block with date/place`); continue; }
    for (const k of Object.keys(e)) {
      if (!EVENT_FIELDS.includes(k) && k !== 'raw') warnings.push(`${id}.md: ${ev} has unknown field "${k}"`);
    }
    if (e.date && !isValidDate(e.date)) {
      fail(`${id}.md: ${ev}.date "${e.date}" is not a valid date — use 1876-11-12, 1876-11, 1876, ~1682, <1727, >1900 or 1575..1587`);
    }
    if (!e.date && !e.raw) fail(`${id}.md: "${ev}" has neither a date nor a raw value`);
  }

  // A citation is a link into research/sources.json, so a typo is caught here
  // rather than becoming a claim backed by a source that does not exist.
  if ('sources' in p) {
    const list = Array.isArray(p.sources) ? p.sources.map(x => (typeof x === 'string' ? x : x.id)) : [p.sources];
    for (const sid of list) if (!SOURCE_IDS.has(sid)) fail(`${id}.md: cites source "${sid}", which is not in research/sources.json`);
  }
  if ('spouses' in p) {
    if (!Array.isArray(p.spouses)) fail(`${id}.md: "spouses" must be a list`);
    else for (const [i, s] of p.spouses.entries()) {
      if (!s.name) fail(`${id}.md: spouses[${i}] has no "name"`);
      for (const k of Object.keys(s)) if (!SPOUSE_FIELDS.includes(k)) warnings.push(`${id}.md: spouses[${i}] unknown field "${k}"`);
    }
  }
  for (const k of Object.keys(p)) if (!FIELDS.includes(k) && k !== 'note') warnings.push(`${id}.md: unknown field "${k}"`);
}

// Parent links point at people who exist, and nobody is their own ancestor.
for (const [id, p] of Object.entries(people)) {
  for (const rel of ['father', 'mother']) {
    if (p[rel] && !people[p[rel]]) fail(`${id}.md: ${rel} "${p[rel]}" does not exist`);
  }
}

// Spouse links point at people who exist, and marriage is mutual: if A records B,
// B records A. Without that, building the tree downwards silently loses branches —
// a child hangs off the parent who happened to be written up first.
for (const [id, p] of Object.entries(people)) {
  for (const s of p.spouses || []) {
    if (!s.id) continue;
    if (!people[s.id]) { fail(`${id}.md: spouse id "${s.id}" does not exist`); continue; }
    if (s.id === id) fail(`${id}.md: is listed as their own spouse`);
    if (!(people[s.id].spouses || []).some(t => t.id === id)) {
      fail(`${id}.md: lists spouse "${s.id}", but ${s.id}.md does not list "${id}" back`);
    }
  }
}

// A shared child is proof of a couple, so both parents must record the marriage.
// This is what keeps the upward tree and the downward tree describing one family.
for (const [id, p] of Object.entries(people)) {
  if (!p.father || !p.mother || !people[p.father] || !people[p.mother]) continue;
  for (const [a, b] of [[p.father, p.mother], [p.mother, p.father]]) {
    if (!(people[a].spouses || []).some(s => s.id === b)) {
      fail(`${a}.md: has a child (${id}) with "${b}" but does not list them as a spouse`);
    }
  }
}

for (const start of Object.keys(people)) {
  const seen = new Set();
  const walk = id => {
    if (!id || seen.has(id) || !people[id]) return;
    if (id === start && seen.size) return fail(`${start}.md: parent chain loops back to itself`);
    seen.add(id);
    walk(people[id].father);
    walk(people[id].mother);
  };
  walk(people[start].father);
  walk(people[start].mother);
}

// Config files only reference people who exist.
if (!people[root]) fail(`meta.json: roots[0] "${root}" does not exist`);
function lineageChain(l) {
  if (l.chain) return l.chain;
  const out = [];
  const seen = new Set();
  let id = l.head;
  while (id && people[id] && !seen.has(id)) { seen.add(id); out.push(id); id = people[id].father; }
  return out.reverse();
}
for (const l of lineages) {
  if (l.head && !people[l.head]) fail(`lineages.json (${l.key}): head "${l.head}" does not exist`);
  for (const id of lineageChain(l)) if (!people[id]) fail(`lineages.json (${l.key}): "${id}" does not exist`);
}
for (const g of groups) {
  if (!g.key || !g.title) fail(`site/labels.json: every group needs a key and a title`);
}

// Not fatal, but usually a mistake: a record connected to nothing. Marriage counts
// as a connection, which is how a spouse with no children still belongs.
// `meta.roots` is the forest case: several unconnected families, each with its own
// starting point. A tree with one root is just the one-element list.
const roots = meta.roots.filter(id => people[id]);
for (const r of meta.roots) if (!people[r]) fail(`meta.json: roots entry "${r}" does not exist`);
for (const [b, sid] of Object.entries(branches)) {
  if (!SOURCE_IDS.has(sid)) fail(`branches.json: "${b}" cites source "${sid}", which is not registered`);
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
  if (reachable.has(id) || !people[id]) continue;
  warnings.push(
    neighbours(id).length === 0
      ? `${id}.md: connected to nobody — no parents, children or spouse`
      : `${id}.md: not connected to any root in meta.js (add a root, or link them in)`
  );
}

// Artifacts are the evidence itself. A record pointing at a file that is missing is
// a citation to nothing; a file whose bytes no longer match the recorded digest is
// worse, because the claim still looks sourced while the proof has changed under it.
const artifacts = loadArtifacts();
for (const [aid, a] of Object.entries(artifacts)) {
  if (a.id !== aid) fail(`artifacts/${aid}.md: "id" says "${a.id}"`);
  if (!a.title) fail(`artifacts/${aid}.md: missing "title"`);
  for (const k of Object.keys(a)) if (!ARTIFACT_FIELDS.includes(k) && k !== 'note') warnings.push(`artifacts/${aid}.md: unknown field "${k}"`);
  if (a.date && !isValidDate(a.date)) fail(`artifacts/${aid}.md: date "${a.date}" is not a valid date`);
  if (a.source && !SOURCE_IDS.has(a.source)) fail(`artifacts/${aid}.md: source "${a.source}" is not registered`);
  for (const pid of a.evidences || []) if (!people[pid]) fail(`artifacts/${aid}.md: evidences "${pid}", who does not exist`);

  if (!a.file) { fail(`artifacts/${aid}.md: missing "file"`); continue; }
  const file = path.join(ARTIFACTS_DIR, a.file);
  if (!fs.existsSync(file)) { fail(`artifacts/${aid}.md: file "${a.file}" is missing`); continue; }
  const bytes = fs.readFileSync(file);
  if (a.bytes && Number(a.bytes) !== bytes.length) fail(`artifacts/${aid}.md: file is ${bytes.length} bytes, the record says ${a.bytes}`);
  if (a.sha256 && createHash('sha256').update(bytes).digest('hex') !== a.sha256) {
    fail(`artifacts/${aid}.md: sha256 does not match the file — the evidence has changed`);
  }
}
for (const f of fs.existsSync(ARTIFACTS_DIR) ? fs.readdirSync(ARTIFACTS_DIR) : []) {
  if (!f.endsWith('.md') && !Object.values(artifacts).some(a => a.file === f)) {
    warnings.push(`artifacts/${f}: no record describes this file`);
  }
}

// The page loads dist/bundle.js, not the individual files, so a stale bundle is
// a site silently showing old data. Catching it here means it cannot be
// committed: the rule is that this validator is green before every commit.
if (!SKIP_GENERATED) {
  const bundlePath = path.join(DATA, '..', 'dist', 'bundle.js');
  if (!fs.existsSync(bundlePath)) {
    fail('dist/bundle.js is missing — run: node tools/build.mjs');
  } else if (fs.readFileSync(bundlePath, 'utf8') !== buildBundle()) {
    fail('dist/bundle.js is out of date with data/people/ — run: node tools/build.mjs');
  }
}

for (const w of warnings) console.warn('warn  ' + w);
for (const e of errors) console.error('error ' + e);
console.log(
  errors.length
    ? `\n${errors.length} error(s) in ${ids.length} people.`
    : `OK — ${ids.length} people, ${Object.keys(branches).length} branches, ${lineages.length} lineages, ${groups.length} index groups.`
);
process.exit(errors.length ? 1 : 0);
