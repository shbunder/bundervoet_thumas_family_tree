# Family Tree of Renée & Léon Bundervoet

The family history of Renée and Léon Bundervoet — Bundervoet–De Keyser of the Flemish
coast and Thumas–Janssens of the Brussels edge, meeting in Leuven. 128 people; the
deepest documented roots reach the early 1600s.

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
  groups.js                    how the "Index" tab is grouped and ordered
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
archive/                       superseded drafts, not part of the site
```

No build step and no dependencies — the files are served exactly as they are.

## A person file

```js
FamilyTree.person({
  id: "marcel_b",
  name: "Marcel Bundervoet",
  dates: "1933–2015 · Oostende",
  confidence: "doc",
  branch: "Bundervoet",
  father: "alphonsus",
  mother: "elodia",
  spouse: { name: "Rosette Van Iseghem, later Francine Bisschop" },
  source: "Memorial card (Uitvaartcentrum Raes, Oostende) + family",
  note: "Confirmed by his memorial card, which named the Bostyn family…",
});
```

Only `id`, `name` and `confidence` are required. `father` and `mother` are the ids of
other person files — that's how the tree is linked together; everything else (who
someone's children are, whether they're a great-great-grandparent, whether they're an
aunt) is worked out from those links when the page loads.

`confidence` drives the colour coding: `doc` documented record · `fam` family knowledge ·
`sup` strongly supported · `unk` unknown, still to research.

`source` is optional — leave it out and the person inherits the default citation for
their `branch` from `branches.js`.

Write plain text, not HTML: use `&` and `é`, not `&amp;` and `&eacute;`. The renderer
escapes everything on the way out.

## Adding or changing someone

1. Add or edit `data/people/<id>.js`.
2. If the person is new, add the id to `data/people.js`, and to a group in
   `data/groups.js` so they show up in the Index tab.
3. Run `node tools/check-data.mjs` — it catches syntax errors, typo'd parent ids,
   unknown branches, people missing from the list, and circular ancestry.
4. Commit. GitHub Pages picks it up; there is no build to run.

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
