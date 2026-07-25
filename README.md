# Family Tree of Renée & Léon Bundervoet

The family history of Renée and Léon Bundervoet — Bundervoet–De Keyser of the Flemish
coast and Thumas–Janssens of the Brussels edge, meeting in Leuven. 302 people; the
deepest documented roots reach the mid-1400s.

What the project is trying to achieve, and the rules research follows, are in
[CLAUDE.md](CLAUDE.md).

**Published at** <https://shbunder.github.io/bundervoet_thumas_family_tree/>

You can also just double-click `index.html` — it works straight off disk, with no
server and no internet connection.

## Layout

Three things are kept apart, because they change for different reasons and are
checked by different rules:

- **`data/`** — the facts. JSON and Markdown, nothing executable. A name or a date
  only ever lives here.
- **`site/`** — the wording the page shows: headings, labels, the footer. Editing it
  can never change what the tree claims.
- **`assets/`** — how it looks and behaves. Contains no names and no dates at all.

`dist/` and `exports/` are generated from those and are never edited by hand.

```
index.html                     landing page
Renee-Leon-family-tree.html    the interactive tree (page shell only)
data/                          FACTS — JSON and Markdown, nothing executable
  people/<id>.md               one file per person — the source of truth
  meta.json                    where the tree starts; the confidence codes
  branches.json                surname branch → its default source id
  lineages.json                the surname chains
site/                          PRESENTATION — the words the page shows
  labels.json                  confidence labels, Index headings, footer
assets/                        how it looks and behaves — no names, no dates
  css/tree.css                 styling for the tree page
  css/site.css                 styling for the landing page
  js/core.js                   the FamilyTree namespace and the data loader
  js/kinship.js                relationships, children, source resolution
  js/render.js                 records → markup
  js/ui.js                     theme switch, hover card, tabs
  js/main.js                   wires it together
research/                      the search state
  sources.json                 sites we can search, and the pages inside them
  searches.jsonl               what was searched, and how it went
dist/bundle.js                 GENERATED — what the browser actually loads
exports/family-tree.ged        GENERATED — the tree in GEDCOM 7
data/artifacts/                saved primary documents + a record for each
docs/research-log.md           what's documented, what's inferred, what to pull next
tools/lib/                     shared loader, frontmatter parser, date grammar
tools/build.mjs                validates, then writes the generated files
```

No dependencies, and nothing is compiled — the files are served exactly as they are.
There is one generation step, `node tools/build.mjs`, which concatenates `data/` into
`dist/bundle.js` and refreshes the GEDCOM export. The page reads the bundle so it makes
one request instead of one per person, which is what lets the tree grow past a few
hundred people. Both generated files are committed, so a clone still opens off disk and
GitHub Pages needs nothing but the repo.

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
branch: DeKeyser
father: desiderius_dk
mother: mtheresia_vandenbroeck
spouses:
  - id: louise_bocklandt
    name: Louise Marie Bocklandt
    detail: m. 4 May 1901; divorced ~1923
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

`occupation` is what someone did ("metser (mason)"), kept in the language of the record
with a gloss. `nickname` is what they were called. Neither ever holds a relationship.

`sex` is `"f"` or `"m"`, and is only needed when it cannot be worked out from the links:
being recorded as someone's `father` or `mother` already settles it. It matters because
relations are named from it — without it the tree says "sibling" rather than "sister".
Fill it in only from what a record actually says, never from a forename.

`spouses` is a list, oldest marriage first. Each entry needs a `name`; give it an `id`
too when that spouse has a record, and the tree becomes walkable sideways. Two rules the
validator enforces, both so the tree can be built *downwards* as well as up:

- **Marriage is mutual.** If A lists B as a spouse, B must list A.
- **A shared child proves a couple.** If a record has `father: A` and `mother: B`, then
  A and B must each list the other.

`sources` is a list of ids from `research/sources.json` — `tree-isavdw`, `S1`. The
records cite the registry rather than describing it, so "Geneanet tree isavdw
(Rijksarchief scans)" is written once, in one place, instead of on 107 people. The
validator rejects an id that isn't registered. Leave it out and the person inherits
the default citation for their `branch`.

`line` names which Index heading the person belongs under, keyed to `groups.js`. The
person says it once; there is no membership list anywhere.

Write plain text, not HTML: `&` and `é`, not `&amp;` and `&eacute;`. The renderer
escapes on the way out.

## The Index

Everyone is sorted into **Ancestors** (the direct line above the root), **Blood
relatives** (related, but off that line) and **Others** (married in, or not yet
connected). Those three are worked out from the links, so adding someone to the data
is all it takes for them to appear — there is no second list to keep in step.

`site/labels.json` no longer decides who appears, only what the sub-headings are called:
"Bostyn & Cappaert (Marcel's mother)" reads better than the bare branch name. Anyone it
doesn't mention is filed under their `branch`, which is why nobody can go missing.

The same tab answers **how any two people are related** — pick two names and it gives
the relation and the ancestor they share. It works from the lowest common ancestor of
the pair rather than from the root, so it can relate anyone to anyone, and it falls
back to one step through marriage when there is no blood link.

## The GEDCOM export

`exports/family-tree.ged` is the whole tree in **GEDCOM 7** — the open interchange
format genealogy programs read. Import it into Gramps, Geneanet, Ancestry or
MyHeritage, or hand it to anything that wants the data without parsing `.js`.

GEDCOM 7 rather than the older 5.5.1 because it is UTF-8 throughout (these records are
full of `é` and `ë`) and has no line-length limit, so the long research notes survive
whole instead of being chopped into continuations.

It is generated — edit `data/people/` and re-run `node tools/export-gedcom.mjs`.

The exporter will not write a file that does not read back as the same tree: it
reparses its own output, rebuilds every parent and marriage link from that alone, and
stops if any of them disagree with the source records. It also prints what GEDCOM
could not carry rather than guessing — a date like "a few years ago" stays as a note
instead of becoming a year.

## Making a change show up straight away

GitHub Pages serves these files with `cache-control: max-age=600`, so a browser that
has already opened the page can show the old version for up to ten minutes — long
enough to look like a change didn't work.

Every stylesheet and script is referenced with a `?v=` stamp, and `node tools/build.mjs`
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
