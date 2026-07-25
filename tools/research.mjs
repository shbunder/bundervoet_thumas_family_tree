#!/usr/bin/env node
// The research log: what was searched, where, and what came back.
//
// The point is the misses. A pass that records only its finds leaves the next
// pass to re-walk every dead end, and an unattended loop will do exactly that,
// forever. "AGATHA is exhausted for Édouard's parentage" is a finding, and this
// is where it goes so that it can be queried instead of re-derived.
//
//   node tools/research.mjs log --person edouard_dk --source agatha \
//        --goal parents --result miss --query "de Keyser Eduardus 1876" \
//        --note "191 hits, none born 1876"
//   node tools/research.mjs tried edouard_dk     what has been tried for them
//   node tools/research.mjs untried edouard_dk   what has not
//   node tools/research.mjs sources              the registry
//   node tools/research.mjs report               where the effort has gone
//   node tools/research.mjs check                validate log + registry
//   node tools/research.mjs docs                 regenerate docs/sources.md
import fs from 'node:fs';
import path from 'node:path';
import vm from 'node:vm';
import { fileURLToPath } from 'node:url';

const ROOT = path.join(path.dirname(fileURLToPath(import.meta.url)), '..');
const SOURCES = path.join(ROOT, 'research', 'sources.json');
const LOG = path.join(ROOT, 'research', 'searches.jsonl');

const RESULTS = new Set(['hit', 'miss', 'ambiguous', 'blocked']);

export function loadSources() {
  return JSON.parse(fs.readFileSync(SOURCES, 'utf8')).sources;
}

export function loadLog() {
  if (!fs.existsSync(LOG)) return [];
  return fs
    .readFileSync(LOG, 'utf8')
    .split('\n')
    .map(l => l.trim())
    .filter(Boolean)
    .map((line, i) => {
      try {
        return JSON.parse(line);
      } catch (e) {
        throw new Error(`research/searches.jsonl line ${i + 1} is not valid JSON: ${e.message}`);
      }
    });
}

// People are read the same way the validator reads them, so ids can be checked.
export function loadPeople() {
  let captured;
  const rec = v => (captured = v);
  const ctx = vm.createContext({
    FamilyTree: { person: rec, roster: rec, meta: rec, branches: rec, lineages: rec, groups: rec },
  });
  const read = f => {
    captured = undefined;
    vm.runInContext(fs.readFileSync(path.join(ROOT, 'data', f), 'utf8'), ctx, { filename: f });
    return captured;
  };
  const ids = read('people.js');
  const people = {};
  for (const id of ids) people[id] = read(`people/${id}.js`);
  return people;
}

const arg = name => {
  const i = process.argv.indexOf(`--${name}`);
  return i > -1 ? process.argv[i + 1] : undefined;
};

// ---------- commands ----------

function cmdLog() {
  const entry = {
    date: arg('date') || new Date().toISOString().slice(0, 10),
    person: arg('person'),
    goal: arg('goal'),
    source: arg('source'),
    query: arg('query'),
    result: arg('result'),
  };
  for (const [k, v] of Object.entries({ person: entry.person, goal: entry.goal, source: entry.source, result: entry.result })) {
    if (!v) throw new Error(`--${k} is required`);
  }
  if (!RESULTS.has(entry.result)) throw new Error(`--result must be one of: ${[...RESULTS].join(', ')}`);

  const sources = loadSources();
  if (!sources.some(s => s.id === entry.source)) {
    throw new Error(
      `unknown source "${entry.source}". Register it in research/sources.json first — ` +
        'a venue that gets searched but never registered is one the next pass cannot know about.'
    );
  }
  const people = loadPeople();
  if (!people[entry.person]) throw new Error(`unknown person "${entry.person}"`);

  for (const optional of ['url', 'artifact', 'note']) {
    const v = arg(optional);
    if (v) entry[optional] = v;
  }

  fs.mkdirSync(path.dirname(LOG), { recursive: true });
  fs.appendFileSync(LOG, JSON.stringify(entry) + '\n');
  console.log(`logged: ${entry.person} · ${entry.source} · ${entry.goal} → ${entry.result}`);
}

function cmdTried() {
  const person = process.argv[3];
  if (!person) throw new Error('usage: research.mjs tried <person-id>');
  const rows = loadLog().filter(e => e.person === person);
  if (!rows.length) return console.log(`Nothing logged for ${person} yet.`);
  const people = loadPeople();
  console.log(`${people[person] ? people[person].name : person} — ${rows.length} search(es)\n`);
  for (const e of rows) {
    console.log(`  ${e.date}  ${e.result.toUpperCase().padEnd(9)} ${e.source.padEnd(22)} ${e.goal}`);
    if (e.query) console.log(`             query: ${e.query}`);
    if (e.note) console.log(`             ${e.note}`);
  }
  const exhausted = rows.filter(e => e.result === 'miss').map(e => e.source);
  if (exhausted.length) console.log(`\n  Already come back empty: ${[...new Set(exhausted)].join(', ')} — do not repeat without a new angle.`);
}

function cmdUntried() {
  const person = process.argv[3];
  if (!person) throw new Error('usage: research.mjs untried <person-id>');
  const used = new Set(loadLog().filter(e => e.person === person).map(e => e.source));
  const rest = loadSources().filter(s => !used.has(s.id) && s.kind !== 'record' && s.kind !== 'family');
  console.log(`Not yet searched for ${person} (${rest.length}):\n`);
  for (const s of rest) console.log(`  ${s.id.padEnd(24)} ${s.access.padEnd(8)} ${s.title}`);
}

function cmdSources() {
  const byKind = {};
  for (const s of loadSources()) (byKind[s.kind] = byKind[s.kind] || []).push(s);
  for (const [kind, list] of Object.entries(byKind)) {
    console.log(`\n${kind} (${list.length})`);
    for (const s of list) console.log(`  ${s.id.padEnd(24)} ${(s.access || '-').padEnd(8)} ${s.title}`);
  }
}

function cmdReport() {
  const log = loadLog();
  const people = loadPeople();
  if (!log.length) return console.log('The search log is empty.');

  const byResult = {};
  for (const e of log) byResult[e.result] = (byResult[e.result] || 0) + 1;
  console.log(`${log.length} searches logged: ` + Object.entries(byResult).map(([k, v]) => `${v} ${k}`).join(', '));

  const perPerson = {};
  for (const e of log) (perPerson[e.person] = perPerson[e.person] || []).push(e);
  console.log('\nMost-searched people:');
  Object.entries(perPerson)
    .sort((a, b) => b[1].length - a[1].length)
    .slice(0, 12)
    .forEach(([id, rows]) => {
      const hits = rows.filter(r => r.result === 'hit').length;
      console.log(`  ${(people[id] ? people[id].name : id).padEnd(34)} ${String(rows.length).padStart(3)} searches, ${hits} hit(s)`);
    });

  const used = new Set(log.map(e => e.source));
  const unused = loadSources().filter(s => !used.has(s.id) && s.kind !== 'record' && s.kind !== 'family');
  if (unused.length) {
    console.log(`\nRegistered but never searched (${unused.length}) — untapped:`);
    for (const s of unused) console.log(`  ${s.id.padEnd(24)} ${s.title}`);
  }
}

// Validates the log and the registry against each other and against the people.
export function check() {
  const problems = [];
  const sources = loadSources();
  const ids = new Set();
  for (const s of sources) {
    if (!s.id) problems.push('a source has no id');
    else if (ids.has(s.id)) problems.push(`duplicate source id "${s.id}"`);
    ids.add(s.id);
    if (!s.title) problems.push(`source "${s.id}" has no title`);
    if (s.via && !sources.some(o => o.id === s.via)) problems.push(`source "${s.id}" cites via "${s.via}", which is not registered`);
    if (s.artifact && !fs.existsSync(path.join(ROOT, s.artifact))) {
      problems.push(`source "${s.id}" points at a missing artifact: ${s.artifact}`);
    }
  }
  const people = loadPeople();
  loadLog().forEach((e, i) => {
    const at = `searches.jsonl line ${i + 1}`;
    for (const field of ['date', 'person', 'goal', 'source', 'result']) {
      if (!e[field]) problems.push(`${at}: missing "${field}"`);
    }
    if (e.result && !RESULTS.has(e.result)) problems.push(`${at}: result "${e.result}" is not one of ${[...RESULTS].join(', ')}`);
    if (e.source && !ids.has(e.source)) problems.push(`${at}: unknown source "${e.source}"`);
    if (e.person && !people[e.person]) problems.push(`${at}: unknown person "${e.person}"`);
    if (e.artifact && !fs.existsSync(path.join(ROOT, e.artifact))) problems.push(`${at}: missing artifact ${e.artifact}`);
  });
  return problems;
}

// docs/sources.md is the readable view of the registry, regenerated from it so
// the two cannot drift apart.
function cmdDocs() {
  const sources = loadSources();
  const KINDS = [
    ['record', 'Documents cited'],
    ['family', 'Family testimony'],
    ['archive', 'Archives'],
    ['index', 'Record indexes'],
    ['tree', 'Member trees'],
    ['obituary', 'Obituaries & memorial cards'],
    ['cemetery', 'Cemetery indexes'],
  ];
  const out = [
    '# Sources',
    '',
    '<!-- GENERATED from research/sources.json by tools/research.mjs docs — do not edit. -->',
    '',
    'Everywhere this project can look, and every document it has cited. The machine-readable',
    'original is `research/sources.json`; the search log that references it is',
    '`research/searches.jsonl`.',
    '',
    'Confidence: **doc** = seen in a primary act or an authoritative index · **sup** = a single',
    'member tree, not yet checked against the act · **fam** = family testimony.',
    '',
  ];
  for (const [kind, heading] of KINDS) {
    const list = sources.filter(s => s.kind === kind);
    if (!list.length) continue;
    out.push(`## ${heading}`, '');
    for (const s of list) {
      out.push(`### \`${s.id}\` — ${s.title}`);
      if (s.url) out.push(`- **URL:** <${s.url}>`);
      if (s.image) out.push(`- **Image:** <${s.image}>`);
      if (s.collection) out.push(`- **Collection:** ${s.collection}`);
      if (s.via) out.push(`- **Via:** \`${s.via}\``);
      if (s.covers) out.push(`- **Covers:** ${s.covers}`);
      if (s.proves) out.push(`- **Proves:** ${s.proves}`);
      if (s.artifact) out.push(`- **Local copy:** \`${s.artifact}\``);
      if (s.access) out.push(`- **Access:** ${s.access}`);
      if (s.confidence) out.push(`- **Confidence:** ${s.confidence}`);
      if (s.accessed) out.push(`- **Accessed:** ${s.accessed}`);
      if (s.note) out.push(`- **Note:** ${s.note}`);
      out.push('');
    }
  }
  fs.writeFileSync(path.join(ROOT, 'docs', 'sources.md'), out.join('\n'));
  console.log(`docs/sources.md regenerated — ${sources.length} sources.`);
}

// ---------- dispatch ----------
const COMMANDS = {
  log: cmdLog,
  tried: cmdTried,
  untried: cmdUntried,
  sources: cmdSources,
  report: cmdReport,
  docs: cmdDocs,
  check: () => {
    const problems = check();
    for (const p of problems) console.error('error ' + p);
    console.log(problems.length ? `\n${problems.length} problem(s).` : `OK — ${loadSources().length} sources, ${loadLog().length} searches logged.`);
    if (problems.length) process.exit(1);
  },
};

if (process.argv[1] && path.resolve(process.argv[1]) === path.resolve(fileURLToPath(import.meta.url))) {
  const cmd = COMMANDS[process.argv[2]];
  if (!cmd) {
    console.error(`usage: research.mjs <${Object.keys(COMMANDS).join('|')}>`);
    process.exit(1);
  }
  try {
    cmd();
  } catch (e) {
    console.error('error ' + e.message);
    process.exit(1);
  }
}
