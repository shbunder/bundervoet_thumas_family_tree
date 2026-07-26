# Data model

!!! info "Field-by-field reference"
    The complete field list, with a worked example, lives in
    [README.md](https://github.com/example/family-tree#a-person-file). It is not repeated
    here — this project's own rule is that nothing is listed twice, and a spec kept in
    two places is a spec that drifts. This page covers the *design*: why the model has
    this shape, and what the validator guarantees.

## One file, one person

`data/people/<id>.md` is the source of truth: a strict frontmatter block for facts, free
Markdown prose below it for everything a field cannot hold.

```
data/people/<id>.md     strict frontmatter + prose body
data/artifacts/<id>.*   a saved primary document + a record describing it
data/meta.json          roots, confidence codes
data/branches.json      surname branch → its default source id
data/lineages.json      the surname chains
data/forenames.json     forenames that are one name in another language, split by sex
```

Nothing in `data/` is executable. It is JSON and Markdown, readable by any tool without a
JavaScript engine — `jq '.branches' data/branches.json` works, and so does `grep` over the
person records. That is a deliberate durability property: the data outlives the tooling.

## Stored versus derived

The central discipline. **Only irreducible facts are stored.** Everything else is
computed on load from `father`/`mother` links:

- children, siblings, generations
- kinship between any two people
- lineages and Index groupings
- the display line under each name

> If you find yourself keeping two things in step by hand, that is the bug.

A relationship is **never a field**. It is a fact about a *pair*, so it is derived.
Writing "Ronny's sister" into a record puts a second, un-checkable copy of the tree into
the prose, and nothing will ever validate it.

The prose body is for reasoning, evidence and frontiers — the things that do not fit a
field. It is never a second copy of one.

## Invariants the validator enforces

| Invariant | Why |
|---|---|
| `father`/`mother` are ids of real person files | The vertical link |
| **Marriage is mutual** — if A lists B, B lists A | Lets the tree be walked sideways |
| **A shared child proves a couple** — `father: A` + `mother: B` obliges each to list the other | Lets the tree be built *downwards* without losing branches |
| Every referenced person has their own file | No one exists only as a string in someone else's note |
| Every citation resolves to `research/sources.json` | A claim with no citation is not a claim |
| Every artifact's `sha256`/`bytes` recompute correctly | Evidence cannot change under a citation |
| Generated files are not stale | Old data cannot reach the site |
| Demographic plausibility | The arithmetic signature of a graft off by a generation |

Ids are stable. Renaming one breaks every reference — don't.

## The date grammar

A deliberately small, fixed grammar, so dates are queryable and sortable rather than
prose:

| Form | Meaning | Asserts a year? |
|---|---|:-:|
| `1876-11-12` | a day | ✅ |
| `1876-11` | a month | ✅ |
| `1876` | a year | ✅ |
| `~1682` | about | ✅ (with slack) |
| `<1727` | before | ❌ bound only |
| `>1900` | after | ❌ bound only |
| `1575..1587` | between | ❌ bound only |

There is deliberately **no syntax for "probably March"**. A format for a guess is an
invitation to record one. If a source says something the grammar cannot express, it goes
in `raw` and is explained in the prose.

!!! warning "A bound is not a measurement"
    `year_of()` reads a number out of any form — correct for **sorting**. `point_year()`
    returns a year only for forms that actually *assert* one — required for
    **arithmetic**.

    Treating `<1673` as a birth year once produced *"is mother at age -6"* for a record
    that was never in conflict with anything. The two functions exist separately because
    the difference is invisible until something does sums, which is exactly when it
    matters.

## Artifacts are data, not documentation

A scan or photograph of an act **is the evidence**, so it lives in `data/artifacts/`
alongside the facts — not in `docs/` with the writing about them.

Each artifact is a file plus a record of the same name in the same frontmatter format,
carrying `sha256` and `bytes`, with the transcription in its prose body. The validator
recomputes the checksum on every build.

The reasoning: *a citation whose evidence has silently changed underneath it is worse
than one with no evidence, because it still reads as sourced.*

The record must also say whether the act **image** was read or only an index page. They
are different evidence and only one of them earns `confidence: doc`.

### Why the images are committed

The harvested corpus is gitignored because it is re-fetchable — the manifest reproduces
it. An artifact is the opposite: the validator recomputes its digest on every build, so a
missing file is a hard error rather than a degraded clone. Excluding the images would
leave a checksum with nothing to check and a citation pointing at nothing, which is the
exact failure the design exists to prevent. Archive URLs rot; the held copy is the point.

The constraint that actually binds is **rights**, not size. A scan usually belongs to the
holding institution named in the record's `repository` field. Where it may not be
redistributed, keep the record and its transcription and leave the image out — the record
still carries the URL, the digest and a statement of what was read.

## Kinship is root-free

`relationBetween(a, b)` works from the pair's lowest common ancestor, so it relates
anyone to anyone rather than everyone to a root. The Index's categories are derived from
the links, so a new person appears without being added to any list.

`meta.roots` takes a *list*, for the forest case — disconnected roots are expected and
legitimate while separate family clusters are still being joined.

## Interchange

`exports/family-tree.ged` is the tree in **GEDCOM 7**, the open format every genealogy
program reads. It is generated, so edits belong in `data/people/`.

The exporter **refuses to write if the file does not read back as the same tree**: it
reparses its own output, rebuilds the parent and marriage links from that alone, and
compares them to the source records. It also reports what GEDCOM could not carry — dates
too vague to express, roles that are relationships rather than occupations — rather than
flattening them into fields that would then read as fact.

The natural second target is **IDS**, the Intermediate Data Structure used in historical
demography (the [Antwerp COR\* database](prior-work.md#the-antwerp-cor-database-flanders)
was re-released in it). IDS models events and their sources rather than conclusions about
people, which is much closer to how `corpus.py` already works.

## Known limits

1. **The bundle is loaded eagerly and committed whole.** ~580 bytes per person, so ~6 MB
   and a full rewrite per commit at 10,000 people. Past a few thousand it wants splitting
   and loading on demand, with the build moving to CI so the artefact leaves git. See
   [Scaling](method/scaling.md).
2. **Sex is unknown for anyone childless** unless their record states it — relations then
   read "sibling" rather than "sister". Fill `sex` in only from what a record says, never
   from a forename.
