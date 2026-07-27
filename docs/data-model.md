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
data/meta.json          roots, the default source, confidence codes
data/lineages.json      the surname chains
data/forenames.json     forenames that are one name in another language, split by sex
```

Nothing in `data/` is executable. It is JSON and Markdown, readable by any tool without a
JavaScript engine — `jq '.lineages' data/lineages.json` works, and so does `grep` over the
person records. That is a deliberate durability property: the data outlives the tooling.

## Where everything lives

**The one authoritative listing.** `CLAUDE.md` and `README.md` link here rather than
repeating it: there were three copies, and when `data/forenames.json` was added only two of
them learned about it.

Three top-level directories are kept apart because different rules apply to each. `data/` is
the only place a name or a date may appear; `site/` is wording the page shows and cannot
change what the tree claims; `assets/` contains neither.

```
index.html                      landing page — loads no JavaScript
Renee-Leon-family-tree.html     the interactive tree (page shell only)

data/people/<id>.md             source of truth: strict frontmatter + prose body
data/artifacts/<id>.*           a saved primary document + a record describing it
data/meta.json                  roots, the default source, confidence codes
data/lineages.json              the surname chains
data/forenames.json             forenames that are one name in another language, by sex

site/labels.json                presentation only, in every language: UI strings, Index
                                headings, footer, relation vocabulary. No word the page
                                shows is written anywhere else — see assets/js/i18n.js

research/sources.json           the registry — SITES (venues) and PAGES (trees, documents)
research/searches.jsonl         the search log, append-only: what each search found, or why not
research/labels.jsonl           the gold standard: every verifier ruling, as a labelled pair
research/harvest/               the corpus — acts from Open Archives. GITIGNORED
research/harvest/corpus.db      the derived index over those acts. GITIGNORED, rebuildable
research/harvest/manifest.json  which queries were run — committed, so the corpus replays

tools/familytree/               the library every tool shares
  people.py                     the loader, the date grammar, the browser record, the census
  frontmatter.py                the parser for the records' strict YAML subset
  sources.py                    the registry and the search log, and what makes an entry valid
  labels.py                     the gold standard, readable by the QUEUES and not only the scorer
  landing.py                    what index.html says about the size of the tree
  bundle.py                     data/ + site/ -> dist/bundle.js
  gedcom.py                     the GEDCOM 7 writer and its round-trip self-check
  corpus.py                     harvested acts read as EVENTS: roles, parent edges, frequencies
  a2a.py                        the same acts as XML — what makes a whole archive one request
  store.py                      the corpus as a SQLite index: blocking keys, offsets, frequencies
  match.py                      blocking keys, Flemish phonetics, rarity-weighted scoring
  frontier.py                   the ranked queue: value x P(resolvable) / cost
  coverage.py                   which act answers most frontiers; components; pedigree collapse
tools/build.py                  validates, then writes everything generated
tools/check_data.py             the validator
tools/verify_all.py             the whole tree scored against the whole corpus, in one pass
tools/research.py               the log, the registry, and every derived report
tools/harvest.py                pull acts from Open Archives and keep them
tools/link.py                   join the held acts to a frontier — candidates, never conclusions
tools/identify.py               is this person already in the tree? ask before writing a record
tools/evaluate.py               the gold standard: label a ruling, then measure the scorer on it
tools/export_gedcom.py          writes exports/family-tree.ged

assets/                         presentation only — no names, no dates
docs/                           the method, written up — mkdocs.yml renders it to dist/docs/
docs/research-log.md            numbered passes: found / checked-and-negative / next
docs/sources.md                 readable source list — GENERATED from research/sources.json
dist/bundle.js                  GENERATED — what the page loads
exports/family-tree.ged         GENERATED — GEDCOM 7
archive/                        superseded drafts, not part of the site
pyproject.toml                  the uv project. No dependencies, on purpose
```

## Stored versus derived

The central discipline. **Only irreducible facts are stored.** Everything else is
computed on load from `father`/`mother` links:

- children, generations
- siblings — *except* the sibships no parent link can state; see below
- kinship between any two people
- lineages and Index groupings
- the display line under each name

> If you find yourself keeping two things in step by hand, that is the bug.

A relationship is **never a field**. It is a fact about a *pair*, so it is derived.
Writing "Ronny's sister" into a record puts a second, un-checkable copy of the tree into
the prose, and nothing will ever validate it.

**`siblings` is the one exception, and it is fenced rather than waved through.** See
[below](#siblings-the-one-relationship-that-is-stored): the validator refuses a stated
sibling link between two people who already share a recorded parent, so the field can only
hold a sibship the links cannot derive. Where there is no first copy, there is no second
copy to drift from it.

The prose body is for reasoning, evidence and frontiers — the things that do not fit a
field. It is never a second copy of one.

## A link is a fact, so it carries its own confidence

`father`, `mother` and each entry in `spouses` may be written either as a bare id or as a
block with `confidence`, `source` and `note`. The scalar is not a legacy form: 646 of this
tree's links are simply known, and a three-line block to say so would add two thousand
lines of ceremony to 329 records for no fact gained.

The vocabulary is **the same one a person carries**, because it is the same question asked
of a different object — how well is this known. On a person it grades their own facts; on a
link it grades whether the two ends really belong together, and a parent documented to the
day can still be the wrong parent. One code is added for links, `asm` (assumed), and one is
refused: `unk` means "not researched yet", which is a state a person can be in and a link
cannot — a link whose existence is unknown is an absent link.

Two consequences worth stating separately:

- **An unqualified link states no confidence and does not inherit the person's.** The first
  draft inherited, which reads well and invents a grade no source gave. It also broke the
  marriage invariant below: a marriage is one link written on two records, so inheriting
  made his `doc` and her `sup` disagree about the same act.
- **`asm` links are invisible to the scorer**, so the tree's own guesses can never be
  counted as one of the two independent identifiers that licenses the next graft. That is
  what makes drawing one survivable; see [evidence § 4a](method/evidence.md).

In memory there is exactly one shape — `load_person` normalises the scalar into a block,
because `if p.get("father")` is truthy for both and `p["father"] == pid` silently goes
False against a dict, so a missed reader would not raise, it would just stop finding
parents. Read links through `parent_id`, `link_of` and `edge_confidence`, never off the
field.

## `siblings` — the one relationship that is stored

Siblinghood is derived from shared parents wherever it can be. It cannot be derived when an
act names two people as brother and sister and names no parent either of them can be
grafted to — and that case had no home at all. `vanalderweireldt_antoine_1780` states it in its own prose:
a probable elder sister, named by a third act giving the same parent pair, given up because
*"she cannot be linked as a sibling while the parents themselves are only a frontier"*.

So `siblings` is a list of links carrying the same `confidence`/`source`/`note` as any
other, with three rules:

- **It may not state what the tree derives.** A stated link between two people who already
  share a recorded parent is an error. This is the whole fence: the field holds only what
  the parent links cannot say, so it is not a second copy of anything.
- **It is mutual and agrees field for field**, like a marriage. Siblinghood is symmetric;
  a one-sided entry makes the tree answer differently depending on whose record is read.
- **It needs an `id`, not a name.** Unlike a spouse — a spouse with no record still belongs
  on the card as a name, but a sibling with no record connects nothing in the graph, which
  is the only reason to state one.

### The parent nobody could name

Downstream, the kinship engine gives each stated sibship **one anonymous shared parent**,
derived on load and written nowhere. That is the honest reading of the fact — the act says
these two share a parent it could not identify — and it means every relation past the pair
falls out instead of being special-cased: siblings read as siblings, their children as
first cousins, the index counts them blood (objective 2). Union-find over the stated links,
so A–B and B–C are one sibship rather than two overlapping ones.

Two consequences worth stating:

- A stated sibship never reads as **half-**sibling. Sharing one derived parent means the
  other is known to differ; sharing the anonymous one means nothing is known about it, and
  "half-brother" would assert more than the act did.
- The arch on the relations tab draws that apex as an **unnamed dashed card**. It is a
  position the records require and no record fills, and giving it a name it does not have
  is what the whole model exists to prevent.

## Invariants the validator enforces

| Invariant | Why |
|---|---|
| `father`/`mother` are ids of real person files | The vertical link |
| A link's `confidence` is one of `doc`/`sup`/`fam`/`asm`, and its `source` resolves | A link is a fact and is evidenced like one |
| An `asm` link states what it rests on | An assumption nobody explained cannot be checked by anyone later |
| A stated `siblings` link is mutual, and never states a sibship the parent links derive | The one stored relationship, fenced to the case with nothing to duplicate |
| **Marriage is mutual** — if A lists B, B lists A | Lets the tree be walked sideways |
| **A shared child proves a couple** — `father: A` + `mother: B` obliges each to list the other | Lets the tree be built *downwards* without losing branches |
| Every referenced person has their own file | No one exists only as a string in someone else's note |
| Every citation resolves to `research/sources.json` | A claim with no citation is not a claim |
| Every artifact's `sha256`/`bytes` recompute correctly | Evidence cannot change under a citation |
| Generated files are not stale — the bundle, `index.html`'s counts, **and the rendered docs** | Old data cannot reach the site |
| Demographic plausibility | The arithmetic signature of a graft off by a generation |

## Ids

`<surname>_<given>_<birthyear>` — lowercase ASCII, particles folded in, so "Van den Bemden"
is `vandenbemden` and a family is one prefix. **Surname first**, because the point of an id
here is finding something by hand: the directory listing sorts into families, and
`ls data/people | grep dekeyser` is a line of descent. The first given name only — "Adriana
Theresia Judoca Sabbe" is `sabbe_adriana_1703`, and the disambiguation the rest would buy is
already bought by the year.

The year is `point_year`, so it appears only where the record *asserts* one: `<1727` bounds
a birth without stating it, and an id ending `_1727` would be claiming more than the record.
152 people have no year in their id for that reason. A numeric suffix breaks a genuine
clash; across 537 people there are currently none.

Renaming breaks every reference — 1925 wikilinks, 444 log entries, 35 artifact records, two
config files — so it is done by machine or not at all:

```
uv run tools/rename_ids.py plan      what would change, writing nothing
uv run tools/rename_ids.py apply     all of it, then a check that nothing dangles
```

It deliberately never rewrites prose. 55 of the old ids were also ordinary words —
`alphonsus` was an id and a forename, `bossin` an id and a surname — so a text substitution
would have corrupted the sentences describing the evidence while looking like it worked.
Only exact structured positions and `[[…]]` links are touched, and anything left pointing at
a dead id is reported rather than guessed at.

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
   from a forename. *(Nobody is currently unknown: every person who is nobody's parent
   states it.)*
3. **A marriage that ended in death has no end date**, because it is derivable from the two
   death dates and inventing a field for it would invite recording a guess. Only `divorced`
   is stored. If that derivation is ever wanted on the page, derive it.
4. **Step-relations are unnamed on purpose.** `relationBetween` goes blood first, then
   exactly one marriage step, then stops — so a stepmother reads as "X married Y, who is
   Z's father" rather than "stepmother", and a step-sibling reads as no connection. Beyond
   one step the wording stops meaning anything reliable, and a wrong in-law label is the
   same class of error as a wrong graft: unfalsifiable prose that reads as fact.
5. **The veto rule is stated in three places** — the scorer, a SQL pre-filter and the
   validator. Deliberate, and the reasoning is in
   [Record linkage](method/linkage.md#the-veto-rule-lives-in-three-places-and-that-is-a-cost-being-paid-on-purpose).
