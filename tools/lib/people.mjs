// Loading and interpreting the data. Every tool goes through here, so there is
// one definition of what a person is rather than four copies drifting apart.
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { parseFrontmatter } from './frontmatter.mjs';

export const ROOT = path.join(path.dirname(fileURLToPath(import.meta.url)), '..', '..');
export const DATA = path.join(ROOT, 'data');
export const PEOPLE_DIR = path.join(DATA, 'people');
export const ARTIFACTS_DIR = path.join(DATA, 'artifacts');

// The fields a person record may carry, in the order they are written.
export const FIELDS = ['id', 'name', 'surname', 'sex', 'birth', 'death', 'confidence', 'occupation', 'nickname', 'branch', 'line', 'father', 'mother', 'spouses', 'sources'];
export const EVENT_FIELDS = ['date', 'place'];
export const SPOUSE_FIELDS = ['id', 'name', 'detail'];
// An artifact is a saved primary document — a scan or photograph of an act. It is
// evidence, so it lives in data/ with the facts, not in docs/ with the writing
// about them, and it carries its own record in the same frontmatter format.
export const ARTIFACT_FIELDS = [
  'id', 'file', 'media', 'bytes', 'sha256', 'title', 'kind', 'event', 'date',
  'place', 'repository', 'collection', 'source', 'url', 'accessed', 'evidences',
];

// ---------- dates ----------
// A deliberately small grammar, so a date is queryable and sortable instead of
// being prose the next tool has to guess at:
//
//   1876-11-12   a day            1876-11   a month           1876   a year
//   ~1682        about            <1727     before            >1900  after
//   1575..1587   between two years
//
// Anything a source did not actually say is simply absent. There is no format
// for "probably March", because inventing one invites inventing the fact.
const DAY = /^\d{4}-\d{2}-\d{2}$/;
const MONTH = /^\d{4}-\d{2}$/;
const YEAR = /^\d{4}$/;
const APPROX = /^~\d{4}$/;
const BEFORE = /^<\d{4}$/;
const AFTER = /^>\d{4}$/;
const RANGE = /^\d{4}\.\.\d{4}$/;

export const isValidDate = s =>
  typeof s === 'string' && [DAY, MONTH, YEAR, APPROX, BEFORE, AFTER, RANGE].some(re => re.test(s));

const MONTH_NAMES = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];

// The human form. The machine form is what is stored; this is only ever display.
export function formatDate(s) {
  if (!s) return '';
  if (DAY.test(s)) {
    const [y, m, d] = s.split('-');
    return `${Number(d)} ${MONTH_NAMES[Number(m) - 1]} ${y}`;
  }
  if (MONTH.test(s)) {
    const [y, m] = s.split('-');
    return `${MONTH_NAMES[Number(m) - 1]} ${y}`;
  }
  if (APPROX.test(s)) return `~${s.slice(1)}`;
  if (BEFORE.test(s)) return `before ${s.slice(1)}`;
  if (AFTER.test(s)) return `after ${s.slice(1)}`;
  if (RANGE.test(s)) return s.replace('..', '–');
  return s;
}

const eventText = e => {
  if (!e) return '';
  const parts = [formatDate(e.date), e.place].filter(Boolean);
  return parts.join(' ');
};

// The line shown under a name. Derived, never stored — one fact, one place.
export function displayDates(p) {
  const b = eventText(p.birth);
  const d = eventText(p.death);
  if (b && d) return `${b} – ${d}`;
  if (b) return `b. ${b}`;
  if (d) return `d. ${d}`;
  return '';
}

// ---------- loading ----------
export const SITE = path.join(ROOT, 'site');

const readJson = file => JSON.parse(fs.readFileSync(file, 'utf8'));

// data/ holds facts; site/ holds the words the page shows. Keeping them apart is
// what stops a heading or a label being mistaken for something a record asserts.
//
// None of this is executable any more. It used to be JavaScript run in a vm
// sandbox, because the browser loaded the files directly; the browser now loads a
// generated bundle instead, so the source can be plain JSON that any tool — or any
// agent with `jq` — can read without a JavaScript engine.
export function loadConfig() {
  const meta = readJson(path.join(DATA, 'meta.json'));
  const site = readJson(path.join(SITE, 'labels.json'));
  return {
    roster: onDisk().sort(),
    meta,
    // The explorer opens on the first root; a forest just has more of them.
    root: meta.roots[0],
    branches: readJson(path.join(DATA, 'branches.json')).branches,
    lineages: readJson(path.join(DATA, 'lineages.json')).lineages,
    site,
    groups: site.groups,
  };
}

export function loadPerson(id) {
  const file = path.join(PEOPLE_DIR, `${id}.md`);
  const { data, body } = parseFrontmatter(fs.readFileSync(file, 'utf8'), `${id}.md`);
  if (body) data.note = body;
  return data;
}

export function loadPeople(roster) {
  const ids = roster || loadConfig().roster;
  const people = {};
  for (const id of ids) people[id] = loadPerson(id);
  return people;
}

export function loadArtifacts() {
  if (!fs.existsSync(ARTIFACTS_DIR)) return {};
  const out = {};
  for (const f of fs.readdirSync(ARTIFACTS_DIR).filter(f => f.endsWith('.md'))) {
    const { data, body } = parseFrontmatter(fs.readFileSync(path.join(ARTIFACTS_DIR, f), 'utf8'), f);
    if (body) data.note = body;
    out[f.slice(0, -3)] = data;
  }
  return out;
}

export const onDisk = () =>
  fs.readdirSync(PEOPLE_DIR).filter(f => f.endsWith('.md')).map(f => f.slice(0, -3));

// ---------- names ----------
// `name` is the name as the record wrote it, particles, spelling and all. Which
// part of it is the family name cannot be computed: a quarter of these names carry
// a particle ("Van den Broucke", "Vande Woestijne", "'t Jonck"), so the last word
// is the wrong answer often enough to matter, and the exporter's particle
// heuristic silently produced no surname at all for six people. So `surname` is
// stated, not guessed — and it is the only extra name field, because "Christianus
// Josephus" is one compound given name, not a first name plus a middle name.
//
// Given names are therefore derived, not stored: the name with the surname removed.
// The surname is usually last, but not always: "Marie Anne Catherine Quinart
// (Kinart)" ends with a variant spelling, so cutting only from the end left the
// surname sitting in the given names as well.
export const givenNames = p => {
  if (!p.surname) return p.name;
  const at = p.name.lastIndexOf(p.surname);
  if (at < 0) return p.name;
  return (p.name.slice(0, at) + p.name.slice(at + p.surname.length)).replace(/\s{2,}/g, ' ').trim();
};

// The grouping key. Spelling varies by the record a person was found in — the
// same Oostende family is written "Dekeyser" and "De Keyser", and both are kept
// on purpose — so grouping compares surnames with case, spacing and accents
// removed. This is what lets objective 3 ask "who are all the Bundervoets?"
// without a hand-maintained list.
export const familyKey = surname =>
  (surname || '').toLowerCase().normalize('NFD').replace(/[̀-ͯ]/g, '').replace(/[^a-z]/g, '');

// ---------- the shape the browser reads ----------
// The site loads a generated bundle, so the display strings are computed once
// here rather than in the renderer, and assets/ stays free of any logic about
// what a date means.
// Titles for the registry ids, loaded once so records can cite `tree-isavdw`
// instead of repeating "Geneanet tree isavdw (Rijksarchief scans)" 25 times.
let sourceTitles = {};
export function setSourceTitles(map) {
  sourceTitles = map;
}

export function toBrowserRecord(p) {
  const out = {
    id: p.id,
    name: p.name,
    dates: displayDates(p),
    confidence: p.confidence,
  };
  // Both derived here rather than in the renderer, so assets/ never has to know
  // what a particle is.
  if (p.surname) {
    out.surname = p.surname;
    out.family = familyKey(p.surname);
  }
  if (p.sex) out.sex = p.sex;
  if (p.birth) out.born = eventText(p.birth);
  if (p.death) out.died = eventText(p.death);
  if (p.occupation) out.occupation = p.occupation;
  if (p.nickname) out.nickname = p.nickname;
  if (p.branch) out.branch = p.branch;
  if (p.line) out.line = p.line;
  if (p.father) out.father = p.father;
  if (p.mother) out.mother = p.mother;
  if (p.spouses) out.spouses = p.spouses;
  // The records cite the registry by id; the browser wants something readable.
  // Resolving here keeps the citation in one place and the prose out of the data.
  if (p.sources && p.sources.length) out.source = p.sources.map(id => sourceTitles[id] || id).join('; ');
  if (p.note) out.note = p.note;
  return out;
}
