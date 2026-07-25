// Loading and interpreting the data. Every tool goes through here, so there is
// one definition of what a person is rather than four copies drifting apart.
import fs from 'node:fs';
import path from 'node:path';
import vm from 'node:vm';
import { fileURLToPath } from 'node:url';
import { parseFrontmatter } from './frontmatter.mjs';

export const ROOT = path.join(path.dirname(fileURLToPath(import.meta.url)), '..', '..');
export const DATA = path.join(ROOT, 'data');
export const PEOPLE_DIR = path.join(DATA, 'people');

// The fields a person record may carry, in the order they are written.
export const FIELDS = ['id', 'name', 'sex', 'birth', 'death', 'confidence', 'occupation', 'nickname', 'branch', 'father', 'mother', 'spouses', 'source'];
export const EVENT_FIELDS = ['date', 'place'];
export const SPOUSE_FIELDS = ['id', 'name', 'detail'];

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
export function loadConfig() {
  let captured;
  const rec = v => (captured = v);
  const ctx = vm.createContext({
    FamilyTree: { person: rec, roster: rec, meta: rec, branches: rec, lineages: rec, groups: rec },
  });
  const read = file => {
    captured = undefined;
    vm.runInContext(fs.readFileSync(path.join(DATA, file), 'utf8'), ctx, { filename: file });
    return captured;
  };
  return {
    roster: read('people.js'),
    meta: read('meta.js'),
    branches: read('branches.js'),
    lineages: read('lineages.js'),
    groups: read('groups.js'),
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

export const onDisk = () =>
  fs.readdirSync(PEOPLE_DIR).filter(f => f.endsWith('.md')).map(f => f.slice(0, -3));

// ---------- the shape the browser reads ----------
// The site loads a generated bundle, so the display strings are computed once
// here rather than in the renderer, and assets/ stays free of any logic about
// what a date means.
export function toBrowserRecord(p) {
  const out = {
    id: p.id,
    name: p.name,
    dates: displayDates(p),
    confidence: p.confidence,
  };
  if (p.sex) out.sex = p.sex;
  if (p.birth) out.born = eventText(p.birth);
  if (p.death) out.died = eventText(p.death);
  if (p.occupation) out.occupation = p.occupation;
  if (p.nickname) out.nickname = p.nickname;
  if (p.branch) out.branch = p.branch;
  if (p.father) out.father = p.father;
  if (p.mother) out.mother = p.mother;
  if (p.spouses) out.spouses = p.spouses;
  if (p.source) out.source = p.source;
  if (p.note) out.note = p.note;
  return out;
}
