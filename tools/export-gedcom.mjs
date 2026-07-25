#!/usr/bin/env node
// Exports the tree as GEDCOM 7 — the open interchange format every genealogy
// program reads. Run with: node tools/export-gedcom.mjs
//
// The .js person files stay the source of truth; this is a generated view of
// them, so it is regenerated rather than edited. What GEDCOM cannot carry
// faithfully is reported at the end rather than fudged into a field that would
// read as fact to whatever imports it.
//
// Deliberately GEDCOM 7 and not 5.5.1: v7 is UTF-8 throughout (these records are
// full of é and ë), has no line-length limit and no CONC continuation, so the
// long research notes survive intact.
import fs from 'node:fs';
import path from 'node:path';
import vm from 'node:vm';
import { fileURLToPath } from 'node:url';

const ROOT = path.join(path.dirname(fileURLToPath(import.meta.url)), '..');
const DATA = path.join(ROOT, 'data');
const OUT = path.join(ROOT, 'exports', 'family-tree.ged');

// ---------- load ----------
let captured;
const record = v => (captured = v);
const context = vm.createContext({
  FamilyTree: { person: record, roster: record, meta: record, branches: record, lineages: record, groups: record },
});
const read = file => {
  captured = undefined;
  vm.runInContext(fs.readFileSync(path.join(DATA, file), 'utf8'), context, { filename: file });
  return captured;
};

const ids = read('people.js');
const meta = read('meta.js');
const branches = read('branches.js');
const people = {};
for (const id of ids) people[id] = read(`people/${id}.js`);

const report = { unparsedDates: [], occupations: 0, notes: [] };

// ---------- names ----------
// Flemish and Walloon surnames carry particles — "Van den Broucke", "De Keyser" —
// so the surname is not simply the last word. The split starts at the first
// particle that has a given name before it.
const PARTICLES = new Set([
  'van', 'de', 'den', 'der', 'ter', 'ten', 'vande', 'vanden', 'vander',
  'del', 'di', 'le', 'la', 'du', 'des', 'op', 'uit', "d'", 'dela',
]);

function splitName(name) {
  // Placeholders like "Roland's sister (name unknown)" are not names; leave them
  // whole rather than inventing a surname out of "unknown)".
  if (/unknown|\bNN\b|\(/.test(name)) return null;
  const parts = name.split(/\s+/);
  if (parts.length < 2) return null;
  for (let i = 1; i < parts.length; i++) {
    if (PARTICLES.has(parts[i].toLowerCase())) {
      return { given: parts.slice(0, i).join(' '), surname: parts.slice(i).join(' ') };
    }
  }
  return { given: parts.slice(0, -1).join(' '), surname: parts[parts.length - 1] };
}

// ---------- dates & places ----------
const MONTHS = { jan: 'JAN', feb: 'FEB', mar: 'MAR', apr: 'APR', may: 'MAY', jun: 'JUN',
  jul: 'JUL', aug: 'AUG', sep: 'SEP', oct: 'OCT', nov: 'NOV', dec: 'DEC' };

// Turns "12 Nov 1876 · Hamme (Oost-Vlaanderen)" or "6 Jan 1905 Oostende" or
// "~1682 · Evergem" into a GEDCOM date and a place. Anything it cannot read with
// confidence comes back as null so the caller keeps the original text instead.
function parseWhen(raw) {
  if (!raw) return null;
  let s = String(raw).trim();
  let qualifier = '';

  s = s.replace(/^†\s*/, '');
  if (/^(b|d)\.\s*/i.test(s)) s = s.replace(/^(b|d)\.\s*/i, '');

  // Some records lead with the place — "Oostende, after 2000". Take it off the
  // front so the remainder can be read as a date.
  let leadingPlace = null;
  const lead = s.match(/^([^,0-9<>~]+),\s*(.+)$/);
  if (lead) { leadingPlace = lead[1].trim(); s = lead[2].trim(); }

  if (/^(bef\.?|before)\s+/i.test(s)) { qualifier = 'BEF'; s = s.replace(/^(bef\.?|before)\s+/i, ''); }
  else if (/^</.test(s)) { qualifier = 'BEF'; s = s.replace(/^<\s*/, ''); }
  else if (/^(aft\.?|after)\s+/i.test(s)) { qualifier = 'AFT'; s = s.replace(/^(aft\.?|after)\s+/i, ''); }
  else if (/^>/.test(s)) { qualifier = 'AFT'; s = s.replace(/^>\s*/, ''); }
  else if (/^[~≈]\s*/.test(s) || /^(c\.|ca\.?|circa|about|abt\.?)\s+/i.test(s)) {
    qualifier = 'ABT';
    s = s.replace(/^[~≈]\s*/, '').replace(/^(c\.|ca\.?|circa|about|abt\.?)\s+/i, '');
  }

  let date = null;
  let rest = s;
  let m;
  // "1575..1587" is a span, and "1913/14" means one year or the other. GEDCOM
  // says both with a range, which is more faithful than picking one end.
  if ((m = s.match(/^(\d{4})\s*\.\.\s*(\d{4})/))) {
    date = `BET ${m[1]} AND ${m[2]}`;
    rest = s.slice(m[0].length);
    qualifier = '';
  } else if ((m = s.match(/^(\d{4})\/(\d{1,2})\b/))) {
    const second = m[2].length === 2 ? m[1].slice(0, 2) + m[2] : m[1].slice(0, 3) + m[2];
    date = `BET ${m[1]} AND ${second}`;
    rest = s.slice(m[0].length);
    qualifier = '';
  } else if ((m = s.match(/^(\d{1,2})\s+([A-Za-z]{3})[a-z]*\.?\s+(\d{4})/))) {
    const mon = MONTHS[m[2].toLowerCase()];
    if (mon) { date = `${Number(m[1])} ${mon} ${m[3]}`; rest = s.slice(m[0].length); }
  } else if ((m = s.match(/^([A-Za-z]{3})[a-z]*\.?\s+(\d{4})/))) {
    const mon = MONTHS[m[1].toLowerCase()];
    if (mon) { date = `${mon} ${m[2]}`; rest = s.slice(m[0].length); }
  } else if ((m = s.match(/^(\d{4})/))) {
    date = m[1];
    rest = s.slice(m[0].length);
  }
  if (!date) return null;

  // "2017 & 2019 · Leuven" is two people's dates in one field — not a single event.
  if (/^\s*&/.test(rest)) return null;

  let place = leadingPlace || rest.replace(/^\s*[·,]\s*/, '').replace(/^\s+/, '').trim() || null;
  // A place name starts with a letter. Anything else is parser debris from a date
  // format not anticipated here, and is dropped rather than published as a place.
  if (place && !/^[A-Za-zÀ-ÿ]/.test(place)) {
    report.notes.push(`discarded "${place}" as a place — from "${raw}"`);
    place = null;
  }
  return { date: qualifier ? `${qualifier} ${date}` : date, place };
}

// Marriage details are free text like "Oostkamp, 30 Sep 1863" or
// "m. 4 May 1901 (legitimized 2 children); divorced ~1923". A leading word with
// no digits is the place; the rest is tried as a date. The raw text is always
// kept as a note, so nothing is lost to the parser's judgement.
function parseMarriage(detail) {
  if (!detail) return null;
  const out = { note: detail, date: null, place: null };
  let s = detail.replace(/^m\.\s*/i, '').replace(/^married\s+/i, '');
  const m = s.match(/^([^,0-9]+),\s*(.+)$/);
  if (m) { out.place = m[1].trim(); s = m[2]; }
  const when = parseWhen(s);
  if (when) {
    out.date = when.date;
    if (!out.place && when.place && !/[();—]/.test(when.place)) out.place = when.place;
  }
  return out;
}

// ---------- occupations ----------
// `occupation` means only an occupation, so this is a straight copy. It used to
// be a guess: the old `role` field mixed occupations with relationship labels and
// nicknames, and the exporter had to sort them out with a regex.
const occupationOf = id => {
  const occ = people[id].occupation;
  if (occ) report.occupations++;
  return occ || null;
};

// ---------- sex ----------
// Stated if the record says so, otherwise inferred from being someone's father or
// mother, otherwise U. GEDCOM has a value for "we do not know"; use it.
const sex = {};
for (const id of ids) {
  const p = people[id];
  if (p.sex === 'f' || p.sex === 'm') sex[id] = p.sex;
}
for (const id of ids) {
  const p = people[id];
  if (p.father && !sex[p.father]) sex[p.father] = 'm';
  if (p.mother && !sex[p.mother]) sex[p.mother] = 'f';
}

// ---------- families ----------
// A couple is either proven by a shared child or recorded as a marriage. Both
// produce one FAM; the key is the unordered pair.
const families = new Map();
const famKey = (a, b) => [a, b].sort().join('|');
const familyFor = (a, b) => {
  const key = famKey(a, b);
  if (!families.has(key)) families.set(key, { a, b, children: [], marriage: null });
  return families.get(key);
};

for (const id of ids) {
  const p = people[id];
  if (p.father && p.mother && people[p.father] && people[p.mother]) {
    familyFor(p.father, p.mother).children.push(id);
  }
  for (const s of p.spouses || []) {
    if (s.id && people[s.id]) {
      const fam = familyFor(id, s.id);
      if (!fam.marriage && s.detail) fam.marriage = parseMarriage(s.detail);
    }
  }
}

// A single parent with no recorded partner still needs a family record, or their
// children have no way to point back at them.
for (const id of ids) {
  const p = people[id];
  const parents = [p.father, p.mother].filter(x => x && people[x]);
  if (parents.length === 1) {
    const fam = familyFor(parents[0], parents[0]);
    fam.solo = true;
    if (!fam.children.includes(id)) fam.children.push(id);
  }
}

// ---------- sources ----------
// The per-person source text is free-form prose. Deduplicating it gives a real
// source list that an importing program can show, instead of the same paragraph
// repeated on 174 people.
const sourceText = id => {
  const p = people[id];
  return p.source || (p.branch && branches[p.branch]) || meta.defaultSource;
};
const sourceXref = new Map();
for (const id of ids) {
  const t = sourceText(id);
  if (t && !sourceXref.has(t)) sourceXref.set(t, `@S${sourceXref.size + 1}@`);
}

// QUAY is GEDCOM's certainty scale: 3 primary, 2 secondary, 1 questionable,
// 0 unreliable. It maps onto the project's confidence codes closely enough.
const QUAY = { doc: 3, sup: 2, fam: 1, unk: 0 };

// ---------- emit ----------
// Xrefs are sequential rather than the project's own ids, because some importers
// still enforce the old 20-character limit. The project id is kept on every
// record as a REFN, so the export can be matched back to the source files.
const indiXref = {};
ids.forEach((id, i) => (indiXref[id] = `@I${i + 1}@`));
const famXref = {};
[...families.keys()].forEach((k, i) => (famXref[k] = `@F${i + 1}@`));

const lines = [];
const put = (level, tag, payload) =>
  lines.push(payload == null || payload === '' ? `${level} ${tag}` : `${level} ${tag} ${payload}`);

// A payload that begins with @ would be read as a pointer; GEDCOM escapes it by
// doubling. Newlines become CONT, which is the only continuation v7 has.
function putText(level, tag, text) {
  const parts = String(text).split(/\r?\n/);
  put(level, tag, parts[0].replace(/^@/, '@@'));
  for (const extra of parts.slice(1)) put(level + 1, 'CONT', extra.replace(/^@/, '@@'));
}

put(0, 'HEAD');
put(1, 'GEDC');
put(2, 'VERS', '7.0');
put(1, 'SOUR', 'FAMILY_TREE');
putText(2, 'NAME', 'Family tree of Renée & Léon Bundervoet');
put(1, 'LANG', 'en');
// No HEAD.DATE on purpose: the file is committed, and a timestamp would make it
// differ on every run even when no data changed.
put(1, 'NOTE', 'Generated by tools/export-gedcom.mjs from data/people/*.js — regenerate rather than edit.');

for (const id of ids) {
  const p = people[id];
  put(0, indiXref[id], 'INDI');
  put(1, 'REFN', id);
  put(2, 'TYPE', 'project-id');

  const split = splitName(p.name);
  if (split) {
    putText(1, 'NAME', `${split.given} /${split.surname}/`);
    putText(2, 'GIVN', split.given);
    putText(2, 'SURN', split.surname);
    if (p.nickname) putText(2, 'NICK', p.nickname);
  } else {
    putText(1, 'NAME', p.name);
    if (p.nickname) putText(2, 'NICK', p.nickname);
  }

  put(1, 'SEX', sex[id] ? sex[id].toUpperCase() : 'U');

  for (const [field, tag] of [['born', 'BIRT'], ['died', 'DEAT']]) {
    const raw = p[field];
    if (!raw) continue;
    const when = parseWhen(raw);
    put(1, tag);
    if (when) {
      put(2, 'DATE', when.date);
      if (when.place) putText(2, 'PLAC', when.place);
    } else {
      // Better an honest note than a date the parser guessed at.
      putText(2, 'NOTE', `Recorded as: ${raw}`);
      report.unparsedDates.push(`${id} ${field}: "${raw}"`);
    }
  }

  const occ = occupationOf(id);
  if (occ) putText(1, 'OCCU', occ);

  for (const [key, fam] of families) {
    if (fam.a === id || fam.b === id) put(1, 'FAMS', famXref[key]);
  }
  for (const [key, fam] of families) {
    if (fam.children.includes(id)) put(1, 'FAMC', famXref[key]);
  }

  // Spouses who have no record of their own would vanish entirely otherwise.
  for (const s of p.spouses || []) {
    if (!s.id) putText(1, 'NOTE', `Spouse (no record of their own): ${s.name}${s.detail ? ` — ${s.detail}` : ''}`);
  }

  if (p.note) putText(1, 'NOTE', p.note);
  if (p.dates) putText(1, 'NOTE', `Dates as recorded: ${p.dates}`);

  const src = sourceText(id);
  if (src) {
    put(1, 'SOUR', sourceXref.get(src));
    put(2, 'QUAY', String(QUAY[p.confidence] ?? 2));
  }
}

for (const [key, fam] of families) {
  put(0, famXref[key], 'FAM');
  if (fam.solo) {
    put(1, sex[fam.a] === 'f' ? 'WIFE' : 'HUSB', indiXref[fam.a]);
  } else {
    // Whoever is known to be male takes HUSB; the other slot takes the partner.
    let husb = fam.a;
    let wife = fam.b;
    if (sex[fam.b] === 'm' || sex[fam.a] === 'f') { husb = fam.b; wife = fam.a; }
    put(1, 'HUSB', indiXref[husb]);
    put(1, 'WIFE', indiXref[wife]);
  }
  for (const child of fam.children) put(1, 'CHIL', indiXref[child]);
  if (fam.marriage) {
    put(1, 'MARR');
    if (fam.marriage.date) put(2, 'DATE', fam.marriage.date);
    if (fam.marriage.place) putText(2, 'PLAC', fam.marriage.place);
    putText(2, 'NOTE', `Recorded as: ${fam.marriage.note}`);
  }
}

for (const [text, xref] of sourceXref) {
  put(0, xref, 'SOUR');
  putText(1, 'TITL', text);
}

put(0, 'TRLR');

// ---------- self-check ----------
// Nothing here validates GEDCOM semantics, but a dangling pointer or a level
// that jumps two at once would break an import silently.
const problems = [];
const declared = new Set(lines.filter(l => /^0 @/.test(l)).map(l => l.split(' ')[1]));
let previousLevel = -1;
lines.forEach((line, i) => {
  const level = Number(line.split(' ')[0]);
  if (Number.isNaN(level)) problems.push(`line ${i + 1}: no level — ${line}`);
  if (level > previousLevel + 1) problems.push(`line ${i + 1}: level jumps from ${previousLevel} to ${level}`);
  previousLevel = level;
  const pointer = line.match(/ (@[A-Z0-9_]+@)$/);
  if (pointer && !declared.has(pointer[1]) && !/^0 /.test(line)) {
    problems.push(`line ${i + 1}: points at ${pointer[1]}, which no record declares`);
  }
});
if (lines[0] !== '0 HEAD') problems.push('file does not start with 0 HEAD');
if (lines[lines.length - 1] !== '0 TRLR') problems.push('file does not end with 0 TRLR');

// Well-formed is not the same as faithful. Read the emitted file back as if it
// were someone else's, rebuild the family links from it alone, and check they say
// what data/people/*.js says. This is what catches a HUSB and WIFE the wrong way
// round, or a child hung off the wrong family.
(() => {
  const records = [];
  let current = null;
  for (const line of lines) {
    const parts = line.split(' ');
    if (parts[0] === '0') {
      current = { xref: parts[1]?.startsWith('@') ? parts[1] : null, tag: parts[1]?.startsWith('@') ? parts[2] : parts[1], fields: [] };
      records.push(current);
    } else if (current) {
      current.fields.push({ level: Number(parts[0]), tag: parts[1], value: parts.slice(2).join(' ') });
    }
  }

  const refnOf = {};
  for (const r of records.filter(r => r.tag === 'INDI')) {
    const refn = r.fields.find(f => f.tag === 'REFN');
    if (refn) refnOf[r.xref] = refn.value;
  }

  const parsedParents = {};
  const parsedCouples = new Set();
  for (const fam of records.filter(r => r.tag === 'FAM')) {
    const husb = fam.fields.find(f => f.tag === 'HUSB')?.value;
    const wife = fam.fields.find(f => f.tag === 'WIFE')?.value;
    if (husb && wife) parsedCouples.add([refnOf[husb], refnOf[wife]].sort().join('|'));
    for (const child of fam.fields.filter(f => f.tag === 'CHIL')) {
      const id = refnOf[child.value];
      parsedParents[id] = { husb: refnOf[husb], wife: refnOf[wife] };
    }
  }

  for (const id of ids) {
    const p = people[id];
    const got = parsedParents[id] || {};
    if (p.father && people[p.father] && got.husb !== p.father) {
      problems.push(`round-trip: ${id}'s father reads back as ${got.husb || 'nobody'}, not ${p.father}`);
    }
    if (p.mother && people[p.mother] && got.wife !== p.mother) {
      problems.push(`round-trip: ${id}'s mother reads back as ${got.wife || 'nobody'}, not ${p.mother}`);
    }
    for (const s of p.spouses || []) {
      if (s.id && people[s.id] && !parsedCouples.has([id, s.id].sort().join('|'))) {
        problems.push(`round-trip: the marriage of ${id} and ${s.id} is not in any family`);
      }
    }
  }
  const individuals = records.filter(r => r.tag === 'INDI').length;
  if (individuals !== ids.length) problems.push(`round-trip: ${individuals} individuals in the file, ${ids.length} in the data`);
})();

if (problems.length) {
  for (const p of problems.slice(0, 20)) console.error('error ' + p);
  console.error(`\n${problems.length} problem(s) — not written.`);
  process.exit(1);
}

fs.mkdirSync(path.dirname(OUT), { recursive: true });
fs.writeFileSync(OUT, lines.join('\n') + '\n');

// ---------- report ----------
const rel = path.relative(ROOT, OUT);
console.log(`Wrote ${rel} — ${ids.length} individuals, ${families.size} families, ${sourceXref.size} sources, ${lines.length} lines.`);
console.log(`Occupations recorded: ${report.occupations}`);
if (report.unparsedDates.length) {
  console.log(`\nDates kept as text, not parsed into GEDCOM dates (${report.unparsedDates.length}):`);
  for (const d of report.unparsedDates) console.log('  ' + d);
}
if (report.notes.length) {
  console.log(`\nParser debris dropped (${report.notes.length}):`);
  for (const n of report.notes) console.log('  ' + n);
}
