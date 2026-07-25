---
description: Run research passes back-to-back, unattended, logging each one. Stops on a broken build.
argument-hint: "[number of passes, default 10]"
---

Run $1 research passes (default 10) one after another, without checking in between.

I am not watching. **Do not ask me questions.** Where you would normally ask, choose what
the rules in [CLAUDE.md](../../CLAUDE.md) already imply, record the choice in the log, and
keep going. Work from the tools, never from memory or from anything earlier in this
conversation — every queue here is derived fresh when asked, so it cannot go stale, and a
half-finished run resumes by recomputing.

Do not edit anything under `tools/`, `.claude/` or `CLAUDE.md`. Those need my approval and
the run will stall waiting for it. Nothing in a research pass requires them: if a pass
seems to, that is a finding to report at the end, not a change to make now.

## Before the first pass

1. `uv run tools/check_data.py` — if it is not green, stop and say why. Never begin from a
   broken tree.
2. `uv run tools/harvest.py status` — finish every harvest still marked PARTIAL, largest
   `found` first, with the command the status output prints. A partial harvest is the
   reason a frontier looks unsearchable when it simply has not been fetched, and
   `link.py` will say so per surname.
3. `uv run tools/research.py frontiers` and `uv run tools/research.py children` — read
   both before starting, so the alternation below has somewhere to go.

## Each pass

Run the `/research-pass` loop: **strategist → searcher → verifier → recorder**, kept
separate. That separation is the whole defence against grafting the wrong person, and it
is worth nothing if one agent both finds a match and decides it is true.

### Alternate the direction

- **Odd passes go up.** `research.py frontiers` — "who were this person's parents".
- **Even passes go down.** `research.py children` — children the held acts name for
  couples already in the tree.

Left to itself the queue only asks the upward question, so the direct lines get deeper and
no sibling is ever found. Objective 2 does not happen by accident. If the downward pass
has nothing because the corpus holds too few birth acts, spend that pass on
`harvest.py place <commune>` instead — a birth act is indexed under the child, so a
sibling is only reachable through the commune or the parents.

### Three routes, cheapest first

1. **Harvest.** Open Archives needs no login, and what it pulls is kept, so it answers this
   frontier and every later one on that surname.
2. **The open web.** `WebSearch` and `WebFetch` reach public archive indexes, WikiTree,
   Find A Grave, digitised newspapers, local-history transcriptions, and venues the
   registry has never heard of. Register a new one in `research/sources.json` when it pays
   off. Everything found this way is reproducible for the next reader.
3. **The logged-in browser.** Last. If Chrome is not running, log those searches as
   `blocked` and continue to the next pass — a missing session makes a pass thinner, it
   does not end the run.

A search-result summary is not the record: fetch the page and read it before treating
anything as found.

### Do not lower the bar to make a pass productive

A pass that grafts nothing and logs five honest misses is a successful pass. Most passes
end NOT PROVEN, and that is the system working rather than stalling. Never graft on one
identifier to have something to report, and never upgrade a confidence to `doc` without
having actually read the act or its image.

## What to write, every pass

- The person files — citation by id, honest confidence, no invented field.
- `uv run tools/research.py log …` for every search, hit or miss. A miss states its scope.
- `uv run tools/evaluate.py label …` for every verifier ruling, **rejections included**.
  A REJECT is the more valuable label: it is a pair that scored well enough to reach a
  verifier and was still wrong, which is exactly what the scorer needs.
- A numbered section in `docs/research-log.md` — the narrative.
- One row appended to `docs/autopilot-log.md`. Create it if absent, with this header:

  ```
  | pass | date | dir | frontier | verdict | added | commit |
  |------|------|-----|----------|---------|-------|--------|
  ```

  `dir` is up/down. `verdict` is GRAFTED / NOT PROVEN / REJECTED / BLOCKED. `added` is the
  person ids created, or `—`. This file is an index into the research log and the git
  history, not a second copy of either — keep each row to one line.
- `uv run tools/build.py`, then one commit per pass. **Do not push.**

## Stop early if

- `build.py` fails and the cause is not obvious from the validator's own message. Leave
  the tree as it is, never force it green, and say what broke.
- Three passes in a row come back entirely `blocked`. That means the session or the
  network is gone, not that the research is exhausted.
- Continuing would require breaking a rule in CLAUDE.md.

Otherwise keep going to the end of the run.

## At the end

Append a summary block to `docs/autopilot-log.md` and print the same thing here:

- people before → after, and how many acts the corpus gained;
- every graft, with the **two independent identifiers** that carried it;
- what was refuted, and what refuted it;
- which venues came back blocked and therefore need a logged-in browser;
- `uv run tools/evaluate.py report` — what the new labels say about the scorer;
- the single most valuable thing to do next, and whether it needs me.

Short enough to read in a minute. I will read `docs/autopilot-log.md`, not the transcript.
