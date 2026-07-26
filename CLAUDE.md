# Family Tree — project charter

Genealogy of **Renée & Léon Bundervoet** (the two children at the root). Static site,
no runtime dependencies, one generation step (`uv run tools/build.py`). ~430 people
today; the target is thousands.

The tools are Python, managed by [uv](https://docs.astral.sh/uv/) — `uv run` fetches the
interpreter and the (empty) dependency set on first use, so a clone runs with nothing
installed. `pyproject.toml` declares no dependencies on purpose: a dependency is a thing
that has to still resolve in ten years for this tree to be readable.

**This file is the operative brief: what to do, what is forbidden, which command.** It
does not explain itself — the reasoning, the prior work and the measurements are the
documentation site in `docs/` (`uv run --group docs mkdocs serve`), and every section
below links to the page that owns its "why". That split is deliberate, and it is the same
rule the data model runs on: **nothing is written down twice.** About 350 lines of this
file used to be a paraphrase of `docs/`, which cannot be diffed against the thing it
paraphrases — and it had already drifted.

Read the objectives, then find work: `uv run tools/research.py frontiers` for the ranked
queue, and [docs/research-log.md](docs/research-log.md) for how it got there.

| Start here | |
|---|---|
| [docs/index.md](docs/index.md) | the problem, and the three commitments the design rests on |
| [docs/method/overview.md](docs/method/overview.md) | the research loop, step by step |
| [docs/method/evidence.md](docs/method/evidence.md) | the rules below, one section each |
| [docs/data-model.md](docs/data-model.md) | the model, the invariants, **and where every file lives** |
| [docs/method/scaling.md](docs/method/scaling.md) | the ordered plan past a few thousand people |
| [docs/prior-work.md](docs/prior-work.md) | the literature this borrows from |

---

## Objectives

**Primary — these define "done" and rank all work:**

1. **All ancestors of Renée & Léon.** Build the tree *upwards*. Every parent link, as far
   back as records go, on every line.
2. **All blood relatives of Renée & Léon.** Build *downwards* from each ancestral couple:
   their children, their children's children. An ancestor's sibling and that sibling's
   descendants are in scope — they are blood.
3. **Connect all Bundervoets.** Build a *forest* of Bundervoet families and find the links
   between the trees. Disconnected roots are expected and legitimate here.

**Secondary — quality bar applied to every person added:**

- **a.** Gather the full life: birth date & place, death date & place, spouse(s), marriage
  date(s) & place, children, occupation, where they lived, migrations.
- **b.** Every person *referenced anywhere* gets their own record file and a place in the
  tree. No one exists only as a string inside someone else's note.
- **c.** For any two people in the index, the site can state their relation.

Priority when they conflict: 1 > 2 > 3 > a. Depth on the direct lines beats breadth.

**Stretch goal (drives architecture, not current work):** map everyone who ever lived in
Oostende. Assume every design decision will meet 10,000+ people — no hand-maintained
per-person lists, no O(n) manual curation.

---

## Non-negotiable rules

These exist because the failure mode of autonomous genealogy is **silently grafting the
wrong person**, and at scale a bad link is unfindable later. Each rule is a section in
[docs/method/evidence.md](docs/method/evidence.md), with the near-miss that produced it —
two different Hammes, two Simonne Vandewalles, the Gustaaf who was a Gustavus.

1. **Never match on name alone.** A graft needs at least two independent identifiers to
   agree — date + place, or parent names, or occupation + commune. Say which two.
2. **Record the evidence, then the fact.** Every new parent link cites a source in
   `research/sources.json`. A claim with no citation does not go in the tree.
3. **Confidence is honest, not aspirational.** `doc` = a primary act or image was actually
   read. `sup` = one member tree, unverified. `fam` = family testimony. `unk` = to
   research. Downgrading is always allowed; upgrading needs a document.
4. **A strong lead is not a link.** Record it in the person's `note` as a named frontier.
   Do not graft it. (`anna_vc` is the model for how to do this.)
5. **Never invent a field.** If an occupation or a day-level date wasn't in the source, it
   is absent, not guessed. Say "not in the reachable pages" in the log.
6. **Corrections are first-class.** When a past conclusion is wrong, retract it explicitly
   in the log with the reasoning, and fix every record it touched. §29 is the model.
7. **Log every search, especially the ones that found nothing.** Every entry states its
   `basis` — *how* the material was consulted — and every miss states its `scope`, what was
   actually covered. A miss with no extent reads as "everywhere" and becomes a permanent
   wall that no later improvement to the venue can re-open. `research.py stale` finds the
   ones that can.
8. `uv run tools/build.py` must be green before any commit.

---

## The work loop

Each research pass. The long form, with what each step defends against, is
[docs/method/overview.md](docs/method/overview.md).

1. **Pick a frontier** — `research.py frontiers` ranks by `value × P(resolvable) ÷ cost`,
   so it already prefers rare surnames over common ones and a person with a date and a
   commune over one with only a name. Direct ancestors sit a tier above collateral
   relatives, because objective 1 outranks objective 2. `research.py acts` asks the better
   question once the corpus is stocked: not *which frontier*, but *which single act answers
   the most of them at once* — a marriage act names six people.
2. **Check what's been tried** — `research.py tried <person>`, `untried <person>`, `yield`,
   `stale`. Do not re-walk a logged `miss` without a new angle; `blocked` means it was
   never actually read, so it is worth retrying.
   The same holds for **rulings**: `research.py children` reads `research/labels.jsonl` and
   holds back any pair a verifier already refuted, printing each with its reason. If a
   suppressed lead looks wrong, **correct the label**; never work around it.
3. **Harvest, then search.** `uv run tools/harvest.py` first — Open Archives is free,
   unauthenticated, ~30M Belgian person-mentions, and a harvest is *kept*, so it answers
   every future frontier too. `uv run tools/link.py <person>` then joins the held acts to
   the tree and prints candidates. Only when that is exhausted is a logged-in browser
   session worth it — see [docs/searching.md](docs/searching.md).
4. **Verify** — actively try to *refute* the identity match before accepting it. `link.py`
   scores in bits of rare-evidence agreement and marks anything short of two independent
   identifiers NOT GRAFTABLE, but a score is a shortlist, never a verdict.
5. **Record** —
   - the person files;
   - `uv run tools/evaluate.py label …` for **every** ruling, accepted or refuted. Label the
     **mention**, `<act-id>#<pid>`, never the act alone: an act names six people, so an
     act-level ref does not say which one the ruling was about. `evaluate.py refs` lists the
     ones still owed a pid. Kept, these turn the thresholds in `match.py` from reasoned
     guesses into measurements;
   - `uv run tools/research.py log …` for **every** search — a hit must say what it
     `--found`, anything else must say `--why`, and a miss must state its `--scope`;
   - a new site or page in `research/sources.json` if one was discovered, and the `yielded`
     line on any page that produced something;
   - a numbered section in `docs/research-log.md`: what was found, what came back negative,
     what the next frontier is.
6. **Build & commit** — `uv run tools/build.py`, then one commit per pass.

`docs/sources.md` is generated from the registry — edit `research/sources.json`, not the
markdown.

---

## Unattended runs

`/autopilot` and `/verify-sweep` both run passes back to back with nobody watching. What
follows holds for both, so each command file describes only what is *particular* to it —
which direction it works in, which queue it reads, which log it writes.

1. **Do not ask questions.** Where you would ask, choose what the rules above already
   imply, write the choice into the log with its reasoning, and continue.
2. **Work from the tools, never from memory.** Every queue is derived from the records when
   asked, so it cannot go stale and a half-finished run resumes by recomputing. Trust it
   over anything earlier in the conversation.
3. **Do not edit `tools/`, `.claude/` or `CLAUDE.md`.** Those need review and the run will
   stall waiting for it. If a pass seems to need one, that is a finding for the final
   report, not a change to make now.
4. **A pass that concludes nothing is a successful pass.** Most end NOT PROVEN. Never graft
   on one identifier to have something to report, and never upgrade a confidence to `doc`
   without having read the act or its image.
5. **Write, every pass:** the person files; `research.py log` for every search, hit or
   miss, a miss stating its scope; `evaluate.py label` for every ruling, **rejections
   included** and always against `<act-id>#<pid>`; any new source registered; a numbered
   section in `docs/research-log.md`; one row in the run's own log. Then `build.py`, then
   one commit. **Do not push.**
6. **Stop early** if `build.py` fails for a reason its own message does not explain — leave
   the tree as it is and never force it green; if three passes in a row come back entirely
   `blocked`, which means the session or the network is gone rather than the research; or
   if continuing would require breaking a rule above.

---

## Searching at scale

The strategy that got this tree to three hundred people does not reach ten thousand, and
the reason is structural rather than a matter of effort. Eight shifts, each written up
where it was measured:

| The old shape | What replaced it | Explained in |
|---|---|---|
| The unit of work was a **person**; a record is an **event** | acts harvested and kept, read as events, joined against every open frontier at once | [corpus.md](docs/method/corpus.md) |
| **One HTTP request per act** — about a month of fetching for Belgium | `harvest.py bulk` takes a whole archive in one request; `oai` at 150 acts a request | [scaling.md §1](docs/method/scaling.md) |
| **Every command re-derived the corpus** — 9.5s and half a gigabyte per invocation | `familytree/store.py` keeps the blocking keys in SQLite; `link.py` went 12s → 0.3s | [scaling.md §2](docs/method/scaling.md) |
| Work was **O(people × venues)**, and both grow | `research.py frontiers` scores value × P ÷ cost; `research.py acts` solves maximum coverage greedily | [overview.md](docs/method/overview.md) |
| The queue asked **only the upward question**, so no pass ever found a sibling | `research.py children`; and `harvest.py place <commune>`, because a birth act is indexed under the child | [overview.md](docs/method/overview.md) |
| **A name in another language was a different name** — 8% of the corpus | `data/forenames.json` folds them, split by sex so a fold can never cross | [linkage.md](docs/method/linkage.md) |
| **Agreement was unweighted** — Janssens scored like Schalandrijn | `familytree/match.py` scores in bits of surprise, counted from the corpus itself | [linkage.md](docs/method/linkage.md) |
| **Nothing stopped a person being entered twice** | `tools/identify.py` asks before a record is written; the validator runs the same blocking index over the whole tree every build | [data-model.md](docs/data-model.md) |

Three things there are operative rather than explanatory, so they are stated here:

- **Take the archive, not the surname, wherever you can.** `bulk`, then `oai`, then
  `surname`. The acts are byte-for-byte identical and the cost differs by three orders of
  magnitude. The per-act route remains the only way into the Rijksarchief and Familiekunde
  sets, which publish neither an export nor OAI-PMH.
- **Scoring ranks candidates; it never promotes one.** The two-independent-identifiers rule
  is a hard floor no score can buy past, and a stated conflict still vetoes outright.
- **After any large harvest, run `uv run tools/evaluate.py report`.** The rarity weights are
  counted from the corpus, so a much larger corpus is a different measuring instrument and
  every score moves. A change in precision afterwards is the old thresholds having been
  fitted to a smaller sample, not the harvest being wrong. What else a large ingest sets off
  is [docs/method/scaling.md §3a](docs/method/scaling.md).

Open Archives is the venue this rests on. Coverage is uneven and that matters —
Vlaams-Brabant has indexed civil acts, while Oostende and Evergem are overwhelmingly
20th-century memorial cards, which is exactly the layer AGATHA's publicity rules block. It
does not replace the logged-in archives; it goes first, because it is cheap, reproducible
for anyone else, and keeps what it finds.

---

## Data model

`data/people/<id>.md` is the source of truth — one file, one person: a strict frontmatter
block for the facts, and free Markdown prose below it for everything a field cannot hold.
Everything derived (children, generations, kinship, lineages) is computed from
`father`/`mother` links.

- **The field list, with a worked example:** [README.md](README.md).
- **The design, the invariants the validator enforces, the date grammar, artifacts,
  interchange and the known limits:** [docs/data-model.md](docs/data-model.md).
- **Where every file in the repository lives:**
  [docs/data-model.md § Where everything lives](docs/data-model.md).

The rules worth having in front of you while editing records:

1. **Nothing is listed twice.** The roster is the directory; the Index groups from each
   person's own `line`; citations are ids into `research/sources.json`. If you find
   yourself keeping two things in step by hand, that is the bug.
2. **A relationship is never a field.** It is a fact about a *pair*, so it is derived from
   the links. Writing "Ronny's sister" into a record puts a second, un-checkable copy of the
   tree in the prose. The same goes for which children came from which marriage: every child
   already names its own father and mother.
3. **Marriage is mutual, and a shared child proves a couple.** If A lists B, B lists A; a
   record with `father: A`, `mother: B` obliges A and B to list each other. **One marriage,
   one set of facts** — the two records must agree field for field. The validator enforces
   all of it.
4. **Every date answers two questions, and code must be explicit about which.** `point_year`
   is what a date *asserts*; `year_span` is what it *permits*. Evidence reads the first,
   vetoes read the second. But `raw` is not a place to park a date the grammar *can* hold —
   a record whose only date was prose is, to the matcher, entirely undated.
5. **`sex` is recorded from what a source says**, never from a forename — and being a
   `father`/`mother` already settles it.
6. **Ids are stable, and data files are plain text** (`é`, `&`, never HTML entities).
   Renaming an id breaks every reference. The renderer escapes.
7. **Presentation carries no facts:** nothing in `assets/` contains a name or a date.

---

## Commands

```
uv run tools/build.py                      validate, then regenerate bundle.js + the GEDCOM
uv run tools/check_data.py                 validate only (must be green before commit)

uv run tools/research.py frontiers         what to work on next, ranked by value/cost
uv run tools/research.py acts              which held act answers the most frontiers
uv run tools/research.py tried <person>    what was searched, found, and why it failed
uv run tools/research.py untried <person>  sites and pages not yet tried on them
uv run tools/research.py yield             which sites, pages and methods pay off
uv run tools/research.py stale             misses a venue has since outgrown
uv run tools/research.py children          unrecorded children of couples we hold — objective 2
uv run tools/research.py components        disconnected families — objective 3
uv run tools/research.py collapse          where the tree folds back on itself
uv run tools/research.py log …             record a search — hit or miss

uv run tools/harvest.py bulk <archive>     a WHOLE archive in one request — try this first
uv run tools/harvest.py oai <archive>      a whole archive at 150 acts a request
uv run tools/harvest.py frontiers          pull the acts the queue is asking for
uv run tools/harvest.py surname Bundervoet every Belgian record for one surname
uv run tools/harvest.py status             what is held, what is missing, what is bulk-able
uv run tools/harvest.py replay             rebuild the whole corpus from the manifest
uv run tools/link.py <person>              what the held acts say about them
uv run tools/identify.py "<name>" --birth … is this person already in the tree?
uv run tools/verify_all.py --json          the whole tree scored at once — the run's worklist

uv run tools/evaluate.py label <person> <act-id>#<pid> --match|--nonmatch --why "…"
uv run tools/evaluate.py refs              labels that name an act but not which of its people
uv run tools/evaluate.py report            precision, recall, and every disagreement
uv run tools/evaluate.py sweep             what moving the graft thresholds would cost
uv run tools/evaluate.py floor             below which bits no true match has ever been seen

uv run --group dev pytest                  the tests
uv run --group docs mkdocs serve           the method documentation, live
uv run --group docs mkdocs build           …and rendered to dist/docs, which IS committed

open index.html                            the site, straight off disk
```

**After changing anything in `data/`, run `uv run tools/build.py`.** It validates first and
refuses to generate from a broken tree. `check_data.py` fails if the generated files are
stale, so the "green before commit" rule already covers this.

**After changing anything in `docs/`, run `uv run tools/build.py` too** — it renders the
docs as its last step and records what it rendered them from. Both pages link to
`dist/docs/index.html` and Pages serves this repository as it stands, so the rendered docs
are committed like `dist/bundle.js`, and the validator now refuses a `docs/` edit that was
not rebuilt. It cannot regenerate them to compare — mkdocs is an optional group and the
validator must run from a bare clone — so it checks a signature over the inputs instead;
`familytree/docsite.py` says what that does and does not catch. Use
`uv run --group docs mkdocs serve` for live preview, but **not** bare `mkdocs build`: it
renders without recording, and the validator will say so.

---

## Open decisions

Not yet decided — do not implement unilaterally:

- **Storage format.** Moving the person files to strict-fielded frontmatter + free-prose
  body. The build step exists now, so the objection has narrowed to whether the working
  files themselves change shape. *(Interchange is settled: GEDCOM 7 is exported.)*

**Waiting on you, not on a decision:** the browser server in `.mcp.json` needs Chrome
started with remote debugging and logged in to the archives once — see
[docs/searching.md](docs/searching.md). Until then, searches that need a session come back
`blocked`, not `miss`.
