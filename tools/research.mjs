#!/usr/bin/env node
// The research log: what was searched, where, and what came back.
//
// Two levels throughout, because they answer different questions. A SITE is a base
// venue — Geneanet, AGATHA, FamilySearch. A PAGE is something specific inside it: a
// member tree, a collection, a single act. "Have we tried Geneanet for this person?"
// and "which pages have ever yielded anything?" are different questions, and a flat
// list answers neither well.
//
// Every search records whether it succeeded, what it found, and — when it found
// nothing — why. The why is the part a strategist needs: "not indexed here" and
// "wrong region" and "hit the paywall" point at completely different next moves.
//
//   node tools/research.mjs tried edouard_dk     what has been tried, and how it went
//   node tools/research.mjs untried edouard_dk   sites and pages not yet used on them
//   node tools/research.mjs sources              the registry, sites then pages
//   node tools/research.mjs yield                which sites and pages actually pay off
//   node tools/research.mjs report               where the effort has gone
//   node tools/research.mjs log …                record a search
//   node tools/research.mjs check                validate log + registry
//   node tools/research.mjs docs                 regenerate docs/sources.md
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { loadPeople as readPeople } from './lib/people.mjs';

const ROOT = path.join(path.dirname(fileURLToPath(import.meta.url)), '..');
const SOURCES = path.join(ROOT, 'research', 'sources.json');
const LOG = path.join(ROOT, 'research', 'searches.jsonl');

// Success and failure, and the two states in between that a strategist must not
// confuse. `ambiguous` is a real find that is not proof — do not graft it, but do
// not search for it again either. `blocked` never reached the material at all, so
// it is the one result that means "try this again".
const RESULTS = {
  hit: 'found what was wanted',
  miss: 'searched properly, nothing there',
  ambiguous: 'found something, not enough to prove it',
  blocked: 'never reached the material — login, paywall, cap',
};
const SUCCEEDED = r => r === 'hit';

export function loadSources() {
  const raw = JSON.parse(fs.readFileSync(SOURCES, 'utf8'));
  return { sites: raw.sites || [], pages: raw.pages || [] };
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

export const loadPeople = () => readPeople();

const arg = name => {
  const i = process.argv.indexOf(`--${name}`);
  return i > -1 ? process.argv[i + 1] : undefined;
};
const nameOf = (people, id) => (people[id] ? people[id].name : id);

// ---------- commands ----------

function cmdLog() {
  const { sites, pages } = loadSources();
  const entry = {
    date: arg('date') || new Date().toISOString().slice(0, 10),
    person: arg('person'),
    goal: arg('goal'),
    site: arg('site'),
    page: arg('page') || null,
    query: arg('query'),
    result: arg('result'),
  };
  for (const k of ['person', 'goal', 'site', 'result']) {
    if (!entry[k]) throw new Error(`--${k} is required`);
  }
  if (!RESULTS[entry.result]) {
    throw new Error(`--result must be one of:\n` + Object.entries(RESULTS).map(([k, v]) => `  ${k.padEnd(10)} ${v}`).join('\n'));
  }
  if (!sites.some(s => s.id === entry.site)) {
    throw new Error(
      `unknown site "${entry.site}". Register it in research/sources.json first — ` +
        'a venue searched but never registered is one the next pass cannot know about.'
    );
  }
  if (entry.page) {
    const page = pages.find(p => p.id === entry.page);
    if (!page) throw new Error(`unknown page "${entry.page}". Register it under sites → "${entry.site}" first.`);
    if (page.site !== entry.site) throw new Error(`page "${entry.page}" belongs to site "${page.site}", not "${entry.site}"`);
  }
  const people = loadPeople();
  if (!people[entry.person]) throw new Error(`unknown person "${entry.person}"`);

  for (const optional of ['found', 'why', 'url', 'artifact', 'note']) {
    const v = arg(optional);
    if (v) entry[optional] = v;
  }
  if (SUCCEEDED(entry.result) && !entry.found) throw new Error('a hit needs --found: say what it actually gave you');
  if (!SUCCEEDED(entry.result) && !entry.why) throw new Error(`a ${entry.result} needs --why: the next pass has to know whether to try again`);

  fs.mkdirSync(path.dirname(LOG), { recursive: true });
  fs.appendFileSync(LOG, JSON.stringify(entry) + '\n');
  console.log(`logged: ${entry.person} · ${entry.site}${entry.page ? '/' + entry.page : ''} · ${entry.goal} → ${entry.result}`);
}

const MARK = { hit: '✓', miss: '✗', ambiguous: '~', blocked: '⊘' };

function cmdTried() {
  const person = process.argv[3];
  if (!person) throw new Error('usage: research.mjs tried <person-id>');
  const rows = loadLog().filter(e => e.person === person);
  const people = loadPeople();
  if (!rows.length) return console.log(`Nothing logged for ${nameOf(people, person)} yet — everything is untried.`);

  console.log(`${nameOf(people, person)} — ${rows.length} search(es)\n`);
  for (const e of rows) {
    const where = e.page ? `${e.site}/${e.page}` : e.site;
    console.log(`  ${MARK[e.result]} ${e.result.toUpperCase().padEnd(10)} ${where.padEnd(30)} goal: ${e.goal}   (${e.date})`);
    if (e.query) console.log(`      searched: ${e.query}`);
    if (e.found) console.log(`      FOUND:    ${e.found}`);
    if (e.why) console.log(`      WHY NOT:  ${e.why}`);
    console.log('');
  }

  const dead = [...new Set(rows.filter(e => e.result === 'miss').map(e => (e.page ? `${e.site}/${e.page}` : e.site)))];
  const retry = [...new Set(rows.filter(e => e.result === 'blocked').map(e => e.site))];
  if (dead.length) console.log(`  Searched and empty — do not repeat without a new angle:\n    ${dead.join(', ')}`);
  if (retry.length) console.log(`  Never actually reached — WORTH RETRYING:\n    ${retry.join(', ')}`);
}

function cmdUntried() {
  const person = process.argv[3];
  if (!person) throw new Error('usage: research.mjs untried <person-id>');
  const { sites, pages } = loadSources();
  const rows = loadLog().filter(e => e.person === person);
  const usedSites = new Set(rows.map(e => e.site));
  const usedPages = new Set(rows.map(e => e.page).filter(Boolean));

  const freshSites = sites.filter(s => !usedSites.has(s.id));
  console.log(`Sites never searched for ${person} (${freshSites.length}):\n`);
  for (const s of freshSites) console.log(`  ${s.id.padEnd(24)} ${(s.access || '-').padEnd(8)} ${s.title}`);

  const freshPages = pages.filter(p => !usedPages.has(p.id) && p.kind !== 'record');
  console.log(`\nPages never opened for them (${freshPages.length}) — those with a track record first:\n`);
  const scored = freshPages.sort((a, b) => (b.yielded ? 1 : 0) - (a.yielded ? 1 : 0));
  for (const p of scored) {
    console.log(`  ${p.id.padEnd(24)} ${p.site.padEnd(14)} ${p.yielded ? 'has yielded before' : '—'.padEnd(18)} ${p.covers || ''}`);
  }
}

function cmdSources() {
  const { sites, pages } = loadSources();
  console.log(`SITES (${sites.length}) — base venues\n`);
  for (const s of sites) {
    console.log(`  ${s.id.padEnd(24)} ${(s.access || '-').padEnd(8)} ${s.kind.padEnd(9)} ${s.title}`);
  }
  console.log(`\nPAGES (${pages.length}) — specific trees, collections and documents\n`);
  const bySite = {};
  for (const p of pages) (bySite[p.site] = bySite[p.site] || []).push(p);
  for (const [site, list] of Object.entries(bySite)) {
    console.log(`  ${site}`);
    for (const p of list) console.log(`    ${p.id.padEnd(30)} ${p.kind.padEnd(11)} ${p.yielded ? '✓ yielded' : '·'}  ${p.title}`);
  }
}

// Which venues actually pay off — the question a strategist asks before choosing.
function cmdYield() {
  const log = loadLog();
  const { sites, pages } = loadSources();
  const tally = key => {
    const t = {};
    for (const e of log) {
      const k = key(e);
      if (!k) continue;
      t[k] = t[k] || { hit: 0, miss: 0, ambiguous: 0, blocked: 0, total: 0 };
      t[k][e.result]++;
      t[k].total++;
    }
    return t;
  };

  console.log('BY SITE — searches run, and how they went\n');
  console.log(`  ${'site'.padEnd(24)} ${'run'.padStart(3)}  ${'hit'.padStart(3)} ${'miss'.padStart(4)} ${'amb'.padStart(3)} ${'blk'.padStart(3)}`);
  const bySite = tally(e => e.site);
  for (const [id, t] of Object.entries(bySite).sort((a, b) => b[1].hit - a[1].hit || b[1].total - a[1].total)) {
    console.log(`  ${id.padEnd(24)} ${String(t.total).padStart(3)}  ${String(t.hit).padStart(3)} ${String(t.miss).padStart(4)} ${String(t.ambiguous).padStart(3)} ${String(t.blocked).padStart(3)}`);
  }

  console.log('\nPAGES THAT HAVE YIELDED\n');
  for (const p of pages.filter(p => p.yielded)) {
    console.log(`  ${p.id} (${p.site})`);
    console.log(`    ${p.yielded}`);
  }

  const untouchedSites = sites.filter(s => !bySite[s.id]);
  if (untouchedSites.length) {
    console.log(`\nSITES NEVER SEARCHED AT ALL (${untouchedSites.length}) — the untapped list:\n`);
    for (const s of untouchedSites) console.log(`  ${s.id.padEnd(24)} ${(s.access || '-').padEnd(8)} ${s.title}`);
  }
  const openPages = pages.filter(p => !p.yielded && p.kind !== 'record');
  if (openPages.length) {
    console.log(`\nPAGES REGISTERED BUT NOT YET PRODUCTIVE (${openPages.length}):\n`);
    for (const p of openPages) console.log(`  ${p.id.padEnd(30)} ${p.site.padEnd(14)} ${p.covers || ''}`);
  }
}

function cmdReport() {
  const log = loadLog();
  const people = loadPeople();
  if (!log.length) return console.log('The search log is empty.');

  const byResult = {};
  for (const e of log) byResult[e.result] = (byResult[e.result] || 0) + 1;
  console.log(`${log.length} searches logged\n`);
  for (const [r, desc] of Object.entries(RESULTS)) {
    console.log(`  ${MARK[r]} ${r.padEnd(10)} ${String(byResult[r] || 0).padStart(3)}   ${desc}`);
  }

  const perPerson = {};
  for (const e of log) (perPerson[e.person] = perPerson[e.person] || []).push(e);
  console.log('\nEffort per person — no hits after several tries means change the angle:\n');
  Object.entries(perPerson)
    .sort((a, b) => b[1].length - a[1].length)
    .forEach(([id, rows]) => {
      const hits = rows.filter(r => SUCCEEDED(r.result)).length;
      const blocked = rows.filter(r => r.result === 'blocked').length;
      console.log(
        `  ${nameOf(people, id).padEnd(32)} ${String(rows.length).padStart(2)} searched · ${hits} hit` +
          (blocked ? ` · ${blocked} still blocked` : '') +
          (!hits && rows.length >= 3 ? '   ← stuck' : '')
      );
    });
}

export function check() {
  const problems = [];
  const { sites, pages } = loadSources();
  const siteIds = new Set();
  for (const s of sites) {
    if (!s.id) problems.push('a site has no id');
    else if (siteIds.has(s.id)) problems.push(`duplicate site id "${s.id}"`);
    siteIds.add(s.id);
    if (!s.title) problems.push(`site "${s.id}" has no title`);
  }
  const pageIds = new Set();
  for (const p of pages) {
    if (!p.id) problems.push('a page has no id');
    else if (pageIds.has(p.id) || siteIds.has(p.id)) problems.push(`duplicate id "${p.id}"`);
    pageIds.add(p.id);
    if (!p.title) problems.push(`page "${p.id}" has no title`);
    if (!p.site) problems.push(`page "${p.id}" names no site`);
    else if (!siteIds.has(p.site)) problems.push(`page "${p.id}" belongs to site "${p.site}", which is not registered`);
    if (p.artifact && !fs.existsSync(path.join(ROOT, p.artifact))) {
      problems.push(`page "${p.id}" points at a missing artifact: ${p.artifact}`);
    }
  }

  const people = loadPeople();
  loadLog().forEach((e, i) => {
    const at = `searches.jsonl line ${i + 1}`;
    for (const field of ['date', 'person', 'goal', 'site', 'result']) {
      if (!e[field]) problems.push(`${at}: missing "${field}"`);
    }
    if (e.result && !RESULTS[e.result]) problems.push(`${at}: result "${e.result}" is not one of ${Object.keys(RESULTS).join(', ')}`);
    if (e.site && !siteIds.has(e.site)) problems.push(`${at}: unknown site "${e.site}"`);
    if (e.page) {
      const page = pages.find(p => p.id === e.page);
      if (!page) problems.push(`${at}: unknown page "${e.page}"`);
      else if (page.site !== e.site) problems.push(`${at}: page "${e.page}" belongs to site "${page.site}", not "${e.site}"`);
    }
    if (e.person && !people[e.person]) problems.push(`${at}: unknown person "${e.person}"`);
    if (e.artifact && !fs.existsSync(path.join(ROOT, e.artifact))) problems.push(`${at}: missing artifact ${e.artifact}`);
    // The outcome has to be legible, or the entry tells the next pass nothing.
    if (e.result && SUCCEEDED(e.result) && !e.found) problems.push(`${at}: a hit with no "found" — say what it gave`);
    if (e.result && !SUCCEEDED(e.result) && !e.why) problems.push(`${at}: a ${e.result} with no "why" — say whether it is worth retrying`);
  });
  return problems;
}

function cmdDocs() {
  const { sites, pages } = loadSources();
  const log = loadLog();
  const searchesPerSite = {};
  for (const e of log) searchesPerSite[e.site] = (searchesPerSite[e.site] || 0) + 1;

  const out = [
    '# Sources',
    '',
    '<!-- GENERATED from research/sources.json by tools/research.mjs docs — do not edit. -->',
    '',
    'Two levels: **sites** are the base venues, **pages** are the specific trees,',
    'collections and documents inside them that were actually opened. The search log that',
    'references both is `research/searches.jsonl` — see [searching.md](searching.md).',
    '',
    'Confidence: **doc** = seen in a primary act or an authoritative index · **sup** = a',
    'single member tree, not checked against the act · **fam** = family testimony.',
    '',
    '## Sites',
    '',
    '| Site | Kind | Access | Searches run | Covers |',
    '|---|---|---|---|---|',
  ];
  for (const s of sites) {
    const covers = (s.covers || '').replace(/\|/g, '\\|');
    out.push(`| \`${s.id}\`${s.url ? ` <${s.url}>` : ''} | ${s.kind} | ${s.access || '—'} | ${searchesPerSite[s.id] || 0} | ${covers} |`);
  }
  out.push('');
  for (const s of sites.filter(s => s.note)) out.push(`**\`${s.id}\`** — ${s.note}`, '');

  out.push('## Pages', '');
  const bySite = {};
  for (const p of pages) (bySite[p.site] = bySite[p.site] || []).push(p);
  for (const site of sites) {
    const list = bySite[site.id];
    if (!list) continue;
    out.push(`### ${site.title}`, '');
    for (const p of list) {
      out.push(`#### \`${p.id}\` — ${p.title}`);
      out.push(`- **Kind:** ${p.kind}${p.url ? ` · <${p.url}>` : ''}`);
      if (p.collection) out.push(`- **Collection:** ${p.collection}`);
      if (p.covers) out.push(`- **Covers:** ${p.covers}`);
      out.push(`- **Yielded:** ${p.yielded || '*nothing yet*'}`);
      if (p.artifact) out.push(`- **Local copy:** \`${p.artifact}\``);
      if (p.image) out.push(`- **Image:** <${p.image}>`);
      if (p.confidence) out.push(`- **Confidence:** ${p.confidence}`);
      if (p.accessed) out.push(`- **Accessed:** ${p.accessed}`);
      if (p.note) out.push(`- **Note:** ${p.note}`);
      out.push('');
    }
  }
  fs.writeFileSync(path.join(ROOT, 'docs', 'sources.md'), out.join('\n'));
  console.log(`docs/sources.md regenerated — ${sites.length} sites, ${pages.length} pages.`);
}

const COMMANDS = {
  log: cmdLog,
  tried: cmdTried,
  untried: cmdUntried,
  sources: cmdSources,
  yield: cmdYield,
  report: cmdReport,
  docs: cmdDocs,
  check: () => {
    const problems = check();
    for (const p of problems) console.error('error ' + p);
    const { sites, pages } = loadSources();
    console.log(problems.length ? `\n${problems.length} problem(s).` : `OK — ${sites.length} sites, ${pages.length} pages, ${loadLog().length} searches logged.`);
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
