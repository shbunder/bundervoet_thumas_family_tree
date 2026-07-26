---
description: Run one full research pass — choose a frontier, search, verify, record, build, commit.
argument-hint: "[optional: person id or line to work on]"
---

Run one complete research pass on the family tree. Target: $1 (if empty, let the strategist
choose).

The four roles exist so that no single agent both finds a match and decides it is true. Keep
them separate; that separation is the main defence against grafting the wrong person, which
is the failure mode this whole project is built around.

1. **Strategist** — launch the `strategist` subagent. It returns one frontier, the sites and
   pages to try in order, and what would count as proof. If a target was given above, tell it
   to work on that one and explain the best route.

2. **Searcher** — launch the `searcher` subagent with that plan. It works the routes in the
   order [CLAUDE.md](../../CLAUDE.md) § Searching at scale sets out and logs every search,
   hit or miss. It returns candidates, never conclusions.

3. **Verifier** — launch the `verifier` subagent on each candidate. It tries to refute. Do
   not skip this even when a match looks obvious — especially then. Its verdicts are ACCEPT,
   REJECT or NOT PROVEN, and NOT PROVEN is the common one. It records each ruling with
   `uv run tools/evaluate.py label …`, rejections included.

4. **Recorder** — launch the `recorder` subagent with the accepted findings and the stated
   confidence. It writes the person files, registers sources, adds the narrative section to
   `docs/research-log.md`, runs `uv run tools/build.py` and commits.

Not every pass should go upwards. The frontier queue only knows how to ask "who were this
person's parents", so a run of passes against it deepens the direct lines and never widens
them. `uv run tools/research.py children` asks the other question, and that is objective 2.
Alternate deliberately, rather than letting the queue's one shape decide the project's shape.

If the browser is not running, that thins the pass; it does not end it. Say so, log every
search that needed a session as `blocked` rather than `miss`, and work the two routes that
need no session at all.

If a pass ends with nothing grafted, that is a normal outcome. A logged set of negatives is
worth more than a speculative link, and saying "this needs the Stadsarchief" is a real result.

Then report back to me, briefly:

- what was found, and what it is grafted on — which two identifiers agreed;
- what was searched and came back empty, and whether it is worth retrying;
- anything the verifier rejected, and why;
- the next frontier.
