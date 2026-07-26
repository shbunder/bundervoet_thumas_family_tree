---
description: Run research passes back-to-back, unattended, logging each one. Stops on a broken build.
argument-hint: "[number of passes, default 10]"
---

Run $1 research passes (default 10) one after another, without checking in between.

**The rules for an unattended run are in [CLAUDE.md](../../CLAUDE.md) § Unattended runs** —
don't ask questions, don't edit `tools/`/`.claude/`/`CLAUDE.md`, what to write every pass,
when to stop early, and why a pass that concludes nothing is still a good one. They are not
repeated here. This file is only what is particular to *growing* the tree: the rotation, the
three routes, and this run's own log.

## Before the first pass

1. `uv run tools/check_data.py` — if it is not green, stop and say why. Never begin from a
   broken tree.
2. `uv run tools/harvest.py status` — it now ends with the archives you already hold acts
   from that publish a **whole-archive export**. Take those first: one request each, and
   it supersedes every future surname query in that archive. Kortrijk is 140,543 acts in a
   19 MB download against thirteen hours of per-act fetching, so this is not a marginal
   saving and it is the difference between a surname and a province.

   Then finish every harvest still marked PARTIAL, largest `found` first, with the command
   the status output prints. A partial harvest is the reason a frontier looks unsearchable
   when it simply has not been fetched, and `link.py` will say so per surname.
3. `uv run tools/verify_all.py --json > .autopilot-worklist.json` — the whole tree scored
   against the whole corpus, **once**. Every pass reads its row out of this instead of
   asking the same question again; a run of ten passes used to pay for it ten times. Delete
   the file at the end of the run — it is a scratch file, not a record, and a stale copy
   is worse than none.
4. `uv run tools/research.py frontiers`, `uv run tools/research.py children` and
   `uv run tools/research.py acts` — read all three before starting, so the rotation below
   has somewhere to go.

## Each pass

Run the `/research-pass` loop: **strategist → searcher → verifier → recorder**, kept
separate. That separation is the whole defence against grafting the wrong person, and it
is worth nothing if one agent both finds a match and decides it is true.

### Rotate the direction, three ways

- **Pass 1 of 3 goes up.** `research.py frontiers` — "who were this person's parents".
- **Pass 2 of 3 goes down.** `research.py children` — children the held acts name for
  couples already in the tree.
- **Pass 3 of 3 goes by ACT.** `research.py acts` — the held act that answers the most open
  frontiers at once, taken from the top of the greedy cover.

Left to itself the queue only asks the upward question, so the direct lines get deeper and
no sibling is ever found. Objective 2 does not happen by accident. If the downward pass
has nothing because the corpus holds too few birth acts, spend that pass on
`harvest.py place <commune>` instead — a birth act is indexed under the child, so a
sibling is only reachable through the commune or the parents.

The third pass is the one that matches the unit of work to the unit of evidence. A frontier
is one person; a marriage act is one document about six, four of them parents. Working an
act resolves whatever it resolves — which is why `research.py acts` orders them by what
each one *adds* rather than by what it repeats. A pass spent on the top act is worth
several spent on the frontiers underneath it, and it is the same reading either way.

### Three routes, cheapest first

1. **Harvest.** Open Archives needs no login, and what it pulls is kept, so it answers this
   frontier and every later one on that surname. Reach for `harvest.py bulk <archive>`
   before `harvest.py surname <name>`: where an archive publishes an export, the whole
   archive costs one request, and the acts it yields are identical to the ones the per-act
   endpoint returns. `harvest.py oai <archive>` is the same idea at 150 acts a request,
   for archives with no export. The per-act route is a last resort — it is where the
   Rijksarchief and Familiekunde sets still have to be read, because they publish neither.
2. **The open web.** `WebSearch` and `WebFetch` reach public archive indexes, WikiTree,
   Find A Grave, digitised newspapers, local-history transcriptions, and venues the
   registry has never heard of. Register a new one in `research/sources.json` when it pays
   off. Everything found this way is reproducible for the next reader.
3. **The logged-in browser.** Last. If Chrome is not running, log those searches as
   `blocked` and continue to the next pass — a missing session makes a pass thinner, it
   does not end the run.

A search-result summary is not the record: fetch the page and read it before treating
anything as found.

## This run's own log

Everything else that gets written is in CLAUDE.md § Unattended runs. The one thing specific
to this command is its row:

- One row appended to `docs/autopilot-log.md`. Create it if absent, with this header:

  ```
  | pass | date | dir | frontier | verdict | added | commit |
  |------|------|-----|----------|---------|-------|--------|
  ```

  `dir` is up/down/act. `verdict` is GRAFTED / NOT PROVEN / REJECTED / BLOCKED. `added` is
  the person ids created, or `—`. This file is an index into the research log and the git
  history, not a second copy of either — keep each row to one line.

## At the end

Append a summary block to `docs/autopilot-log.md` and print the same thing here:

- people before → after, and how many acts the corpus gained;
- every graft, with the **two independent identifiers** that carried it;
- what was refuted, and what refuted it;
- which venues came back blocked and therefore need a logged-in browser;
- `uv run tools/evaluate.py report` — what the new labels say about the scorer;
- the single most valuable thing to do next, and whether it needs me.

Short enough to read in a minute. I will read `docs/autopilot-log.md`, not the transcript.
