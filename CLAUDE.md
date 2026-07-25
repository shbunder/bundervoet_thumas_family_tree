# Family Tree — project charter

Genealogy of **Renée & Léon Bundervoet** (the two children at the root). Static site,
no build step, no dependencies. 301 people today; the target is thousands.

This file is the standing brief. Read the objectives, then read
[docs/research-log.md](docs/research-log.md) §"open frontiers" to find work.

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
   [docs/sources.md](docs/sources.md). A claim with no citation does not go in the tree.
3. **Confidence is honest, not aspirational.** `doc` = a primary act or image was
   actually read. `sup` = one member tree, unverified. `fam` = family testimony.
   `unk` = to research. Downgrading is always allowed; upgrading needs a document.
4. **A strong lead is not a link.** Record it in the person's `note` as a named
   frontier. Do not graft it. (`anna_vc` is the model for how to do this.)
5. **Never invent a field.** If an occupation or a day-level date wasn't in the source,
   it is absent, not guessed. Say "not in the reachable pages" in the log.
6. **Corrections are first-class.** When a past conclusion is wrong, retract it
   explicitly in the log with the reasoning (see §29), fix every record it touched.
7. `node tools/check-data.mjs` must be green before any commit.

---

## The work loop

Each research pass:

1. **Pick a frontier** — the highest-value unresolved question. Prefer: marriage acts
   (they name *both* spouses' parents — the single richest record); rare surnames over
   common ones; the wife's side when the husband's is blocked. Both breakthroughs in
   this project came from those two moves.
2. **Search** — consult the source registry first; check the log for what has already
   been tried and failed, so dead ends aren't re-walked.
3. **Verify** — actively try to *refute* the identity match before accepting it.
4. **Record** — person files + `docs/sources.md` entry + a numbered section in
   `docs/research-log.md` saying what was found, what was checked and came back
   negative, and what the next frontier is.
5. **Validate & commit** — `node tools/check-data.mjs`, then one commit per pass.

Negative results are worth recording. "AGATHA is exhausted for Édouard's parentage" is
a real finding that saves the next pass a day.

---

## Data model

`data/people/<id>.js` is the source of truth — one file, one person, registering itself
via `FamilyTree.person({...})`. Everything derived (children, generations, kinship,
lineages) is computed at load time from `father`/`mother` links. See
[README.md](README.md) for the field list and the reason the files are `.js` not `.json`.

Invariants:

- `father`/`mother` are ids of other person files — the vertical link.
- `spouses` is a list, oldest first; an entry's `id` links to that spouse's record —
  the horizontal link. **Marriage is mutual** (if A lists B, B lists A) and **a shared
  child proves a couple** (a record with `father: A`, `mother: B` obliges A and B to
  list each other). The validator enforces both; they are what let the tree be built
  downwards without losing branches.
- Every id in `data/people/` is listed in `data/people.js`.
- Ids are stable. Renaming one breaks every reference — don't.
- Plain text in data files (`é`, `&`), never HTML entities. The renderer escapes.
- Presentation carries no facts: nothing in `assets/` contains a name or a date.

**Known limits of the current model** — these block the objectives above and are the
next structural work, in this order:

1. **Kinship is root-relative.** `assets/js/kinship.js` walks from the single
   `meta.root`. Objective (c) needs a root-free relationship calculator (lowest common
   ancestor → "second cousin twice removed"), and objective 3 needs multiple roots.
2. **`data/groups.js` is hand-curated.** 301 ids maintained by hand does not reach
   10,000. The Index tab's three categories — **ancestors / relatives / other** — are
   computable from the links and should be derived, not listed.
3. **One `<script>` tag per person.** Fine at 301, fatal at thousands. Needs a bundled
   data file (and therefore a build step) before the tree grows an order of magnitude.

---

## Layout

```
data/people/<id>.js     source of truth, one per person
data/people.js          manifest of ids to load
data/groups.js          Index tab grouping     ← to be derived (see above)
data/lineages.js        the surname chains
data/branches.js        default citation per branch
data/meta.js            root, confidence labels, footer
docs/research-log.md    numbered passes: found / checked-and-negative / next
docs/sources.md         source registry, stable S-ids, with local artifacts
docs/sources/           saved act images and scans
tools/check-data.mjs    the validator
assets/                 presentation only — no names, no dates
archive/                superseded drafts, not part of the site
```

## Commands

```
node tools/check-data.mjs      validate (must be green before commit)
open index.html                the site, straight off disk
```

---

## Open decisions

Not yet decided — do not implement unilaterally:

- **Storage format.** Moving to strict-fielded frontmatter + free-prose body, aligned
  to an open vocabulary (schema.org / GEDCOM X) with a GEDCOM export, and a build step
  emitting the browser bundle. Trade-off: loses "works straight off disk with no build".
- **Research logging format.** Machine-readable per-person search log (which source,
  which query, hit/miss/ambiguous, artifact path) replacing prose-only logging.
- **Browser-based searching.** A logged-in browser for Geneanet / FamilySearch /
  Ancestry, driven by an MCP browser server.
- **Sub-agent split** for autonomous runs (strategist / searcher / verifier / archiver).
