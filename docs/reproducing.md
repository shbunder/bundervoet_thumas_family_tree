# Reproducing this

The repository is designed to be cloned and run by someone who is not the author, on a
different family, in a different region.

## Requirements

[uv](https://docs.astral.sh/uv/), and nothing else. `uv run` fetches the interpreter on
first use.

`pyproject.toml` declares **no runtime dependencies**, deliberately. The frontmatter
parser, the date grammar, the GEDCOM writer and the Open Archives client are all standard
library, because a dependency is a thing that has to still resolve in ten years for the
tree to remain readable.

## Getting started

```bash
git clone <repo> && cd family-tree
uv run tools/check_data.py      # validate — should be green on a fresh clone
uv run tools/build.py           # regenerate the bundle and the GEDCOM
open index.html                 # the site, straight off disk
```

## The command surface

```bash
# Validate and generate
uv run tools/build.py                       # validate, then regenerate everything derived
uv run tools/check_data.py                  # validate only (green before every commit)

# Decide what to work on
uv run tools/research.py frontiers          # the ranked queue: value × P(resolvable) ÷ cost
uv run tools/research.py acts               # which held act answers the most frontiers
uv run tools/research.py tried <person>     # what was searched, found, and why it failed
uv run tools/research.py untried <person>   # venues not yet attempted
uv run tools/research.py yield              # which sites, pages and methods pay off
uv run tools/research.py stale              # misses a venue has since outgrown
uv run tools/research.py children           # unrecorded children of couples we hold — objective 2
uv run tools/research.py components         # disconnected families
uv run tools/research.py collapse           # where the tree folds back on itself

# Harvest and link
uv run tools/harvest.py frontiers           # pull the acts the queue is asking for
uv run tools/harvest.py surname Bundervoet  # every Belgian record for one surname
uv run tools/harvest.py place Oostende      # every Belgian record for one commune
uv run tools/harvest.py status              # what is held, and what is missing
uv run tools/link.py <person>               # what the held acts say about them
uv run tools/identify.py "<name>" --birth … # is this person already in the tree?
uv run tools/verify_all.py                  # re-check every held record against the corpus

# Measure
uv run tools/evaluate.py label <person> <ref> --match|--nonmatch --why "…"
uv run tools/evaluate.py report             # precision, recall, and every disagreement
uv run tools/evaluate.py sweep              # what moving the thresholds would cost

# Test and document
uv run --group dev pytest
uv run --group docs mkdocs serve            # this documentation, live
```

## Reproducing the corpus

`research/harvest/` is **gitignored** — it is re-fetchable open data that grows without
limit. `research/harvest/manifest.json` **is** committed, and it records the exact query
behind every harvest, so the corpus can be rebuilt from the repository alone:

```bash
uv run tools/harvest.py status     # shows what the manifest expects and what is held
```

A harvest that hit its cap is recorded as `PARTIAL`, with the command to complete it. A
capped harvest that looked complete would be the corpus equivalent of an unlogged miss.

## Adapting it to another family or region

The parts that are specific, and what to change:

| What | Where | Note |
|---|---|---|
| The roots | `data/meta.json` | Takes a list — a forest is fine |
| Surname branches and lineages | `data/branches.json`, `data/lineages.json` | |
| Page wording | `site/labels.json` | Presentation only; carries no facts |
| Venue registry | `research/sources.json` | Sites and pages, with what each has yielded |
| Phonetic folding | `familytree/match.py` | **Tuned to Flemish.** See below |
| Role vocabulary | `familytree/corpus.py` | Dutch role labels from Belgian/Dutch archives |

!!! danger "The phonetics are not portable"
    The folding rules in `match.py` encode Flemish orthographic drift — `ij→i`, `sch→s`,
    `ae→a`, terminal `dt→t`. They are deliberately conservative because **over-folding
    merges families, and a merged family is the failure this project is built to avoid.**

    Applied to another language's records they will either do nothing or do harm. If you
    adapt them, pin both directions in the test suite as
    `tools/tests/test_tools.py` does: the variants that *must* fold, and the distinct
    families that must *not*.

Open Archives covers the Netherlands, Belgium and France. Outside that, `harvest.py`
needs a different client, but `corpus.py`'s event model and everything above it does not
care where the acts came from.

## Layout

```
data/people/<id>.md            source of truth: frontmatter + prose
data/artifacts/<id>.*          a saved primary document + its record
research/sources.json          the venue registry
research/searches.jsonl        the search log — append-only, hits and misses
research/labels.jsonl          the gold standard — verifier rulings as labelled pairs
research/harvest/              the corpus (gitignored; manifest.json is committed)
docs/                          this documentation
tools/familytree/              the shared library
tools/*.py                     the commands
dist/bundle.js                 GENERATED — what the page loads
dist/docs/                     GENERATED — this site
exports/family-tree.ged        GENERATED — GEDCOM 7
assets/                        presentation only — no names, no dates
```

Three things are kept apart because they change for different reasons: **`data/` is the
only place a name or a date may appear**, `site/` is wording the page shows and cannot
change what the tree claims, and `assets/` contains neither.

## Licensing

- **Code** (`tools/`, `assets/`) — MIT.
- **Data and documentation** (`data/`, `docs/`, `research/`) — CC BY 4.0.

Harvested material from Open Archives remains under its own terms and is not
redistributed here; only the manifest of queries is, which is why the corpus is
gitignored.
