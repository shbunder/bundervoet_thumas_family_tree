# The research loop

One pass, repeated. Each step exists because skipping it produced a specific error that
is recorded in the [research log](../research-log.md).

```
  frontier  ──▶  what's been tried  ──▶  harvest  ──▶  link  ──▶  verify  ──▶  record
     ▲                                                                            │
     └────────────────────────────────────────────────────────────────────────────┘
```

## 1. Pick a frontier

```bash
uv run tools/research.py frontiers
```

A *frontier* is an unresolved question — most often "who were this person's parents".
The queue ranks them by `value × P(resolvable) ÷ cost`, which encodes what this project
learned the hard way:

- **Rare surnames over common ones.** A rare surname makes agreement informative; a
  common one makes it worthless. This is measured, not guessed — see
  [Record linkage](linkage.md).
- **A person with a date and a commune over one with only a name.** The second
  identifier has to come from somewhere.
- **Direct ancestors above collateral relatives**, because objective 1 outranks
  objective 2.

There is a better question the queue can ask once the corpus is stocked:

```bash
uv run tools/research.py acts
```

Not *which frontier*, but **which single act answers the most frontiers at once** — a
maximum-coverage problem, solved greedily. A marriage act names six people and four of
them are parents.

!!! warning "The queue only asks the upward question"
    A frontier is someone whose parents are unknown. So a run of passes driven by the
    queue will deepen the direct lines and **never find a sibling** — a couple with one
    recorded child and eight unrecorded ones produces no frontier at all, because nothing
    is missing from any record that exists.

    Objective 2 needs the downward question:

    ```bash
    uv run tools/research.py children
    ```

    ...which children the held acts name for couples already in the tree. It identifies
    both parents through the ordinary scoring rules, requires them to be recorded as a
    couple, and separates *add this person* from *link the person already held* — because
    offering the second as the first is how a tree acquires two copies of someone.

    This also changes what to harvest. A surname harvest finds ancestors, because
    marriage and death acts are indexed under the person. A **birth** act is indexed
    under the child, so a sibling is reachable only through the commune or the parents —
    which makes `harvest.py place <commune>` the harvest objective 2 needs, and the one
    that points at a whole parish rather than one family.

## 2. Check what has been tried

```bash
uv run tools/research.py tried <person>     # history: what was searched, and how it went
uv run tools/research.py untried <person>   # venues not yet attempted on them
uv run tools/research.py yield              # which sites, pages and methods actually pay
uv run tools/research.py stale              # misses a venue has since outgrown
```

A logged `miss` is not re-walked without a new angle. A logged `blocked` means nothing
was ever read, so it is always worth retrying. That distinction is load-bearing: it is
the difference between "this venue does not have him" and "I could not log in".

Every miss records its **scope** — what was actually covered. "AGATHA is exhausted" was
only ever true of AGATHA's *name index*. A miss with no extent reads as *everywhere* and
becomes a permanent wall that no later improvement to the venue can reopen. Since venues
are now retro-fitting AI full-text search over previously unindexed images, this is not
hypothetical.

## 3. Harvest, then search

```bash
uv run tools/harvest.py frontiers    # pull the acts the queue is asking for
uv run tools/link.py <person>        # what the held acts say about them
```

Harvesting comes first because it is free, unauthenticated, reproducible by anyone else,
and — critically — **kept**. A logged-in browser session is the fallback, not the
default. See [The corpus](corpus.md) for why the unit of work changed from *person* to
*act*.

## 4. Verify

Actively try to **refute** the identity match before accepting it. `link.py` produces a
ranked shortlist and marks anything below two independent identifiers `NOT GRAFTABLE`,
but a score is a shortlist and never a verdict.

The verification agent defaults to rejecting when uncertain. This asymmetry is
deliberate and is the core of the method: **a missed link is found again next pass; a
false link is invisible forever.** See [Verification](verification.md).

## 5. Record

- The person files — one file per person, no exceptions.
- Every search, hit or miss:
  `uv run tools/research.py log …` (a hit says what it `--found`, anything else says `--why`).
- Every verifier ruling as a labelled pair:
  `uv run tools/evaluate.py label …` — this is what makes the thresholds measurable.
- Any new venue or page in `research/sources.json`.
- A numbered section in [the research log](../research-log.md): what was found, what came
  back negative, what the next frontier is.

## 6. Build and commit

```bash
uv run tools/build.py     # validates first, then regenerates everything derived
```

The validator must be green before any commit, and it refuses to generate from a broken
tree. It also fails if the generated artefacts are stale, so old data cannot reach the
site.

---

## The agents

The loop is run by four specialised agents, kept separate because they have different
failure modes and must not be allowed to cover for each other:

| Agent | Job | Constraint |
|---|---|---|
| **strategist** | Choose the frontier and name the venues to try | Read-only — never edits the tree |
| **searcher** | Run the searches, log every one | Returns *candidates*, never facts |
| **verifier** | Try to refute each candidate | Adversarial; rejects when unsure; never edits |
| **recorder** | Write accepted findings into the tree | Mechanical; makes no decisions of its own |

The separation is the point. An agent that both finds and accepts evidence will accept
what it found.
