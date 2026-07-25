# The search strategy

Three files carry it:

| | |
|---|---|
| `research/sources.json` | everywhere we can look, and every document cited |
| `research/searches.jsonl` | what was searched, where, and what came back |
| `docs/sources.md` | the readable view — generated, don't edit it |

## Why the log exists

The misses are the point. A pass that records only its finds leaves the next pass to
re-walk every dead end, and an unattended loop will do that forever. "AGATHA is
exhausted for Édouard's parentage" is a real finding — it took a full sweep to
establish — and it belongs somewhere queryable rather than buried in prose.

Before searching for someone, ask what has already been tried:

```
node tools/research.mjs tried edouard_dk     what has been tried, and what came back
node tools/research.mjs untried edouard_dk   registered sources not yet used on them
```

After searching, record it — **hit or miss**:

```
node tools/research.mjs log --person edouard_dk --source agatha --goal parents \
     --result miss --query "Analyses van akten — Eduardus de Keyser" \
     --note "names only Eduardus and Louisa, never the grandparents"
```

`--result` is one of **hit** · **miss** · **ambiguous** · **blocked**. `ambiguous` is for
a strong lead that is not proof — the Van Craenenbroeck trunk is the model: right
surname, right village, right milieu, but the tree stops above Anna's generation, so
nothing was grafted. `blocked` is for a login wall, a paywall, a rate limit or a spend
cap: not searched, so not exhausted, and worth retrying.

`--artifact` takes a path under `docs/sources/` for a saved scan. Save the image for
anything that breaks a wall; a URL to a logged-in archive is not reproducible.

## New sources

Registering a source is not paperwork — a venue that gets searched but never registered
is one the next pass cannot know about, and the `untried` list silently under-reports.
So `research.mjs log` **refuses an unregistered source**, which forces the registry to
stay complete.

When a search turns up somewhere new — another member tree, a commune index, a
parish-register collection, a cemetery database — add it to `research/sources.json`
before logging against it:

```json
{
  "id": "tree-someone",
  "kind": "tree",
  "title": "Geneanet tree someone (Real Name)",
  "url": "https://gw.geneanet.org/someone",
  "access": "open",
  "covers": "which family and which region",
  "note": "what it is sourced to, and where it stops"
}
```

`kind` is `archive` · `index` · `tree` · `obituary` · `cemetery` · `record` · `family`.
`access` is `open` · `login` · `paywall` · `offline` · `mixed` — how to reach it, which
is not a judgement about how good it is. A `record` is a specific document that proves
something, and takes `proves`, `confidence` and ideally an `artifact`.

`node tools/build.mjs` validates the registry and the log together and regenerates
`docs/sources.md`, so the readable list cannot drift from the data.

## What works, from the passes so far

- **Marriage acts name both spouses' parents.** They are the richest single record.
  Prioritise them over birth acts.
- **Push the rarer surname.** Both breakthroughs came this way: the Bocklandt line
  opened the Dekeyser branch, and Van Craenenbroeck located a family that Janssens
  never could. A common surname with no anchor is not searchable.
- **Find a tree that cites the Rijksarchief zoekrobot** and transcribed the parents —
  `isavdw` and `vxnce13` are the models. Open a candidate's fiche in each tree until one
  shows an "Ouders" section.
- **FamilySearch is deeper than AGATHA or Ancestry** for Belgian civil registration.
  It broke a wall the other two could not. Try it before concluding an act is unindexed.
- **Memorial cards (bidprentjes)** name parents and children and sit outside the
  civil-registration publicity rules — the key to 20th-century walls.
- **Match on region, not surname.** The Van Craenenbroeck and Janssens false positives
  were all right-name/wrong-province. Rejecting them cost a pass; the log now records
  that so it costs nothing next time.

## Browser access

The archives that matter most need a logged-in session — Geneanet, FamilySearch,
Ancestry all gate their record images. `WebFetch` cannot reach those, which is why
several passes stopped at "login-walled".

`.mcp.json` in the project root configures the **chrome-devtools-mcp** server to attach
to a Chrome you are already signed into, rather than launching a clean one:

```
# start Chrome with remote debugging, then log in to the archives once
/Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome \
  --remote-debugging-port=9222 --user-data-dir=$HOME/.chrome-genealogy
```

Then restart Claude Code so it picks up the server. Sessions persist in that profile,
so the login is a one-off.

Two things to keep in mind while it runs. Archives rate-limit and will suspend an
account that hammers them — pace requests, because losing the session costs far more
than the delay. And a page behind a login is not reproducible for anyone else, so save
the scan to `docs/sources/` and cite the local file alongside the URL.
