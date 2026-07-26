# Family Tree — project charter

Genealogy of **Renée & Léon Bundervoet** (the two children at the root). Static site,
no runtime dependencies, one generation step (`uv run tools/build.py`). ~300 people
today; the target is thousands.

The tools are Python, managed by [uv](https://docs.astral.sh/uv/) — `uv run` fetches
the interpreter and the (empty) dependency set on first use, so a clone runs with
nothing installed. `pyproject.toml` deliberately declares no dependencies: the
frontmatter parser, the date grammar, the GEDCOM writer and the Open Archives client
are all stdlib, because a dependency is a thing that has to still resolve in ten years
for this tree to be readable.

This file is the standing brief. Read the objectives, then find work:
`uv run tools/research.py frontiers` for the ranked queue, and
[docs/research-log.md](docs/research-log.md) for the narrative of how it got there.

The **method** — why the rules below are what they are, what prior work they come from,
and where the model is known to be weak — is written up as a documentation site in
`docs/` (`uv run --group docs mkdocs serve`). Start at [docs/index.md](docs/index.md);
[docs/prior-work.md](docs/prior-work.md) is the literature this borrows from, and
[docs/method/scaling.md](docs/method/scaling.md) is the ordered plan for getting past a
few thousand people. This file stays the operative brief; the docs explain it.

---

## Objectives

**Primary — these define "done" and rank all work:**

1. **All ancestors of Renée & Léon.** Build the tree *upwards*. Every parent link,
   as far back as records go, on every line.
2. **All blood relatives of Renée & Léon.** Build *downwards* from each ancestral
   couple: their children, their children's children. An ancestor's sibling and that
   sibling's descendants are in scope — they are blood.
3. **Connect all Bundervoets.** Build a *forest* of Bundervoet families and find the
   links between the trees. Disconnected roots are expected and legitimate here.

**Secondary — quality bar applied to every person added:**

- **a.** Gather the full life: birth date & place, death date & place, spouse(s),
  marriage date(s) & place, children, occupation, where they lived, migrations.
- **b.** Every person *referenced anywhere* gets their own record file and a place in
  the tree. No one exists only as a string inside someone else's note.
- **c.** For any two people in the index, the site can state their relation.

Priority when they conflict: 1 > 2 > 3 > a. Depth on the direct lines beats breadth.

**Stretch goal (drives architecture, not current work):** map everyone who ever lived
in Oostende. Assume every design decision will meet 10,000+ people — no hand-maintained
per-person lists, no O(n) manual curation.

---

## Non-negotiable rules

These exist because the failure mode of autonomous genealogy is **silently grafting the
wrong person**. At scale, a bad link is unfindable later. The research log is full of
near-misses: two different Hammes, two Simonne Vandewalles, Van Craenenbroecks in the
wrong province, the Gustaaf/Gustavus confusion.

1. **Never match on name alone.** A graft needs at least two independent identifiers to
   agree — date + place, or parent names, or an occupation + commune. Say which two.
2. **Record the evidence, then the fact.** Every new parent link cites a source in
   `research/sources.json`. A claim with no citation does not go in the tree.
3. **Confidence is honest, not aspirational.** `doc` = a primary act or image was
   actually read. `sup` = one member tree, unverified. `fam` = family testimony.
   `unk` = to research. Downgrading is always allowed; upgrading needs a document.
4. **A strong lead is not a link.** Record it in the person's `note` as a named
   frontier. Do not graft it. (`anna_vc` is the model for how to do this.)
5. **Never invent a field.** If an occupation or a day-level date wasn't in the source,
   it is absent, not guessed. Say "not in the reachable pages" in the log.
6. **Corrections are first-class.** When a past conclusion is wrong, retract it
   explicitly in the log with the reasoning (see §29), fix every record it touched.
7. **Log every search, especially the ones that found nothing.** An unrecorded miss is
   a dead end the next pass will walk again. Every entry states its `basis` — *how* the
   material was consulted — and every miss states its `scope`, what was actually
   covered. "AGATHA is exhausted" was only ever true of AGATHA's name index; a miss
   with no extent reads as "everywhere" and becomes a permanent wall that no later
   improvement to the venue can re-open. `research.py stale` finds the ones that can.
8. `uv run tools/build.py` must be green before any commit.

---

## The work loop

Each research pass:

1. **Pick a frontier** — `uv run tools/research.py frontiers` ranks them by
   `value × P(resolvable) ÷ cost`, so it already prefers what this project learned the
   hard way: rare surnames over common ones, and a person with a date and a commune
   over one with only a name. Direct ancestors are a tier above collateral relatives,
   because objective 1 outranks objective 2. `research.py acts` asks the better
   question when the corpus is stocked — not *which frontier*, but *which single act
   answers the most of them at once*, because a marriage act names six people.
2. **Check what's been tried** — `uv run tools/research.py tried <person>` for the
   history, `untried <person>` for what is left, `yield` for which venues and which
   *methods* pay off, `stale` for misses a venue has since outgrown. Do not re-walk a
   logged `miss` without a new angle; `blocked` means it was never actually read, so it
   is worth retrying.

   The same now holds for **rulings**, not just searches. `research.py children` reads
   `research/labels.jsonl` and holds back any pair a verifier already refuted, printing
   each one with its reason. Before, the refutations were written down and nothing read
   them, so the downward queue re-proposed the same retracted graft every run — the one
   thing an unattended loop cannot afford. If a suppressed lead looks wrong, **correct the
   label**; never work around it.
3. **Harvest, then search.** Reach for `uv run tools/harvest.py` first: Open Archives
   is free, unauthenticated and holds ~30M Belgian person-mentions, and a harvest is
   kept, so it answers every future frontier too. `uv run tools/link.py <person>` then
   joins the held acts to the tree and prints candidates. Only when that is exhausted
   is it worth a logged-in browser session — see [docs/searching.md](docs/searching.md).
4. **Verify** — actively try to *refute* the identity match before accepting it.
   `link.py` scores in bits of rare-evidence agreement and marks anything short of two
   independent identifiers NOT GRAFTABLE, but a score is a shortlist, never a verdict.
5. **Record** —
   - the person files;
   - `uv run tools/evaluate.py label …` for **every** ruling, accepted or refuted. Label
     the **mention**, `<act-id>#<pid>`, never the act alone: an act names six people, so
     an act-level ref does not say which one the ruling was about. 45 of the first 48
     labels were written that way and the scorer was silently handed whichever participant
     came first — usually the groom — so Maria Thérèsia Pardon was scored against her own
     husband and the resulting "recall 33%" measured the ambiguity rather than the scorer.
     `evaluate.py refs` lists the ones still owed a pid. A
     ruling is a labelled pair, and it is the only labelled data this project will ever
     produce. Kept, they turn the thresholds in `match.py` from reasoned guesses into
     measurements — `evaluate.py report` re-scores every past ruling with the current
     code, so a change to scoring can be checked against judgements already made;
   - `uv run tools/research.py log …` for **every** search, hit or miss — a hit must
     say what it `--found`, anything else must say `--why`;
   - a new site or page in `research/sources.json` if one was discovered, and the
     `yielded` line on any page that produced something;
   - a numbered section in `docs/research-log.md` for the narrative: what was found,
     what came back negative, what the next frontier is.
6. **Build & commit** — `uv run tools/build.py`, then one commit per pass.

**Log the misses.** They are the difference between a loop that converges and one that
searches AGATHA for Édouard's parents every night forever. `docs/sources.md` is
generated from the registry — edit `research/sources.json`, not the markdown.

---

## Unattended runs

`/autopilot` and `/verify-sweep` both run passes back to back with nobody watching. What
follows holds for both, so each command file describes only what is *particular* to it —
which direction it works in, which queue it reads, which log it writes.

This section exists because those two files each carried their own paraphrase of all of it.
Only three lines were ever byte-identical, and that is the problem rather than the excuse: a
dozen instructions saying the same thing in different words cannot be diffed, so divergence
is undetectable. Two had already diverged in meaning by the time anyone looked — one file
said to stop when the browser is down while the other said to log `blocked` and continue, and
`.claude/agents/verifier.md` went on teaching the act-level label form for months after §60
corrected it here. Same rule as the data model: nothing is listed twice.

1. **Do not ask questions.** Where you would ask, choose what the rules above already imply,
   write the choice into the log with its reasoning, and continue.
2. **Work from the tools, never from memory.** Every queue is derived from the records when
   asked, so it cannot go stale and a half-finished run resumes by recomputing. Trust it over
   anything earlier in the conversation.
3. **Do not edit `tools/`, `.claude/` or `CLAUDE.md`.** Those need review and the run will
   stall waiting for it. If a pass seems to need one, that is a finding for the final report,
   not a change to make now.
4. **A pass that concludes nothing is a successful pass.** Most end NOT PROVEN. Never graft on
   one identifier to have something to report, and never upgrade a confidence to `doc`
   without having read the act or its image.
5. **Write, every pass:** the person files; `research.py log` for every search, hit or miss,
   a miss stating its scope; `evaluate.py label` for every ruling, **rejections included** and
   always against `<act-id>#<pid>`; any new source registered; a numbered section in
   `docs/research-log.md`; one row in the run's own log. Then `build.py`, then one commit.
   **Do not push.**
6. **Stop early** if `build.py` fails for a reason its own message does not explain — leave the
   tree as it is and never force it green; if three passes in a row come back entirely
   `blocked`, which means the session or the network is gone rather than the research; or if
   continuing would require breaking a rule above.

---

## Searching at scale

The search strategy that got this tree to three hundred people does not reach ten
thousand, and the reason is structural rather than a matter of effort.

**The unit of work was wrong.** A search is person-indexed — one query, one person —
but a record is event-indexed. A marriage act is one document about six people, four
of them parents. Searching per person pays the cost of finding that act once per
person and throws away the other five. So acts are now **harvested and kept**
(`tools/harvest.py`), read as events (`familytree/corpus.py`), and joined against
every open frontier at once. This is family reconstitution, which historical
demography has done since Louis Henry; the modern form is the IISG's LINKS project.

**Fetching was one HTTP request per act.** Which is fine for a surname and hopeless for a
province: at the four requests a second the venue permits, Belgium's ~30 million
person-mentions are about a month of continuous fetching, and 1.2% of them are held. The
same records are published whole — a gzipped A2A export per archive, and an OAI-PMH feed
serving 150 full records a request — so `harvest.py bulk` takes an archive in one request
and `harvest.py oai` in a few hundred. Kortrijk is 140,543 acts in a 19 MB download, where
the per-act route had fetched 1,361 of them. `familytree/a2a.py` reads that XML into
exactly the shape the JSON API returns, which is what makes the routes interchangeable:
all 1,361 Kortrijk acts held both ways normalise to identical records. The per-act endpoint
remains the only route to the Rijksarchief and Familiekunde sets, which publish neither.

**Every command re-derived the whole corpus.** Reading 100,000 acts to answer a question
about one person — 9.5 seconds and half a gigabyte, per invocation, and `link.py` paid it
again for the next person. The blocking keys already say which records could possibly be
compared, so `familytree/store.py` keeps them in a SQLite index and a candidate lookup
becomes a query: `link.py` went from 12 seconds to 0.3. The index holds byte offsets, never
a second copy of the acts, and stores the signature of every harvest file so it rebuilds
rather than silently lagging — an index answering "no candidates" for an act fetched an
hour ago is the corpus form of reporting `blocked` as `miss`. The in-memory scan stays for
the reports that genuinely touch every act: `verify_all.py` is *slower* through the index
(40s against 27s) because a whole-tree sweep needs nearly all of them, and that was
measured rather than assumed.

**The work was O(people × venues), and both grow.** 147 open frontiers against 17
registered venues is 2,500 cells, and every person added opens up to two more. A queue
that ranks only by generation cannot converge — it has no way to prefer the frontier
that will actually move. `research.py frontiers` now scores `value × P ÷ cost`, and
`research.py acts` asks the better question: which single act answers the most open
frontiers, which is maximum coverage and is solved greedily.

**The queue only asks one of the two questions.** A frontier is someone whose parents are
unknown, so every pass driven by it grows the tree *upwards* and no pass ever finds a
sibling — 127 couples here have exactly one recorded child, and not one of them is a
frontier. Objective 2 needs the downward question: `research.py children`, which children
the held acts name for couples already recorded. It changes what to harvest, too. A
surname harvest finds ancestors, because marriage and death acts are indexed under the
person; a *birth* act is indexed under the child, so a sibling is reachable only through
the commune or the parents. `harvest.py place <commune>` is the harvest objective 2
needs, and the one that points at a whole parish.

**A name in another language was a different name.** Flanders wrote its registers in Latin,
then French, then Dutch, so one man is Joannes at his baptism, Jean at his marriage and Jan at
his death — 353,553 mentions, 8% of the corpus, that the scorer read as three unrelated names.
`data/forenames.json` folds them, and it is **data because it is names**, split by sex so a
fold can never cross from Ludovicus to Ludovica. It is curated and not learned: the
masculine/feminine pairs that must never fold are *more* similar than the Latin/vernacular
pairs that should, so any similarity threshold merges a brother with his sister first. The
split does not license reading sex off a forename — that stays forbidden.

**Agreement was unweighted.** "Never match on name alone" is right, but it treats
Janssens and Schalandrijn as the same evidence. `familytree/match.py` scores each
agreement in **bits of surprise** — `log2(1/frequency)`, counted from the harvested
corpus itself, which is where the u-probabilities of probabilistic record linkage come
from. The two-independent-identifiers rule stays as a hard floor that no score can buy
past, and a stated conflict still vetoes outright. Scoring ranks candidates; it never
promotes one.

**Nothing stopped the same person being entered twice.** Bostyn/Bostin,
De Keyser/Dekeyser and Vanstechele/Vanstechelman are all already in this tree. A
duplicate does not look broken — it looks like two people, and it splits a branch.
`tools/identify.py` asks before a record is written, and the validator runs the same
blocking index over the whole tree on every build.

Open Archives is the venue this rests on: free, unauthenticated, ~30M Belgian
person-mentions, with structured roles so a parent link is a field rather than prose.
Coverage is uneven and that matters — Vlaams-Brabant has indexed civil acts, while
Oostende and Evergem are overwhelmingly 20th-century memorial cards, which is exactly
the layer AGATHA's publicity rules block. It does not replace the logged-in archives;
it goes first, because it is cheap, reproducible for anyone else, and keeps what it
finds.

---

## Data model

`data/people/<id>.md` is the source of truth — one file, one person: a strict
frontmatter block for the facts, and free Markdown prose below it for everything a
field cannot hold. Everything derived (children, generations, kinship, lineages) is
computed from `father`/`mother` links. See [README.md](README.md) for the field list.

Dates use a small fixed grammar so they are queryable and sortable, never prose:
`1876-11-12` · `1876-11` · `1876` · `~1682` about · `<1727` before · `>1900` after ·
`1575..1587` between. There is deliberately no syntax for "probably March" — a format
for a guess is an invitation to record one. If a source says something the grammar
cannot express, put it in `raw` and explain it in the prose.

**Every date answers two different questions, and code must be explicit about which.**
`point_year` is what a date *asserts*; `year_span` is what it *permits*. Evidence reads the
first — `~1682` still earns its bits against an act saying 1682. Vetoes read the second, and
only fire when no year satisfies both: a bound or a range asserts nothing, so `1920..1929`
cannot disagree with 1925. Reading `year_of` for both flattened every form to one number and
turned "the decade is all we know" into a conflict with every year in it. Bounds are read
inclusively at year granularity, because `<1946` is the only way the grammar can carry "died
before 9 May 1946" and it must not assert more than the source did.

But `raw` is not a place to park a date the grammar *can* hold. A record whose only date was
prose was, to the matcher, entirely undated — which is how a boy born 1901 was offered as a
man whose birth was declared in 1847, with no veto able to fire. If the source gives a
declaration date, the year is a fact: record `1847` and keep the day in `raw`.

Invariants:

- `father`/`mother` are ids of other person files — the vertical link.
- `spouses` is a list, oldest first; an entry's `id` links to that spouse's record —
  the horizontal link. **Marriage is mutual** (if A lists B, B lists A) and **a shared
  child proves a couple** (a record with `father: A`, `mother: B` obliges A and B to
  list each other). The validator enforces both; they are what let the tree be built
  downwards without losing branches.
- A marriage is an **event**, stored like one: `married` and `divorced` are dates in the
  grammar above, `place` is where the act was passed, and `kind: partnership` marks a
  couple who had children without a recorded marriage — so the page never prints "wife"
  over someone no source called one. `detail` is what none of those can hold, and nothing
  else: it may not carry a date, a place, or a position in a sequence. **One marriage,
  one set of facts** — the two records must agree field for field, because before that
  was checked they gave different places for the same wedding and the first one read won.
- **Which children came from which marriage is derived, never written.** Every child
  already names its own father and mother, so "1st — mother of Segerius" in a marriage
  field was a second copy of a link nothing kept in step. The validator rejects a
  marriage that names its own child; the tree draws one row of children per marriage,
  captioned with the other parent, which is what makes a half-sibling visible at the
  parent instead of only after clicking into a child.
- `occupation` and `nickname` hold only those things. A relationship is never a field:
  it is a fact about a *pair*, so it is derived from the links. Writing "Ronny's sister"
  into a record puts a second, un-checkable copy of the tree in the prose.
- `sex` is `"f"`/`"m"`, optional, and only needed for people who are nobody's parent
  (being a `father`/`mother` already settles it). Record it from what the source says —
  a note calling someone "Roland's sister", a role of "wife" — never from a forename.
- **Nothing is listed twice.** The roster is the directory; the Index groups from each
  person's own `line`; citations are ids into `research/sources.json`. If you find
  yourself keeping two things in step by hand, that is the bug.
- The prose body is for reasoning, evidence and frontiers — the things that do not fit
  a field. It is never a second copy of a field.
- Ids are stable. Renaming one breaks every reference — don't.
- Plain text in data files (`é`, `&`), never HTML entities. The renderer escapes.
- Presentation carries no facts: nothing in `assets/` contains a name or a date.

**Artifacts are data, not documentation.** A scan or photograph of an act is the
evidence itself, so it lives in `data/artifacts/`: the file, plus a record of the same
name in the same frontmatter format, with the transcription in its prose body. The
record carries `sha256` and `bytes`, and the validator recomputes them — a citation
whose evidence has silently changed underneath it is worse than one with no evidence,
because it still reads as sourced. Say in the record whether the act *image* was read
or only an index page; they are different evidence and only one is `doc`.

Kinship is root-free: `relationBetween(a, b)` in `assets/js/kinship.js` works from the
pair's lowest common ancestor, so it relates anyone to anyone (objective c). It names
the relation out of a *vocabulary* held in `site/labels.json`, not out of words in the
code — which is what lets the page say "3×-overgrootmoeder" as readily as
"3×-great-grandmother", and what makes a third language an edit to one data file.
`meta.roots` takes a list for the forest case (objective 3); with one root it is the
ordinary tree.

**The Index groups four ways and sorts three, and every one of them is derived** — by
family line (the person's own `line`), by first letter (the folded family key), by
century (the birth date), or by ancestor/blood/other (the links). So a person added to
`data/` files themselves correctly under all four at once, and there is no list that
regrouping would have to rewrite. That is the rule from the data model — nothing is
listed twice — paying off: a hand-kept index can be regrouped only by rewriting it.

The page loads `dist/bundle.js` — one request for the whole tree, whatever it grows to.
The files in `data/` and `site/` stay the source of truth; the bundle is generated, and
the validator fails if it is stale, so old data cannot reach the site.

**After any large harvest**, run `uv run tools/evaluate.py report`. The rarity weights are
counted from the corpus, so a much larger corpus is a different measuring instrument and
every score moves — a change in precision afterwards is the old thresholds having been
fitted to a smaller sample, not the harvest being wrong. The ordered list of what else a
large ingest sets off is [docs/method/scaling.md §3a](docs/method/scaling.md); the short
version is that the scanning reports (`acts`, `children`, `verify_all`) scale with the
corpus while the targeted lookups stay flat, and when those become the bottleneck it is the
signal that the two-tier storage split is no longer optional.

**Known limits of the current model** — the next structural work:

1. **The bundle is loaded eagerly and committed whole.** ~580 bytes per person, so
   ~6 MB and a full rewrite per commit at 10,000 people. Past a few thousand it wants
   splitting (by branch or generation) and loading on demand, and the build moving to
   CI so the artefact leaves git. The relation finder's two `<select>`s go the same way.
2. **Sex is unknown for anyone childless** unless their record states it. Relations then
   read "sibling" rather than "sister". Fill `sex` in only from what a record says — a
   role of "wife", a note calling someone "Roland's sister" — never from a forename.
   *(Nobody is currently unknown: every person who is nobody's parent states it.)*
3. **A marriage that ended in death has no end date**, because it is derivable from the
   two death dates and inventing a field for it would invite recording a guess. Only
   `divorced` is stored. If that derivation is ever wanted on the page, derive it.
4. **Step-relations are unnamed on purpose.** `relationBetween` goes blood first, then
   exactly one marriage step, then stops — so a stepmother reads as "X married Y, who is
   Z's father" rather than "stepmother", and a step-sibling reads as no connection.
   Beyond one step the wording stops meaning anything reliable, and a wrong in-law label
   is the same class of error as a wrong graft: unfalsifiable prose that reads as fact.

---

## Layout

Three things, kept apart because they change for different reasons and different
rules apply to each. `data/` is the only place a name or a date may appear;
`site/` is wording the page shows and cannot change what the tree claims;
`assets/` contains neither.

```
data/people/<id>.md     source of truth: strict frontmatter + prose body
data/artifacts/<id>.*   a saved primary document + a record describing it
data/meta.json          roots, confidence codes
data/branches.json      surname branch -> its default source id
data/lineages.json      the surname chains
data/forenames.json     forenames that are one name in another language, split by sex
site/labels.json        presentation only, in every language: UI strings, Index
                        headings, footer, and the relation vocabulary. No word the
                        page shows is written anywhere else — see assets/js/i18n.js
research/sources.json   the registry — SITES (venues) and PAGES (trees, documents)
research/searches.jsonl the search log, append-only: what each search found, or why not
research/labels.jsonl   the gold standard: every verifier ruling, as a labelled pair
research/harvest/       the corpus — acts pulled from Open Archives. GITIGNORED
research/harvest/corpus.db      the derived index over those acts. GITIGNORED, rebuildable
research/harvest/manifest.json  which queries were run — committed, so the corpus is reproducible
docs/research-log.md    numbered passes: found / checked-and-negative / next
docs/searching.md       the search strategy: harvest first, browser second
docs/sources.md         readable source list — GENERATED from research/sources.json
pyproject.toml          the uv project. No dependencies, on purpose
tools/familytree/       the library every tool shares
  people.py             the loader, the date grammar, the browser record, the census
  frontmatter.py        the parser for the records' strict YAML subset
  sources.py            the registry and the search log, and what makes an entry valid
  labels.py             the gold standard, readable by the QUEUES and not only the scorer
  landing.py            what index.html says about the size of the tree, so it cannot rot
  bundle.py             data/ + site/ -> dist/bundle.js
  gedcom.py             the GEDCOM 7 writer and its round-trip self-check
  corpus.py             harvested acts, read as EVENTS: roles, parent edges, frequencies
  a2a.py                the same acts as XML — what makes a whole archive one request
  store.py              the corpus as a SQLite index: blocking keys, offsets, frequencies
  match.py              blocking keys, Flemish phonetics, rarity-weighted scoring
  frontier.py           the ranked queue: value x P(resolvable) / cost
  coverage.py           which act answers most frontiers; components; pedigree collapse
tools/build.py          validates, then writes everything generated
tools/verify_all.py     the whole tree scored against the whole corpus, in one pass
tools/check_data.py     the validator
tools/research.py       the log, the registry, and every derived report
tools/harvest.py        pull acts from Open Archives and keep them
tools/link.py           join the held acts to a frontier — candidates, never conclusions
tools/identify.py       is this person already in the tree? ask before writing a record
tools/evaluate.py       the gold standard: label a ruling, then measure the scorer on it
docs/                   the method, written up — mkdocs.yml renders it to dist/docs/
tools/export_gedcom.py  writes exports/family-tree.ged
dist/bundle.js          GENERATED — what the page loads
exports/family-tree.ged GENERATED — GEDCOM 7
assets/                 presentation only — no names, no dates
archive/                superseded drafts, not part of the site
```

Nothing in `data/` is executable. It is JSON and Markdown, readable by any tool
without a JavaScript engine — `jq '.branches' data/branches.json` works, and so does
grep over the person records.

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
uv run tools/evaluate.py refs               labels that name an act but not which of its people
uv run tools/evaluate.py report            precision, recall, and every disagreement
uv run tools/evaluate.py sweep             what moving the graft thresholds would cost
uv run tools/evaluate.py floor             below which bits no true match has ever been seen

uv run --group dev pytest                  the tests
uv run --group docs mkdocs serve           the method documentation, live
uv run --group docs mkdocs build           …and rendered to dist/docs, which IS committed

open index.html                            the site, straight off disk
```

**After changing anything in `data/`, run `uv run tools/build.py`.** It validates first
and refuses to generate from a broken tree. `check_data.py` fails if the generated
files are stale, so the "green before commit" rule already covers this.

**After changing anything in `docs/`, run `uv run --group docs mkdocs build`.** Both
pages link to `dist/docs/index.html`, and Pages serves this repository as it stands, so
the rendered docs are committed like `dist/bundle.js`. Unlike the bundle, nothing checks
them: the validator has no dependencies and mkdocs is an optional group, so a docs edit
committed without a rebuild ships silently stale. That hole closes when the docs build
moves to CI.

`exports/family-tree.ged` is the tree in **GEDCOM 7**, the open format every genealogy
program reads — import it into Gramps, Geneanet, Ancestry or MyHeritage, and it is the
form to hand to anything that wants the data without parsing `.js`. It is generated, so
edits belong in `data/people/` and the file is regenerated.

The exporter refuses to write if the file does not read back as the same tree: it
reparses its own output, rebuilds the parent and marriage links from that alone, and
compares them to the source records. It also reports what GEDCOM could not carry —
dates too vague to express, `role` values that are relationships rather than
occupations — rather than flattening them into fields that would then read as fact.

---

## Open decisions

Not yet decided — do not implement unilaterally:

- **Storage format.** Moving the person files to strict-fielded frontmatter + free-prose
  body. The build step exists now, so the objection has narrowed to whether the working
  files themselves change shape. *(Interchange is settled: GEDCOM 7 is exported.)*
**Waiting on you, not on a decision:** the browser server in `.mcp.json` needs Chrome
started with remote debugging and logged in to the archives once — see
[docs/searching.md](docs/searching.md). Until then, searches that need a session come
back `blocked`, not `miss`.
