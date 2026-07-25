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

Content and presentation are kept apart: everything factual lives in `data/`, and
nothing in `assets/` contains a name or a date.

```
index.html                     landing page
Renee-Leon-family-tree.html    the interactive tree (page shell only)
data/
  people/<id>.md               one file per person — the source of truth
  people.js                    the list of person ids to load
  branches.js                  default source citation per surname branch
  lineages.js                  the four surname chains in the "Lineages" tab
  groups.js                    optional headings for the "Index" tab
  meta.js                      root person(s), confidence labels, footer text
  bundle.js                    all of the above in one file — generated
assets/
  css/tree.css                 styling for the tree page
  css/site.css                 styling for the landing page
  js/core.js                   the FamilyTree namespace and the data loader
  js/kinship.js                relationships, children, source resolution
  js/render.js                 records → markup
  js/ui.js                     theme switch, hover card, tabs
  js/main.js                   wires it together
docs/research-log.md           what's documented, what's inferred, what to pull next
tools/lib/                     shared loader, frontmatter parser, date grammar
tools/build.mjs                validates, then writes the generated files
tools/check-data.mjs           validates the data files
tools/export-gedcom.mjs        writes the GEDCOM export
exports/family-tree.ged        the tree in GEDCOM 7 — generated, not edited
archive/                       superseded drafts, not part of the site
```

No dependencies, and nothing is compiled — the files are served exactly as they are.
There is one generation step, `node tools/build.mjs`, which concatenates `data/` into
`data/bundle.js` and refreshes the GEDCOM export. The page reads the bundle so it makes
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

`source` is optional — leave it out and the person inherits the default citation for
their `branch` from `branches.js`.

Write plain text, not HTML: `&` and `é`, not `&amp;` and `&eacute;`. The renderer
escapes on the way out.

## The Index

Everyone is sorted into **Ancestors** (the direct line above the root), **Blood
relatives** (related, but off that line) and **Others** (married in, or not yet
connected). Those three are worked out from the links, so adding someone to the data
is all it takes for them to appear — there is no second list to keep in step.

`data/groups.js` no longer decides who appears, only what the sub-headings are called:
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

GitHub Pages serves these files with `cache-control: max-age=600`, so a phone or
browser that has already opened the page can keep showing the old version for up
to ten minutes. That is long enough to look like a change didn't work.

Every stylesheet and script in `Renee-Leon-family-tree.html` is referenced with a
`?v=N` stamp, `data/bundle.js` included. **Bump that number** — a find-and-replace of
`?v=7` to `?v=8` across the page — and every visitor gets the new version on their next
load rather than up to ten minutes later. It only matters when you want the change
visible immediately; forgetting it just means the old ten-minute wait.

## Why the generated bundle is `.js` and not `.json`

So that opening the HTML from disk works. Browsers block `fetch()` and ES modules on
`file://` URLs, but they still load ordinary `<script>` tags — so `data/bundle.js` is a
script that registers itself with `FamilyTree.person({…})` rather than JSON that has to
be fetched. That one constraint is why the whole site works by double-clicking a file
with no server and no network.

The person records themselves are Markdown, which a browser cannot read at all. That is
what the build step is for: it turns them into the bundle. Keeping the authored format
and the delivered format separate is what lets the records be pleasant to write and
review in git while the page still loads in one request.

The remaining config files (`people.js`, `meta.js`, `branches.js`, `lineages.js`,
`groups.js`) stay `.js` because they are small, rarely edited, and go into the bundle
verbatim.

## A note on `archive/`

`archive/2026-07-21-bundervoet-dekeyser-draft.html` is an earlier version of the tree,
kept for reference only. Its De Keyser line is **superseded**: it has Roland's father as
Gustaaf Audomarus Dekeyser (b. 1917), son of Camillius Dekeyser × Maria Justina Pollet.
Cosette has since confirmed that Jerome Dekeyser ❦ Léonie Paelinck are Roland's
grandparents, which rules that reading out. The current tree is the one to trust.
