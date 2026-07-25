# Family Tree of Renée & Léon Bundervoet

The family history of Renée and Léon Bundervoet — Bundervoet–De Keyser of the Flemish
coast and Thumas–Janssens of the Brussels edge, meeting in Leuven. 301 people; the
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
  people/<id>.js               one file per person — the source of truth
  people.js                    the list of person ids to load
  branches.js                  default source citation per surname branch
  lineages.js                  the four surname chains in the "Lineages" tab
  groups.js                    optional headings for the "Index" tab
  meta.js                      root person, confidence labels, footer text
assets/
  css/tree.css                 styling for the tree page
  css/site.css                 styling for the landing page
  js/core.js                   the FamilyTree namespace and the data loader
  js/kinship.js                relationships, children, source resolution
  js/render.js                 records → markup
  js/ui.js                     theme switch, hover card, tabs
  js/main.js                   wires it together
docs/research-log.md           what's documented, what's inferred, what to pull next
tools/check-data.mjs           validates the data files
tools/export-gedcom.mjs        writes the GEDCOM export
exports/family-tree.ged        the tree in GEDCOM 7 — generated, not edited
archive/                       superseded drafts, not part of the site
```

No build step and no dependencies — the files are served exactly as they are.

## A person file

```js
FamilyTree.person({
  id: "marcel_b",
  name: "Marcel Henri Bundervoet",
  dates: "1933–2015 · Oostende",
  confidence: "doc",
  branch: "Bundervoet",
  father: "alphonsus",
  mother: "elodia",
  spouses: [
    { id: "rosette", name: "Rosette Van Iseghem" },
    { name: "Francine Bisschop", detail: "later" },
  ],
  source: "Memorial card (Uitvaartcentrum Raes, Oostende) + family",
  note: "Confirmed by his memorial card, which named the Bostyn family…",
});
```

Only `id`, `name` and `confidence` are required. `father` and `mother` are the ids of
other person files — that's how the tree is linked together; everything else (who
someone's children are, whether they're a great-great-grandparent, whether they're an
aunt) is worked out from those links when the page loads.

`spouses` is a list, oldest marriage first, because people remarried. Each entry needs
a `name`; give it an `id` too when that spouse has a record of their own, and the tree
becomes walkable sideways — you can climb from someone into their spouse's family
rather than hitting a dead end. An entry with no `id` is a person who is referenced but
not yet written up. `detail` is free text for the marriage itself ("Oostkamp, 30 Sep 1863").

Two rules the validator enforces, both there so the tree can be built *downwards* as
well as up:

- **Marriage is mutual.** If A lists B as a spouse, B must list A.
- **A shared child proves a couple.** If a record has `father: A` and `mother: B`, then
  A and B must each list the other as a spouse.

`confidence` drives the colour coding: `doc` documented record · `fam` family knowledge ·
`sup` strongly supported · `unk` unknown, still to research.

`occupation` is what someone did ("metser (mason)", "bierverkoopster (beer seller)") —
kept in the language of the record with a gloss, since that is how it was written down.
`nickname` is what they were called ("Meme Lenie"). Neither ever holds a relationship:
"Ronny's sister" is not a fact about a person, it is a fact about two people, and the
tree works it out from the links.

`sex` is `"f"` or `"m"`, and is only needed when it can't be worked out from the links:
being recorded as someone's `father` or `mother` already settles it. It matters because
relations are named from it — without it the tree says "sibling" rather than "sister".
Fill it in only from what a record actually says (a note calling someone "Roland's
sister", a role of "wife"), never from a forename.

`born` and `died` are optional explicit date fields (e.g. `born: "12 Nov 1876 · Hamme-Merchtem"`),
carried alongside the free-text `dates` string that drives the display. They are filled in for
everyone with a known date, so birth and death are available as structured data.

`source` is optional — leave it out and the person inherits the default citation for
their `branch` from `branches.js`.

Write plain text, not HTML: use `&` and `é`, not `&amp;` and `&eacute;`. The renderer
escapes everything on the way out.

## Adding or changing someone

1. Add or edit `data/people/<id>.js`.
2. If the person is new, add the id to `data/people.js`. That is enough to put them
   in the Index — it is grouped from the links, not from a list.
3. Run `node tools/check-data.mjs` — it catches syntax errors, typo'd parent ids,
   unknown branches, people missing from the list, one-sided marriages, and
   circular ancestry.
4. Run `node tools/export-gedcom.mjs` to refresh `exports/family-tree.ged`.
5. Commit. GitHub Pages picks it up; there is no build to run.

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
instead of becoming a year, and a `role` of "Uncle (Shaun's brother)" is not filed as
an occupation.

## Making a change show up straight away

GitHub Pages serves these files with `cache-control: max-age=600`, so a phone or
browser that has already opened the page can keep showing the old version for up
to ten minutes. That is long enough to look like a change didn't work.

Every stylesheet and script in `Renee-Leon-family-tree.html` is referenced with a
`?v=N` stamp, and `core.js` carries the same stamp onto the person files it loads.
**Bump that number** — a find-and-replace of `?v=1` to `?v=2` across the page —
and every visitor gets the new version on their next load rather than up to ten
minutes later. It only matters when you want the change visible immediately;
forgetting it just means the old ten-minute wait.

## Why the data files are `.js` and not `.json`

So that opening the HTML from disk works. Browsers block `fetch()` and ES modules on
`file://` URLs, but they still load ordinary `<script>` tags — so each person file is a
script that registers itself with `FamilyTree.person({…})` rather than JSON that has to
be fetched. The content is the same either way, and you get comments and trailing commas
for free.

## A note on `archive/`

`archive/2026-07-21-bundervoet-dekeyser-draft.html` is an earlier version of the tree,
kept for reference only. Its De Keyser line is **superseded**: it has Roland's father as
Gustaaf Audomarus Dekeyser (b. 1917), son of Camillius Dekeyser × Maria Justina Pollet.
Cosette has since confirmed that Jerome Dekeyser ❦ Léonie Paelinck are Roland's
grandparents, which rules that reading out. The current tree is the one to trust.
