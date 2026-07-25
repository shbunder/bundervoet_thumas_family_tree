# Family Tree — project charter

Genealogy of **Renée & Léon Bundervoet** (the two children at the root). Static site,
no dependencies, one generation step (`node tools/build.mjs`). 302 people today; the
target is thousands.

This file is the standing brief. Read the objectives, then find work: open frontiers in
[docs/research-log.md](docs/research-log.md), and `node tools/research.mjs report` for
where the effort has already gone.

---

## Objectives

**Primary — these define "done" and rank all work:**

1. **All ancestors of Renée & Léon.** Build the tree *upwards*. Every parent link,
   as far back as records go, on every line.
2. **All blood relatives of Renée & Léon.** Build *downwards* from each ancestral
   couple: their children, their children's children. An ancestor's sibling and that
   sibling's descendants are in scope — they are blood.
3. **Connect all Bundervoets.** Build a *forest* of Bundervoet families and find the
   links between the trees. Disconnected roots are expected and legitimate here.

**Secondary — quality bar applied to every person added:**

- **a.** Gather the full life: birth date & place, death date & place, spouse(s),
  marriage date(s) & place, children, occupation, where they lived, migrations.
- **b.** Every person *referenced anywhere* gets their own record file and a place in
  the tree. No one exists only as a string inside someone else's note.
- **c.** For any two people in the index, the site can state their relation.

Priority when they conflict: 1 > 2 > 3 > a. Depth on the direct lines beats breadth.

**Stretch goal (drives architecture, not current work):** map everyone who ever lived
in Oostende. Assume every design decision will meet 10,000+ people — no hand-maintained
per-person lists, no O(n) manual curation.

---

## Non-negotiable rules

These exist because the failure mode of autonomous genealogy is **silently grafting the
wrong person**. At scale, a bad link is unfindable later. The research log is full of
near-misses: two different Hammes, two Simonne Vandewalles, Van Craenenbroecks in the
wrong province, the Gustaaf/Gustavus confusion.

1. **Never match on name alone.** A graft needs at least two independent identifiers to
   agree — date + place, or parent names, or an occupation + commune. Say which two.
2. **Record the evidence, then the fact.** Every new parent link cites a source in
   `research/sources.json`. A claim with no citation does not go in the tree.
3. **Confidence is honest, not aspirational.** `doc` = a primary act or image was
   actually read. `sup` = one member tree, unverified. `fam` = family testimony.
   `unk` = to research. Downgrading is always allowed; upgrading needs a document.
4. **A strong lead is not a link.** Record it in the person's `note` as a named
   frontier. Do not graft it. (`anna_vc` is the model for how to do this.)
5. **Never invent a field.** If an occupation or a day-level date wasn't in the source,
   it is absent, not guessed. Say "not in the reachable pages" in the log.
6. **Corrections are first-class.** When a past conclusion is wrong, retract it
   explicitly in the log with the reasoning (see §29), fix every record it touched.
7. **Log every search, especially the ones that found nothing.** An unrecorded miss is
   a dead end the next pass will walk again.
8. `node tools/build.mjs` must be green before any commit.

---

## The work loop

Each research pass:

1. **Pick a frontier** — the highest-value unresolved question. Prefer: marriage acts
   (they name *both* spouses' parents — the single richest record); rare surnames over
   common ones; the wife's side when the husband's is blocked. Both breakthroughs in
   this project came from those two moves.
2. **Check what's been tried** — `node tools/research.mjs tried <person>` for the
   history, `untried <person>` for what is left, `yield` for which venues pay off. Do
   not re-walk a logged `miss` without a new angle; `blocked` means it was never
   actually read, so it is worth retrying.
3. **Search** — see [docs/searching.md](docs/searching.md) for the registry, the
   logged-in browser, and what has worked before.
4. **Verify** — actively try to *refute* the identity match before accepting it.
5. **Record** —
   - the person files;
   - `node tools/research.mjs log …` for **every** search, hit or miss — a hit must
     say what it `--found`, anything else must say `--why`;
   - a new site or page in `research/sources.json` if one was discovered, and the
     `yielded` line on any page that produced something;
   - a numbered section in `docs/research-log.md` for the narrative: what was found,
     what came back negative, what the next frontier is.
6. **Build & commit** — `node tools/build.mjs`, then one commit per pass.

**Log the misses.** They are the difference between a loop that converges and one that
searches AGATHA for Édouard's parents every night forever. `docs/sources.md` is
generated from the registry — edit `research/sources.json`, not the markdown.

---

## Data model

`data/people/<id>.md` is the source of truth — one file, one person: a strict
frontmatter block for the facts, and free Markdown prose below it for everything a
field cannot hold. Everything derived (children, generations, kinship, lineages) is
computed from `father`/`mother` links. See [README.md](README.md) for the field list.

Dates use a small fixed grammar so they are queryable and sortable, never prose:
`1876-11-12` · `1876-11` · `1876` · `~1682` about · `<1727` before · `>1900` after ·
`1575..1587` between. There is deliberately no syntax for "probably March" — a format
for a guess is an invitation to record one. If a source says something the grammar
cannot express, put it in `raw` and explain it in the prose.

Invariants:

- `father`/`mother` are ids of other person files — the vertical link.
- `spouses` is a list, oldest first; an entry's `id` links to that spouse's record —
  the horizontal link. **Marriage is mutual** (if A lists B, B lists A) and **a shared
  child proves a couple** (a record with `father: A`, `mother: B` obliges A and B to
  list each other). The validator enforces both; they are what let the tree be built
  downwards without losing branches.
- `occupation` and `nickname` hold only those things. A relationship is never a field:
  it is a fact about a *pair*, so it is derived from the links. Writing "Ronny's sister"
  into a record puts a second, un-checkable copy of the tree in the prose.
- `sex` is `"f"`/`"m"`, optional, and only needed for people who are nobody's parent
  (being a `father`/`mother` already settles it). Record it from what the source says —
  a note calling someone "Roland's sister", a role of "wife" — never from a forename.
- **Nothing is listed twice.** The roster is the directory; the Index groups from each
  person's own `line`; citations are ids into `research/sources.json`. If you find
  yourself keeping two things in step by hand, that is the bug.
- The prose body is for reasoning, evidence and frontiers — the things that do not fit
  a field. It is never a second copy of a field.
- Ids are stable. Renaming one breaks every reference — don't.
- Plain text in data files (`é`, `&`), never HTML entities. The renderer escapes.
- Presentation carries no facts: nothing in `assets/` contains a name or a date.

Kinship is root-free: `relationBetween(a, b)` in `assets/js/kinship.js` works from the
pair's lowest common ancestor, so it relates anyone to anyone (objective c). The Index's
three categories are derived from the links, so a new person appears without being added
to any list. `meta.roots` takes a list for the forest case (objective 3); with one root
it is the ordinary tree.

The page loads `dist/bundle.js` — one request for the whole tree, whatever it grows to.
The files in `data/` and `site/` stay the source of truth; the bundle is generated, and
the validator fails if it is stale, so old data cannot reach the site.

**Known limits of the current model** — the next structural work:

1. **The bundle is loaded eagerly and committed whole.** ~580 bytes per person, so
   ~6 MB and a full rewrite per commit at 10,000 people. Past a few thousand it wants
   splitting (by branch or generation) and loading on demand, and the build moving to
   CI so the artefact leaves git. The relation finder's two `<select>`s go the same way.
2. **Sex is unknown for anyone childless** unless their record states it. Relations then
   read "sibling" rather than "sister". Fill `sex` in only from what a record says.
   *(Currently all 302 are known — keep it that way as people are added.)*

---

## Layout

Three things, kept apart because they change for different reasons and different
rules apply to each. `data/` is the only place a name or a date may appear;
`site/` is wording the page shows and cannot change what the tree claims;
`assets/` contains neither.

```
data/people/<id>.md     source of truth: strict frontmatter + prose body
data/meta.json          roots, confidence codes
data/branches.json      surname branch -> its default source id
data/lineages.json      the surname chains
site/labels.json        presentation only: labels, Index headings, footer
research/sources.json   the registry — SITES (venues) and PAGES (trees, documents)
research/searches.jsonl the search log, append-only, with what each search found or why not
docs/research-log.md    numbered passes: found / checked-and-negative / next
docs/searching.md       the search strategy, the browser, what has worked
docs/sources.md         readable source list — GENERATED from research/sources.json
docs/sources/           saved act images and scans
tools/lib/              the shared loader, frontmatter parser and date grammar
tools/build.mjs         validates, then writes everything generated
tools/check-data.mjs    the validator
tools/research.mjs      log a search, ask what's been tried, see what yields
tools/export-gedcom.mjs writes exports/family-tree.ged
dist/bundle.js          GENERATED — what the page loads
exports/family-tree.ged GENERATED — GEDCOM 7
assets/                 presentation only — no names, no dates
archive/                superseded drafts, not part of the site
```

Nothing in `data/` is executable. It is JSON and Markdown, readable by any tool
without a JavaScript engine — `jq '.branches' data/branches.json` works, and so does
grep over the person records.

## Commands

```
node tools/build.mjs           validate, then regenerate bundle.js + the GEDCOM
node tools/check-data.mjs      validate only (must be green before commit)
node tools/research.mjs frontiers        what to work on next, ranked
node tools/research.mjs tried <person>    what was searched, found, and why it failed
node tools/research.mjs untried <person> sites and pages not yet tried on them
node tools/research.mjs yield            which sites and pages actually pay off
node tools/research.mjs log …            record a search — hit or miss
open index.html                the site, straight off disk
```

**After changing anything in `data/`, run `node tools/build.mjs`.** It validates first
and refuses to generate from a broken tree. `check-data.mjs` fails if the generated
files are stale, so the "green before commit" rule already covers this.

`exports/family-tree.ged` is the tree in **GEDCOM 7**, the open format every genealogy
program reads — import it into Gramps, Geneanet, Ancestry or MyHeritage, and it is the
form to hand to anything that wants the data without parsing `.js`. It is generated, so
edits belong in `data/people/` and the file is regenerated.

The exporter refuses to write if the file does not read back as the same tree: it
reparses its own output, rebuilds the parent and marriage links from that alone, and
compares them to the source records. It also reports what GEDCOM could not carry —
dates too vague to express, `role` values that are relationships rather than
occupations — rather than flattening them into fields that would then read as fact.

---

## Open decisions

Not yet decided — do not implement unilaterally:

- **Storage format.** Moving the person files to strict-fielded frontmatter + free-prose
  body. The build step exists now, so the objection has narrowed to whether the working
  files themselves change shape. *(Interchange is settled: GEDCOM 7 is exported.)*
- **Marriage detail is still prose.** `spouses[].detail` holds "Oostkamp, 30 Sep 1863"
  as free text, so the GEDCOM exporter still parses it. Person dates are structured;
  marriages are the last place that isn't.
**Waiting on you, not on a decision:** the browser server in `.mcp.json` needs Chrome
started with remote debugging and logged in to the archives once — see
[docs/searching.md](docs/searching.md). Until then, searches that need a session come
back `blocked`, not `miss`.
