# Family Tree of Renée & Léon Bundervoet

The family history of Renée and Léon Bundervoet — Bundervoet–De Keyser of the Flemish
coast and Thumas–Janssens of the Brussels edge, meeting in Leuven. 307 people. The tree
reaches back to the 1440s, and to the 1640s on records actually read in an archive —
the older generations rest on other people's trees and are marked as such.

What the project is trying to achieve, and the rules research follows, are in
[CLAUDE.md](CLAUDE.md). **The method — why those rules exist, the prior work it builds
on, and the plan for scaling past a few thousand people — is documented in
[`docs/`](docs/index.md)**, rendered with `uv run --group docs mkdocs serve`:

| | |
|---|---|
| [Overview](docs/index.md) | The problem, and the three commitments the design rests on |
| [Prior work](docs/prior-work.md) | BALSAC, LINKS, the Antwerp COR\* database, Fellegi–Sunter, Splink, LLM transcription — what is borrowed and from whom |
| [The research loop](docs/method/overview.md) | One pass, and the four agents that run it |
| [Rules of evidence](docs/method/evidence.md) | Two independent identifiers, confidence codes, what the validator enforces |
| [The corpus](docs/method/corpus.md) | Acts read as events rather than as people |
| [Record linkage](docs/method/linkage.md) | Blocking, Flemish phonetics, rarity in bits, the vetoes |
| [Verification](docs/method/verification.md) | Adversarial refutation, and the gold standard it produces |
| [Scaling to Flanders](docs/method/scaling.md) | The ordered plan, and what gives way first |
| [Reproducing this](docs/reproducing.md) | Running it, and adapting it to another family or region |

This repository is intended to be usable as a research artefact:
[CONTRIBUTING.md](CONTRIBUTING.md) states the bar for adding a person, and
[CITATION.cff](CITATION.cff) has the citation. Code is MIT; data and documentation are
CC BY 4.0 ([LICENSE-DATA](LICENSE-DATA)).

**Published at** <https://shbunder.github.io/bundervoet_thumas_family_tree/>

You can also just double-click `index.html` — it works straight off disk, with no
server and no internet connection.

## Layout

Three things are kept apart, because they change for different reasons and are
checked by different rules:

- **`data/`** — the facts. JSON and Markdown, nothing executable. A name or a date
  only ever lives here.
- **`site/`** — the wording the page shows: headings, labels, the footer, in every
  language it offers them in. Editing it can never change what the tree claims.
- **`assets/`** — how it looks and behaves. Contains no names and no dates at all.

`dist/` and `exports/` are generated from those and are never edited by hand.

The file-by-file listing is in the method docs, under
[Data model → Where everything lives](dist/docs/data-model.html). It is not repeated here:
there were three copies of it, and when `data/forenames.json` was added only two of them
learned about it.

Nothing is compiled and the site has no dependencies — the files are served exactly as
they are. There is one generation step, `uv run tools/build.py`, which turns `data/`
into `dist/bundle.js` and refreshes the GEDCOM export. The page reads the bundle so it
makes one request instead of one per person, which is what lets the tree grow past a
few hundred people. Both generated files are committed, so a clone still opens off disk
and GitHub Pages needs nothing but the repo.

The tools are Python, run through [uv](https://docs.astral.sh/uv/), which fetches the
interpreter on first use — so `uv run tools/build.py` works in a fresh clone with
nothing installed. `pyproject.toml` declares no dependencies and that is deliberate:
the frontmatter parser, the date grammar, the GEDCOM writer and the Open Archives
client are all standard library, because a dependency is something that has to still
resolve in ten years for this tree to stay readable. `uv run --group dev pytest` runs
the tests.

## A person file

`data/people/<id>.md` — strict fields on top, free prose underneath.

```markdown
---
id: edouard_dk
name: Édouard Dekeyser
sex: m
birth:
  date: 1876-11-12
  place: Hamme (Oost-Vlaanderen)
death:
  date: 1951-09-08
  place: Oostende
confidence: doc
occupation: werkman
father:
  id: desiderius_dk
  confidence: sup
mother:
  id: mtheresia_vandenbroeck
  confidence: sup
siblings:
  - id: alois_dk
    confidence: sup
spouses:
  - id: louise_bocklandt
    name: Louise Marie Bocklandt
    confidence: doc
    married: 1901-05-04
    divorced: ~1923
    detail: legitimized their two eldest children
  - id: leontine_schreel
    name: Leontine Schreel
    married: 1946-05-09
    place: Oostende
source: "PRIMARY: Oostende marriage act nr. 81, 9 May 1946 (FamilySearch)"
---

WALL BROKEN (July 2026). His own 1946 remarriage act names his parents in full…
```

Only `id`, `name` and `confidence` are required. `father` and `mother` are the ids of
other person files — that is how the tree is linked; everything else (children,
generations, whether someone is an aunt) is worked out from those links on load.

The body is the part no field can hold: what a document actually said, why an identity
was accepted or rejected, and what to pull next. It is never a second copy of a field —
a relationship written into the prose is a copy of the tree that nothing validates.

### Dates

A small fixed grammar, so dates sort and compare instead of needing to be re-read:

| | |
|---|---|
| `1876-11-12` | a day |
| `1876-11` | a month |
| `1876` | a year |
| `~1682` | about |
| `<1727` / `>1900` | before / after |
| `1575..1587` | between |

There is deliberately no syntax for "probably March". A format for a guess is an
invitation to record one — if a source did not say it, the field is absent. Where a
record says something the grammar genuinely cannot express ("a few years ago"), it goes
in `raw` and is explained in the prose rather than rounded into a year.

The display line under each name (`12 Nov 1876 Hamme – 8 Sep 1951 Oostende`) is
generated from these, so there is no hand-written copy to fall out of step.

### Other fields

`confidence` drives the colour coding: `doc` documented record · `fam` family knowledge ·
`sup` strongly supported · `unk` unknown, still to research.

### Links carry their own confidence

`father`, `mother`, `siblings` and `spouses` are **links**, and a link is a fact in its own
right. A bare id is accepted when you write one by hand:

```yaml
father: lucien_vincke
```

…but `uv run tools/build.py` writes it out in full, so records on disk always state what a
link is worth. Anything you put there yourself is kept:

```yaml
mother:
  id: ludovica_vanald
  confidence: asm
  source: agatha-diksmuide-1880-birth
  note: birth act names a Ludovica Vanalderweireldt; commune and year agree, no second identifier
```

`confidence` here is the **same vocabulary as a person's**, because it is the same
question asked of a different object: how well is this known. On a person it grades their
own facts; on a link it grades whether the two ends really belong together — and a parent
documented to the day can still be the wrong parent. One extra code, `asm` (assumed),
for a link entered on a single identifier where the rules want two. `unk` is not valid on
a link: a link whose existence is unknown is an absent link.

The generated value is the **weaker of the link's two ends** — a link between a documented
person and one known only from family testimony is not documented, because the weaker end
is what a reader would have to accept in order to accept the join. It is symmetric, so a
marriage written on two records gets the same answer from both. A sibling edge is graded on
the two parent links it rests on, not on the two people, because that is what actually makes
them siblings.

`source` is an id from `research/sources.json`, exactly like `sources` on the person. It
is what makes "every parent link cites a source" checkable at all: while the only citation
was a person-level list, nothing could say *which* source established the mother.

**An `asm` link is evidence for nothing.** The scorer cannot see it in either direction —
not as a parent, and not as a child reaching back. That is what makes it safe to draw one:
the tree's own guess can never come back as one of the two independent identifiers that
licenses the next graft. `uv run tools/research.py weak` lists every one of them, ordered
by how many people would leave the tree with it, and the page draws them red.

### `siblings` — the one relationship that is stored

Everything else about a relationship is derived; siblinghood usually is too, from shared
parents. `siblings` exists for the case the parent links cannot state at all:

```yaml
siblings:
  - id: maria_joanna_vanald
    confidence: asm
    source: rab-diksmuide-1857-death
    note: same parent pair named in three acts; the father's forename disagrees in all three
```

**Sibling edges are generated, not hand-kept.** `uv run tools/edges.py sync` writes every
derived sibship out as edges (994 of them) and `build.py` runs it; the validator then fails
on any record that disagrees with what it would write. That is what makes the redundancy
safe rather than reckless — the edges are a projection of the parent links, checked on every
build, exactly like `dist/bundle.js`. Change a parent link and the sibling edges resting on
it go stale loudly instead of quietly describing a family that changed.

A stated sibship the parent links **contradict** — both pairs fully recorded, sharing
nobody — is an error. Entries are mutual and agree field for field, like a marriage.

The case is real: `antoine_vanald` records a probable elder sister named by a third act
giving the same parent pair, and had to give the fact up — *"she cannot be linked as a
sibling while the parents themselves are only a frontier"*, because the father's forename
disagrees across all three acts.

Downstream, a stated sibship behaves as a sibship: the page derives **one anonymous shared
parent** for it — never written anywhere — so the two read as siblings, their children as
first cousins, and the index counts them blood. The arch on the relations tab draws that
apex as an unnamed dashed card, which is what it is: a position the records require and no
record fills. A stated sibship never reads as "half-", because an act calling two people
brother and sister says nothing about the *other* parent.

`occupation` is what someone did ("metser (mason)"), kept in the language of the record
with a gloss. `nickname` is what they were called. Neither ever holds a relationship.

`sex` is `"f"` or `"m"`, and is only needed when it cannot be worked out from the links:
being recorded as someone's `father` or `mother` already settles it. It matters because
relations are named from it — without it the tree says "sibling" rather than "sister".
Fill it in only from what a record actually says, never from a forename.

`spouses` is a list, oldest marriage first. Each entry needs a `name`; give it an `id`
too when that spouse has a record, and the tree becomes walkable sideways.

A marriage is an event, so it is stored like one. `married` and `divorced` take dates in
the grammar above; `place` is where the act was passed; `kind` is `partnership` for a
couple who had children without a recorded marriage, and is otherwise omitted. `detail`
is left for what none of those can hold — and only that. It may not carry a date, a
place, or which marriage in a sequence this was, because those are fields now, or are
what the list order already says.

Five rules the validator enforces:

- **Marriage is mutual.** If A lists B as a spouse, B must list A.
- **A shared child proves a couple.** If a record has `father: A` and `mother: B`, then
  A and B must each list the other.
- **One marriage, one set of facts.** The two records must give the same `kind`,
  `confidence`, `source`, `married`, `place` and `divorced`. Before this was checked, two
  records gave different places for the same wedding and whichever was read first won.
  `confidence` and `source` are in that list because a marriage is one link written on two
  records: without them the same act could be `doc` on his and `asm` on hers, and whichever
  the reader opened first would decide whether the page drew it red.
- **Oldest first.** Where both entries are dated, the list order must match them — so
  the order carries the sequence and nothing has to write "his 2nd marriage" anywhere.
- **A marriage never names a child.** Which children came from which marriage is already
  in the data: every child names its own father and mother. "1st — mother of Segerius"
  in a marriage field was a second copy of a link nothing kept in step.

Which children belong to which marriage is therefore *derived*, and the tree draws it:
someone who married twice gets one row of children per marriage, captioned with the other
parent, rather than one row that silently merges two sibships into one.

`sources` is a list of ids from `research/sources.json` — `tree-isavdw`, `S1`. The
records cite the registry rather than describing it, so "Geneanet tree isavdw
(Rijksarchief scans)" is written once, in one place, instead of on 107 people. The
validator rejects an id that isn't registered. Leave it out and the person inherits
`defaultSource` from `data/meta.json`.

`line` names which Index heading the person belongs under, keyed to `groups.js`. The
person says it once; there is no membership list anywhere.

Write plain text, not HTML: `&` and `é`, not `&amp;` and `&eacute;`. The renderer
escapes on the way out.

## The Index

Everyone in the tree, cut into groups by whichever question you ask of it. **Group by**
offers four:

| Grouping | The cards are | Derived from |
| --- | --- | --- |
| Family line | the curated headings — "Bostyn & Cappaert (Marcel's mother)" | the person's own `line` |
| First letter | A, B, C … | the folded family key, so "De Keyser", "Dekeyser" and "'t Jonck" land where you'd look |
| Century | 15th century … , plus one card for the undated | the birth date |
| Ancestor / blood / other | the direct line above the root; blood off that line; married in or unconnected | the parent and marriage links |

and **Sort by** orders inside each card: by generation (closest to the root first, the
default, and the only one of the three that tells a story), by family name, or by birth
date.

Every one of those is *derived*, which is the whole reason the controls can exist:
adding someone to `data/` files them correctly under all four groupings at once, and
there is no list anywhere that regrouping would have to rewrite. Both choices are
remembered between visits.

`site/labels.json` doesn't decide who appears, only what the family-line headings are
called. Anyone it doesn't mention is filed under "unplaced", which is why nobody can go
missing.

## Relations

Its own tab, because it answers a different question: the Index says who is in the
tree, this says **what any two of them are to each other**. Pick two names and it gives
the relation, the ancestor they share, and the route between them drawn as an arch — up
one side, across, down the other, so the shape is the argument rather than the label
being a claim.

It works from the lowest common ancestor of the pair rather than from the root, so it
can relate anyone to anyone (objective c), and it falls back to one step through
marriage when there is no blood link. It stops there: beyond one step the wording stops
meaning anything reliable, and a wrong in-law label is the same class of error as a
wrong graft.

## Two languages

The flag under the theme switch turns the page between English and Dutch. It opens in
whichever of the two the browser asks for, and remembers a choice made against that.

Switching is not a reload: the reader keeps their place, their focus, their search and
their index grouping. That is only possible because **no word is written in
`assets/`** — every one of them, down to the field labels and the relation vocabulary,
comes from `site/labels.json` through the bundle. Adding a third language is editing
that file; nothing in `assets/` would need to know.

The relation names are generated rather than listed, so they had to be translated as a
*grammar* and not as a phrasebook. Each language brings its own prefixes:
`great-grandmother` stacks one word for ever, where Dutch has `overgrootmoeder` and
then `betovergrootmoeder` before it too needs a count. Descent, aunts and nieces take
three different prefixes in Dutch (`achter-`, `oud-`, `achter-`) where English uses
`great-` for all three. Dutch cousins are numbered — `tweedegraads neef` — because
`achterneef` means both "second cousin" and "great-nephew", and a label that could be
either is the same class of error as a wrong graft.

The validator refuses a build with a hole in the table. Falling back to English is
invisible on the page, which is exactly why a build has to be the thing that notices.

## The GEDCOM export

`exports/family-tree.ged` is the whole tree in **GEDCOM 7** — the open interchange
format genealogy programs read. Import it into Gramps, Geneanet, Ancestry or
MyHeritage, or hand it to anything that wants the data without parsing `.js`.

GEDCOM 7 rather than the older 5.5.1 because it is UTF-8 throughout (these records are
full of `é` and `ë`) and has no line-length limit, so the long research notes survive
whole instead of being chopped into continuations.

It is generated — edit `data/people/` and re-run `uv run tools/export_gedcom.py`.

The exporter will not write a file that does not read back as the same tree: it
reparses its own output, rebuilds every parent and marriage link from that alone, and
stops if any of them disagree with the source records. It also prints what GEDCOM
could not carry rather than guessing — a date like "a few years ago" stays as a note
instead of becoming a year.

## Making a change show up straight away

GitHub Pages serves these files with `cache-control: max-age=600`, so a browser that
has already opened the page can show the old version for up to ten minutes — long
enough to look like a change didn't work.

Every stylesheet and script is referenced with a `?v=` stamp, and `uv run tools/build.py`
sets it to a hash of the bytes it just generated. It changes when the served files
change and not otherwise, so there is nothing to remember and nothing to bump by hand.

## Why the generated bundle is `.js` and not `.json`

So that opening the HTML from disk works. Browsers block `fetch()` and ES modules on
`file://` URLs, but they still load ordinary `<script>` tags — so `dist/bundle.js` is a
script that registers itself with `FamilyTree.person({…})` rather than JSON that has to
be fetched. That one constraint is why the whole site works by double-clicking a file
with no server and no network.

The person records themselves are Markdown, which a browser cannot read at all. That is
what the build step is for: it turns them into the bundle. Keeping the authored format
and the delivered format separate is what lets the records be pleasant to write and
review in git while the page still loads in one request.

Nothing else is JavaScript. The person records are Markdown and the config is JSON,
so `data/` can be read by any tool — `jq`, grep, another language — without running
anything. Only the generated bundle is code, and only because a browser opening a
`file://` page has no other way to load it.

## A note on `archive/`

`archive/2026-07-21-bundervoet-dekeyser-draft.html` is an earlier version of the tree,
kept for reference only. Its De Keyser line is **superseded**: it has Roland's father as
Gustaaf Audomarus Dekeyser (b. 1917), son of Camillius Dekeyser × Maria Justina Pollet.
Cosette has since confirmed that Jerome Dekeyser ❦ Léonie Paelinck are Roland's
grandparents, which rules that reading out. The current tree is the one to trust.
