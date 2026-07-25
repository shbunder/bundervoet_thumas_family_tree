# The search strategy

Three files carry it:

| | |
|---|---|
| `research/sources.json` | **sites** we can search, and the **pages** inside them |
| `research/searches.jsonl` | what was searched, where, and how it went |
| `docs/sources.md` | the readable view — generated, don't edit it |

## Why the log exists

The misses are the point. A pass that records only its finds leaves the next pass to
re-walk every dead end, and an unattended loop will do that forever. "AGATHA is
exhausted for Édouard's parentage" is a real finding — it took a full sweep to
establish — and it belongs somewhere queryable rather than buried in prose.

## Sites and pages

Everything is recorded at two levels, because they answer different questions.

A **site** is a base venue — `geneanet`, `agatha`, `familysearch`. A **page** is
something specific inside it: a member tree, a collection, a single act. *"Have we tried
Geneanet for this person at all?"* and *"which pages have ever yielded anything?"* need
different answers, and a flat list gives neither.

```
node tools/research.mjs sources    the registry: sites, then pages grouped under them
node tools/research.mjs yield      which sites and pages actually pay off
```

`yield` is the one to read before choosing where to look. It shows hit/miss/ambiguous/
blocked per site, every page that has ever produced something and what, and — most
useful — the sites never searched at all and the pages registered but not yet
productive.

## Logging a search

Before searching for someone, ask what has already been tried:

```
node tools/research.mjs tried edouard_dk     what was tried, what it found, why it failed
node tools/research.mjs untried edouard_dk   sites and pages not yet used on them,
                                             pages with a track record listed first
```

After searching, record it — **hit or miss**:

```
node tools/research.mjs log --person edouard_dk --site agatha --goal parents \
     --result miss --query "Analyses van akten — Eduardus de Keyser" \
     --why "names only Eduardus and Louisa, never the grandparents; his parents are
            only in the 1901 marriage act, which is not indexed here"
```

Add `--page` when the search was against a specific tree or document
(`--site geneanet --page tree-isavdw`). `--artifact` takes a path under `docs/sources/`
for a saved scan — save the image for anything that breaks a wall, because a URL behind
a login is not reproducible for anyone else.

## Saying how it went

`--result` is one of four, and the distinction matters more than hit-versus-fail:

| | |
|---|---|
| `hit` | found what was wanted |
| `miss` | searched properly, nothing there |
| `ambiguous` | found something, not enough to prove it |
| `blocked` | never reached the material — login, paywall, spend cap |

`ambiguous` is a real find that is not proof. The Van Craenenbroeck trunk is the model:
right surname, right village, right milieu, but the tree stops above Anna's generation,
so it is recorded and **not grafted**. `blocked` is the one result that means *try this
again* — nothing was read, so nothing is exhausted.

Then say what happened, and the tool insists on it:

- a **hit** requires `--found` — what it actually gave you;
- anything else requires `--why` — whether it is worth another go.

"Miss" on its own tells the next pass nothing. *"191 hits, none born 1876"*, *"wrong
region — Pajottenland, not Zaventem"* and *"hit the monthly fetch cap"* point at three
completely different next moves.

## New sources

Registering a source is not paperwork — a venue that gets searched but never registered
is one the next pass cannot know about, and the `untried` list silently under-reports.
So `research.mjs log` **refuses an unregistered source**, which forces the registry to
stay complete.

When a search turns up somewhere new, register it before logging against it. A whole new
venue goes in `sites`; a tree or document inside one already listed goes in `pages`,
naming its site:

```json
{
  "id": "tree-someone",
  "site": "geneanet",
  "kind": "tree",
  "title": "someone (Real Name)",
  "url": "https://gw.geneanet.org/someone",
  "covers": "which family and which region",
  "yielded": "what it actually gave — null until it gives something",
  "note": "what it is sourced to, and where it stops"
}
```

Sites take `kind` (`archive` · `index` · `obituary` · `cemetery` · `family` · `web`) and
`access` (`open` · `login` · `paywall` · `offline` · `mixed` — how to reach it, not a
judgement of its worth). Pages take `kind` (`tree` · `record` · `collection` ·
`index-page`) and `yielded`. A `record` is a specific document, and also takes
`confidence` and ideally an `artifact`.

Keep `yielded` current — it is what `yield` ranks on, and a page nobody records a result
for looks unproductive whether or not it is.

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
